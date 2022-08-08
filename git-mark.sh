#!/bin/sh
set -euo

if [ -z "$1" ]; then
	printf "Fatal: argument needed (a mark name)" >&2 &&
	exit 1
fi

mark="$1"

git branch --show-current |\
	sed 's@^'"$mark"'/@@' |\
	xargs -I% git branch -m "$mark"'/'%
