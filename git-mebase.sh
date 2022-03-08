#!/bin/bash
set -euo pipefail

INTERACTIVE=false

while getopts ":i" opt; do
	case $opt in
		i)
			INTERACTIVE=true
			;;
		\?)
			printf "Invalid option: -$OPTARG\n"
			exit 1
			;;
	esac
done

PARENTS=$(git parents)

if [ "$INTERACTIVE" == true ] ; then
	nl <<< "$PARENTS"
	# TODO: Verify this works 10+
	read -p "Pick parent: " N_PARENT
else
	N_PARENT=1
fi

PARENT=$(sed "${N_PARENT}q;d" <<< "$PARENTS")

git arch &&\
  git -c sequence.editor='git rebase-retag.sh' rebase -i -r --autosquash "$PARENT"
