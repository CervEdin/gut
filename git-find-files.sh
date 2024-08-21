#!/bin/sh

usage="\
git find-files <grep-args>

Find using grep parameters <grep-args> across _all_ refs
(tags, branches, log, stash, remotes)
and sort it according to authordate of last commit containing that file.

--

h,help   Show the help "

eval "$(echo "$usage" | git rev-parse --parseopt -- "$@" || echo exit $?)"
shift

for b in $(git for-each-ref --format="%(refname)"); do
	files=$(git ls-tree -r --name-only $b | grep "${@:-.}" )
	if [ -n "$files" ]; then
		echo "$files" | while IFS= read -r file; do
			ad="$(git log -1 --format="%as" "$b" -- "$file")"
			printf '%s\t%s\t%s\n' "$b" "$ad" "$file"
		done
	fi
done | sort -k 2
