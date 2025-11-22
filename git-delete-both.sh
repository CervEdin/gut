#!/bin/bash

# TODO: handle missing upstream

if [ $# -ne 0  ]; then
	target=$1
else
	target=$(git symbolic-ref -q --short HEAD)
	git rev-list -1 HEAD |\
		xargs git checkout # detach HEAD to enable deletion of checked out branch
fi

# Check if the branch has an upstream that exists on the remote
if ! git rev-parse --abbrev-ref --symbolic-full-name "$target"'@{upstream}' > /dev/null 2>&1; then
	echo "No upstream branch found for '$target' or upstream has been deleted. Deleting local branch." >&2
	git branch -D "$target"
	exit 0
fi

# Get the local and remote branch references
{
	read -r local_ref;
	read -r remote_ref;
} < <(git rev-parse --abbrev-ref --symbolic-full-name "$target" "$target"'@{upstream}')

git push --delete "${remote_ref%%/*}" "${remote_ref#*/}" &&
	git branch -D "$local_ref"
