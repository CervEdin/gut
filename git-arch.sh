#!/bin/bash
set -euo pipefail

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
	TARGET="$1"
else
	TARGET=HEAD
fi

NAME=$(
	git symbolic-ref -q --short "$TARGET" ||
		# if in detached head, assume rebase
		head "$(git rev-parse --show-toplevel \
		'.git/rebase-merge/head-name' |\
		sed 'N ; s@\n@\\@')" |\
		sed 's@refs/heads/@@'
)
STEM="archive/${NAME}/"

if [ "$LISTMODE" == true ] ; then
	printf "list mode: ($TARGET)\n" >&2
	git tag --list "$STEM*"
else
	git tag "$STEM$(date --utc +'%Y-%m-%dT%H.%M.%S')" "$TARGET"
fi
