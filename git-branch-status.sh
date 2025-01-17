#!/bin/sh

# Default to refs/heads if no arguments are provided
if [ "$#" -eq 0 ]; then
    set -- "refs/heads"
fi

git for-each-ref \
	--sort='committerdate' \
	--format='%(refname:short)%09%(committerdate:short)%09%(upstream:track)%09%(upstream:remotename)' \
	"$@" |\
	column -t -s '	'
