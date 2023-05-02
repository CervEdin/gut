#!/bin/sh

usage="\
branch-status

Show the status of all branches in the current repository.
--
h,help  Show help"

git for-each-ref --format='%(refname:short)%09%(upstream:track)%09%(upstream:remotename)' refs/heads |\
	column -t -s '	'
