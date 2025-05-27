#!/bin/bash

if [ -z "$1" ]; then
	printf "Fatal: argument needed (a mark name)" >&2 &&
	exit 1
fi

add=true
# If the first letter of 1st argument is -
if [ "${1:0:1}" == "-" ]; then
	# Assume the tag is +
	tag_char='+'
	# and that the mark is the rest
	mark="${1:1}"
	add=false
else
	# Otherwise the first argument is the tag character
	if [[ "${1:0:1}" =~ [[:punct:]] ]]; then
		tag_char="${1:0:1}"
		# and that the mark is the rest
		mark="${1:1}"
	else
		# otherwise, the tag character is +
		tag_char='+'
		# and the mark is the first argument
		mark="$1"
	fi
fi
shift 1

if [ -z "${1:-}" ]; then
	branches="$(git branch --show-current)"
else
	branches=$(printf '%s\n' "$@")
fi


for branch in $branches; do
	# branch starts with $tag_char
	if [[ $branch == $tag_char$mark/* ]]; then
		[[ $add == true ]] &&
			continue # already marked
		git branch -m "$branch" ${branch#$tag_char$mark/} # remove the mark
	elif [[ $add == false ]]; then continue
	else
		git branch -m "$branch" "$tag_char$mark/"${branch#$tag_char*/}
		ec=$?
		if [ $ec -ne 0 ]; then
			printf "Failed to mark branch '%s'\n" "$branch" >&2
			exit $ec
		fi
	fi
done

exit 0
