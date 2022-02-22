#!/bin/bash

LISTMODE=false

while getopts ":l" opt; do
	case $opt in
		l)
			LISTMODE=true
			;;
		\?)
			printf "Invalid option: -$OPTARG\n"
			exit 1
			;;
	esac
done

shift $(($OPTIND - 1))

TARGET="$1"

if [ -z "$1" ]; then
	TARGET=$(git symbolic-ref --short HEAD)
fi

if [ "$LISTMODE" == true ] ; then
	printf "list mode: ($TARGET)\n"
	git tag | grep "archive/$TARGET"
else
	git tag archive/"$TARGET"-$(date --utc +'%Y-%m-%dT%H.%M.%S') "$TARGET"
fi
