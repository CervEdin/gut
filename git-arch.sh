#!/bin/sh

usage="\
	Usage: git arch [-l] [refname]

Create or list an \"archive tag\" for refname.

An archive tag is a tag that follows the convention:
archive/<refname>/<date>
It is basically a snapshot of a branch, implemented using tags.
It can be used to archive old branches, or to create a persistant snapshot of a branch."

LISTMODE=false

while getopts ":l" opt; do
	case $opt in
		l)
			LISTMODE=true
			;;
		\?)
			case $opt in h)
				printf -- '%s\n' "$usage" >&2
				exit 0
				;;
			esac
			printf -- 'Invalid option: -%s\n\n' "$OPTARG" >&2
			printf -- '%s\n' "$usage" >&2
			exit 1
			;;
	esac
done

shift $((OPTIND - 1))

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

if [ "$LISTMODE" = true ] ; then
	printf -- 'list mode: (%s\n' "$refname" >&2
	git tag --list "$STEM*"
else
	TAG=$(git tag --list "$STEM*" --points-at HEAD)
	if [ -z "$TAG" ]; then
		TAG="${STEM}$(date --utc +'%Y-%m-%dT%H.%M.%S')"
		git tag "$TAG" "$refname"
	fi
	printf -- 'Created tag: %s\n' "$TAG" >&2
	printf -- '%s\n' "$TAG"
fi
