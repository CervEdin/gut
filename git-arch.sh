#!/bin/sh



usage="\
git arch [<options>] <refname>

Create (at most one per 'stem') or list 'archive tags' for refname.

An archive tag is a tag that follows the convention:
archive/<refname>/<date>
It is basically a snapshot of a branch, implemented using tags.
It can be used to archive old branches, or to create a persistant snapshot of a branch.

I mainly used it before I figured out how to use the reflog.

--

h,help                  Show the help
l,list                  List tags of <refname>
"

eval "$(echo "$usage" | git rev-parse --parseopt -- "$@" || echo exit $?)"

LISTMODE=false

while getopts ":l" opt; do
	case $opt in
		l)
			LISTMODE=true
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
