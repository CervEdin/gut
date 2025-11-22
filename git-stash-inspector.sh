#!/bin/bash

# Check if the user provided a branch name
if [ -z "$1" ]; then
  exec "$0" --help
  exit 1
fi

# Get the branch name from the first argument
branch_name="$1"

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
