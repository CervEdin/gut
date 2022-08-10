#!/bin/bash
set -euo pipefail

if [ "$GIT_ENV" == true ] ; then
	echo "Exiting git enviroment"
	unset -f aa
	unset -f ss
	unset -f sk
	unset -f dff
	unset -f sdf
	unset -f cm
	export GIT_ENV=false
else
	echo "Setting git enviroment"
	git config commit.verbose true
	aa () { git add --all ; }
	ss () { git status ; }
	sk () { git rebase --skip; }
	dff () { git diff ; }
	sdf () { git diff --staged ; }
	cm () { git commit -m $1 ; }
	export GIT_ENV=true
fi
