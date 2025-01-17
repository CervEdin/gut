#!/bin/sh

git for-each-ref \
	--sort='committerdate' \
	--format='%(refname:short)%09%(upstream:track)%09%(upstream:remotename)' \
	refs/heads |\
	column -t -s '	'
