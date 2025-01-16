#!/bin/sh

OPTIONS_SPEC="\
git pull-other [options] <local-ref>

Fetch and update the local reference from the default remote.
--
h,help           Show help message
v,verbose        Enable verbose output
q,quiet          Suppress output
"

# Parse options using git rev-parse --parseopt
eval "$(echo "$OPTIONS_SPEC" | git rev-parse --parseopt -- "$@" || echo exit $?)"

VERBOSE=false
QUIET=false

while :; do
  case "$1" in
    --verbose)
      VERBOSE=true
      shift
      ;;
    --quiet)
      QUIET=true
      shift
      ;;
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

# Check if a local-ref is provided
if [ $# -lt 1 ]; then
  echo "Error: Missing <local-ref>"
  exec "$0" --help
  exit 1
fi

LOCAL_REF="$1"
shift

# Validate the local reference
if ! git rev-parse --verify "$LOCAL_REF" >/dev/null 2>&1; then
  echo "Error: Local reference '$LOCAL_REF' does not exist or is invalid."
  exit 1
fi

# Determine the default remote using config or fall back to the first remote
DEFAULT_REMOTE=$(git config --get checkout.defaultRemote)
if [ -z "$DEFAULT_REMOTE" ]; then
  DEFAULT_REMOTE=$(git remote | head -n 1)
fi

if [ -z "$DEFAULT_REMOTE" ]; then
  echo "Error: No remote repository configured."
  exit 1
fi

# Fetch the remote reference and update the local reference
[ "$VERBOSE" = true ] && echo "Fetching from $DEFAULT_REMOTE and updating $LOCAL_REF"
git fetch "$DEFAULT_REMOTE" "$LOCAL_REF:$LOCAL_REF"

if [ $? -eq 0 ]; then
  [ "$QUIET" = false ] && echo "Successfully fetched and updated $LOCAL_REF."
else
  echo "Error: Failed to fetch and update $LOCAL_REF."
  exit 1
fi
