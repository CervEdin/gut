#!/bin/bash

OPTIONS_SPEC="\
git stash-inspector [options] [<branch-name>]

List and show stashes related to a specific branch (default to the current branch if no branch is specified).
--
h,help           Show the help
"

# Parse options using git rev-parse --parseopt
eval "$(echo "$OPTIONS_SPEC" | git rev-parse --parseopt -- "$@" || echo exit 1)"

VERBOSE=false

while :; do
  case "$1" in
    --)
      shift
      break
      ;;
    *)
      echo "Unexpected option: $1"
      exit 1
      ;;
  esac
done

# Get the branch name from the first argument, if provided
branch_name="$1"

# If no branch name is provided, use the current branch name
if [ -z "$branch_name" ]; then
  branch_name=$(git rev-parse --abbrev-ref HEAD)
fi

# Get the list of stash entries that match the given pattern
stashes=$(git stash list --grep "WIP on $branch_name")

# Check if the stashes variable is empty
if [ -z "$stashes" ]; then
  echo "No stash entries found for branch '$branch_name'."
  exit 0
fi

# Iterate over each stash entry
while IFS= read -r line; do
  # Extract stash identifier
  stash=$(echo "$line" | grep -o 'stash@{[0-9]\+}')

  # Extract branch name, commit hash, and title
  if [[ $line =~ WIP\ on\ ([^:]+):\ ([a-f0-9]+)\ (.+) ]]; then
    extracted_branch_name="${BASH_REMATCH[1]}"
    commit_hash="${BASH_REMATCH[2]}"
    title="${BASH_REMATCH[3]}"
  else
    echo "Failed to parse line: $line"
    continue
  fi

  # Print extracted information
  echo "Stash: $stash"
  echo "Branch: $extracted_branch_name"
  echo "Commit Hash: $commit_hash"
  echo "Title: $title"
  echo

  # Show the stash patch
  git stash show --stat "$stash"
  printf "\n\n"
done <<< "$stashes"
