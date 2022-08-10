#!/bin/bash
set -euo pipefail

if [ -z "$1" ]; then
	printf "Fatal: argument needed" >&2 &&
	exit 1
fi

add=true
if [ "${1:0:1}" == "-" ]; then
	mark="${1:1}"
	add=false
else
	mark="$1"
fi
shift 1

if [ -z "${1:-}" ]; then
	branches="$(git branch --show-current)"
else
	branches="$@"
fi

tag_char='@'

for branch in $branches; do
	# branch starts with #mark
	if [[ $branch == $tag_char$mark/* ]]; then
		[[ $add == true ]] &&
			continue # already marked
		git branch -m $branch ${branch#$tag_char$mark/} # remove the mark
	elif [[ $add == false ]]; then continue
	else
		git branch -m $branch "#$mark/"${branch#$tag_char*/}
	fi
done