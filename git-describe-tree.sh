#!/bin/sh

usage="\
git describe-tree [<options>] <tree-ish>

A wrapper around 'git describe' that uses the latest commit that modified
<tree> instead of HEAD.

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

path="$1"

path=$(realpath $1)
latest_tree=$(git ls-tree --object-only -d HEAD $path)
latest_commit=$(
  git rev-list --all |
  git diff-tree --stdin --find-object=$latest_tree |
  head -n1
)
git describe $@ "$latest_commit"
