#!/bin/sh



usage="\
git arch [<options>] <refname>

Create (at most one per 'stem') or list 'decorated' tags for refname.

A 'decorated' tag is a tag that follows the convention:
<decoration>/<refname>/\$(date)
It is basically a snapshot of a branch, implemented using tags.

A 'stem' is the initial part of the 'decorated' tag:
<decoration>/<refname>

### Use case

The typical use case are the decorations 'archive' and 'wip'.
- 'archive' tags represent persistant snapshots of a branch, e.g. for archiving
old branches, create persistant backup of local branch on upstream or
milestones in commit/rebase workflow.
- 'wip' tags represent more ethereal snapshots, e.g. push to send to colleague,
save a goodish state of tree etc.

--

h,help                  Show the help
l,list                  List tags of <refname>
d,decor=decoration      Use <decoration>, default 'archive'
"

eval "$(echo "$usage" | git rev-parse --parseopt -- "$@" || echo exit $?)"

listmode=false
decor=archive

while getopts ":d:l" opt; do
	case $opt in
		l)
			listmode=true
			;;
		d)
			decor="$OPTARG"
			;;
		*)
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

STEM="${decor}/${refname}/"

if [ "$listmode" = true ] ; then
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
