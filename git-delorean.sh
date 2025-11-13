#!/bin/bash

staged=$(git diff --name-only --relative --cached --diff-filter=M)

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
						# BSD awk compatible: use match and substr instead of gensub
						match($3, /[0-9]+/)
						r = substr($3, RSTART, RLENGTH)
					}
					if (r != 0) {
						print $2","$2 + r - 1
					}
					else {
						print $2","$2
					}}'
	)
	commits=$(
		<<< "$lines" \
		xargs \
			-I% \
				git blame \
					--incremental  \
					-L \
					% \
					"$revspec" \
					-- \
					"$file" |\
			awk \
			'/^[a-f0-9]{40} /{ a[$1]++ } END { for (b in a) { print b }}'
	)
	git rev-list --topo-order "$revspec" |\
		{ grep "$commits" || test $? = 1; } |\
		head -n 1 |\
		xargs \
			-I first_parent \
				git commit --fixup first_parent -- "$file"
done

git stash apply "$working_tree_sha" --index
