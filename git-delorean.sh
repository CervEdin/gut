#!/bin/bash
set -euo pipefail

GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"
STAGED=$(git diff --name-only --cached)
git stash --keep-index

IFS=$'\n'
for FILE in $STAGED; do
	# BUG: When there are only adds (@@ -XX,0 +YY,x) the first line will be XX
	# It should probably be YY + x
	LINES=$(
		git diff --word-diff=porcelain -U0 --cached HEAD -- "$FILE" |\
			awk -F '[, ]' '/^@@/ {
					gsub(/^[^0-9]*/, "", $2)
					r = 0
					if (substr($3,1,1) != "+") {
						r = gensub(/([0-9]*).*/, "\\1", "g", $3)
					}
					if (r != 0) {
						print $2","$2 + r - 1
					}
					else {
						print $2","$2
					}}'
	)
	COMMITS=$(
		xargs --verbose -I% git blame --incremental  -L % HEAD -- "$FILE" <<< "$LINES" |\
			sed -n '/^[a-f,0-9]\{40\} /{s@ .*@@;p}' |\
			awk '{ a[$1]++ } END { for (b in a) { print b }}'
		)
		FIRST_PARENT=$(git rev-list --topo-order HEAD | grep "$COMMITS" | head -1)
		git commit --fixup $FIRST_PARENT -- "$FILE"
done

git stash pop
