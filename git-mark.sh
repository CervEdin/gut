#!/bin/sh

usage="\
usage: git-mark.sh [-]mark [branch...]

Mark branches with a prefix.

options:
	[-]mark
		Mark branches with a prefix.
		If the mark starts with a dash, remove the mark.
		If the mark starts with a punctuation, use it as the mark.
		If the mark starts with a letter, use + as the mark.

Examples:
  git mark under-review
changes the current branch name to +under-review/<current-branch-name>
  git mark -under-review
removes the mark under-review from the current branch name
	git mark @reivewed b1 b2 b3
changes the branch names to @reivewed/b1 @reivewed/b2 @reivewed/b3"

if [ -z "$1" ]; then
	printf "Fatal: argument needed\n" >&2 &&
	printf '%s\n' "$usage" >&2 &&
	exit 1
fi

add=true
# If the first character is a dash, remove the mark
if [ "${1:0:1}" = "-" ]; then
	tag_char='+'
	mark="${1:1}"
	add=false
else
	# If the first character is a punctuation, use it as the mark
	if [ "${1:0:1}" =~ [[:punct:]] ]; then
		tag_char="${1:0:1}"
		mark="${1:1}"
	else
		tag_char='+'
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
	case $branch in
		$tag_char$mark/*)
			[ $add = true ] &&
				continue # already marked
			;;
		*) branch="$tag_char$branch";;
	esac

	# branch starts with $tag_char
	if [ $branch == $tag_char$mark/* ]; then
		[ $add == true ] &&
			continue # already marked
		git branch -m "$branch" ${branch#$tag_char$mark/} # remove the mark
	elif [ $add == false ]; then continue
	else
		git branch -m "$branch" "$tag_char$mark/"${branch#$tag_char*/}
	fi
done
