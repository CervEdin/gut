#!/bin/bash

LISTMODE=false

while getopts ":l" opt; do
	case $opt in
		l)
			LISTMODE=true
			;;
		\?)
			printf "Invalid option: -$OPTARG\n" >&2
			exit 1
			;;
	esac
done

shift $(($OPTIND - 1))

if [ $# -ne 0  ]; then
	refname="$1"
else
	refname=$(
		git symbolic-ref -q --short HEAD ||
			# if in detached head, assume rebase
			head "$(git rev-parse --show-toplevel \
			'.git/rebase-merge/head-name' |\
			sed 'N ; s@\n@\\@')" |\
			sed 's@refs/heads/@@'
	)
fi

STEM="archive/${refname}/"

if [ "$LISTMODE" == true ] ; then
	printf "list mode: ($refname\n" >&2
	git tag --list "$STEM*"
else
	TAG=$(git tag --list "$STEM*" --points-at HEAD)
	if [[ -z "$TAG" ]]; then
		TAG="${STEM}$(date --utc +'%Y-%m-%dT%H.%M.%S')"
		git tag "$TAG" "$refname"
	fi
	printf "Created tag: $TAG\n" >&2
	printf "$TAG\n"
fi
