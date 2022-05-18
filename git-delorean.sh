#!/bin/bash
set -euox pipefail

git_root=$(git rev-parse --show-toplevel)
cd "$git_root"
staged=$(git diff --name-only --cached)
revspec="${1:-HEAD}"
working_tree_sha=$(git stash create)
#TODO: replace with git restore?
git stash --keep-index

IFS=$'\n'
for file in $staged; do
	# BUG: When there are only adds (@@ -XX,0 +YY,x) the first line will be XX
	# It should probably be YY + x
	# TODO: should this also use revspec?
	lines=$(
		git diff --word-diff=porcelain -U0 --cached HEAD -- "$file" |\
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
	commits=$(
		xargs --verbose -I% git blame --incremental  -L % $revspec -- "$file" <<< "$lines" |\
			sed -n '/^[a-f,0-9]\{40\} /{s@ .*@@;p}' |\
			awk '{ a[$1]++ } END { for (b in a) { print b }}'
	)
	git rev-list --topo-order $revspec |\
		{ grep "$commits" || test $? = 1; } |\
		head -1 |\
		xargs \
			--replace=first_parent \
				git commit --fixup first_parent -- "$file"
done

git stash apply $working_tree_sha --index
