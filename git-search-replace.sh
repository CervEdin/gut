#!/bin/bash

usage=''

search_for="$1"
replace_with="$2"

path=${3:-.}

git grep -l "$search_for" -- "$path" |\
	xargs -d '\n' sed -i s@"$search_for"@"$replace_with"@g
