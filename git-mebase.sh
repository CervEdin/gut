#!/bin/bash

INTERACTIVE=false

while getopts ":i" opt; do
	case $opt in
		i)
			INTERACTIVE=true
			;;
		\?)
			printf -- 'Invalid option: -%s\n' "$OPTARG"
			exit 1
			;;
	esac
done

PARENTS=$(git parents)

if [ "$INTERACTIVE" == true ] ; then
	nl <<< "$PARENTS"
	read -r -p "Pick parent: " N_PARENT
else
	N_PARENT=1
fi

PARENT=$(sed "${N_PARENT}q;d" <<< "$PARENTS")

git arch &&\
  git -c sequence.editor='git rebase-retag' rebase -i -r --autosquash "$PARENT"
