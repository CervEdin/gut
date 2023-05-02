#!/bin/sh

usage="\
git rebase-retag [<options>] TODO

Retags commits in a rebase todo file.

Tags are not updated in a rebase.
This script updates tags in a rebase todo file.
--
h,help   Show help"

if [ $# -ne 0 ]; then
	TODO="$1"
	if [ ! -f "$TODO" ]; then
		echo "$TODO not a valid file"
		exit 1
	fi
else
	exit 1
fi

SED_CMD='/^p\(ick\)\{0,1\} [0-9a-f]*/{s|^p\(ick\)\{0,1\} \([0-9a-f]*\).*|\2|p;q}'
FIRST_SHA=$(sed --quiet "$SED_CMD" "$TODO")
echo "$FIRST_SHA"

TAGS=$(set +o pipefail; # grep fails w exit 1 on empty
	git tag --contains "$FIRST_SHA" |
	grep -v '^archive/' |
	xargs --no-run-if-empty -n 1 sh -c 'printf "$1\t" && git rev-list -n 1 $1' 'tag_and_sha')

IFS='
' # IFS=$'\n'
SED_CMDs=''
for TAG in $TAGS; do
	IFS='	' read -r NAME SHA <<< "$TAG"
	SHORT_SHA=${SHA::7}
	SED_CMD="/^[^#].*${SHORT_SHA}/s|\$|\nx git tag -f ${NAME}|"
	SED_CMDs="$SED_CMDs;$SED_CMD"
done

sed -e "$(cat "$HOME"/bin/git-rebase-indent)" \
-e "$SED_CMDs" -i "$TODO"

vim "$1"
