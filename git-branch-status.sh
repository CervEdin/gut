#!/bin/sh

git for-each-ref --format='%(refname:short)%09%(upstream:track)%09%(upstream:remotename)' refs/heads |\
	column -t -s $'\t'
