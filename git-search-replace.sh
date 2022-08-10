#!/bin/sh

search_for="$1"
replace_with="$2"

if [ -z "$3" ]; then
	path='.'
else
	path="$3"
fi

git grep -l "$search_for" -- "$path" |\
	xargs -d '\n' sed -i s@"$search_for"@"$replace_with"@g
