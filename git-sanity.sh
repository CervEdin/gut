#!/usr/bin/env bash
set -euo pipefail

USAGE="\
Usage: git sanity [current|tip] [<diff-options>]

Convenient diffs during interactive rebase.

  current   diff stopped commit against HEAD (default)
  tip       diff HEAD against the original branch tip"

case "${1:-}" in
    -h|--help) echo "$USAGE"; exit 0 ;;
esac

rebase_dir="$(git rev-parse --absolute-git-dir)/rebase-merge"

if [[ ! -d "$rebase_dir" ]]; then
    echo "fatal: not in a rebase" >&2
    exit 1
fi

mode=current
if [[ ${1:-} = tip || ${1:-} = current ]]; then
    mode="$1"
    shift
fi

case "$mode" in
    current) exec git diff "$(<"$rebase_dir/stopped-sha")" HEAD "$@" ;;
    tip)     exec git diff HEAD "$(<"$rebase_dir/orig-head")" "$@" ;;
esac
