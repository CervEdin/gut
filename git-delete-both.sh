#!/bin/bash

usage="\
delete-both [<options>] [branch]...

Delete both local and remote branch.
If branch is not specified, delete current branch.
--
h,help      Show the help "

eval "$(echo "$usage" | git rev-parse --parseopt -- "$@" || echo exit $?)"

if [ $# -ne 0  ]; then
	target=$1
else
	target=$(git symbolic-ref -q --short HEAD)
	git rev-list -1 HEAD |\
		xargs git checkout # detach HEAD to enable deletion of checked out branch
fi
{
	read -r local;
	read -r remote;
} < <(git rev-parse --abbrev-ref --symbolic-full-name "$target" "$target"'@{upstream}')

git push --delete "${remote%%/*}" "${remote#*/}" &&
	git branch -D "$local"
