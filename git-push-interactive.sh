#!/bin/bash

usage="\
git push-interactive

Interactive push helper script.

Show the diff between HEAD and @{upstream} and confirm wether to push.
Optionally, force push."

git rev-parse HEAD '@{upstream}' |\
 uniq |\
 sed -n -e '${1p}' -e '2q 1' &&
 printf 'no changes\n' &&
 exit 0

git log --oneline --graph '@{upstream}...HEAD'
printf '\n'
git diff '@{upstream}' HEAD

while [ -z "${REPLY-}" ]; do
	read -p "Push? [Yy/Ff/*]" -r
	printf '\n'
done

if [[ $REPLY =~ ^[YyFf]$ ]]; then
	if [[ $REPLY =~ ^[Ff]$ ]]; then
		git push --force-with-lease
		exit $?
	fi
	unset REPLY
	git push &&
		exit 0 ||
		[ $? -eq 128 ] &&
		exit 128 # probably network issue
	while [ -z "${REPLY-}" ]; do
		read -p "Force push? [Ff/*]" -r
		printf '\n'
	done
	if [[ $REPLY =~ ^[Ff]$ ]]; then
		git push --force-with-lease
		exit $?
	fi
fi

exit 1
