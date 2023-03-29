#!/bin/bash

if [ $# -ne 0  ]; then
	target=$1
else
	target=$(git symbolic-ref -q --short HEAD)
	git rev-list -1 HEAD |\
		xargs git checkout # detach HEAD to enable deletion of checked out branch
fi
{
	read local;
	read remote;
} < <(git rev-parse --abbrev-ref --symbolic-full-name "$target" "$target"'@{upstream}')

git push --delete "${remote%%/*}" "${remote#*/}" &&
	git branch -D "$local"
