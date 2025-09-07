#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 [<start-commit-or-tag>] <path> [<path>...]" >&2
  exit 1
fi

# If the first arg is a valid commit-ish, treat it as START
if git rev-parse -q --verify "$1^{commit}" >/dev/null 2>&1; then
  START=$1
  shift
  RANGE="$START..HEAD"
else
  START=
  RANGE=HEAD
fi

for path in "$@"; do
  printf '%s\n' "$path"
  git log --follow -M --name-status --pretty=format: "$RANGE" -- "$path" |
  awk -F '\t' -v cur="$path" '
    BEGIN { seen[cur]=1 }
    $1 ~ /^R[0-9]+$/ { if (!seen[$2]) { print "  " $2; seen[$2]=1 }
                       if (!seen[$3]) { print "  " $3; seen[$3]=1 }
                       next }
    NF>=2 { if (!seen[$2]) { print "  " $2; seen[$2]=1 } }
  '
done
