#!/bin/sh

usage=''

for _ in $(seq "$1" "$2"); do
	git stash drop 'stash@{'"$1"'}'
done
