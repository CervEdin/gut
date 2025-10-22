#!/bin/sh

# Detect sed -i syntax (GNU vs BSD)
_tmp=$(mktemp)
echo "test" > "$_tmp"
if sed -i 's/test/test/' "$_tmp" 2>/dev/null; then
    SED_INPLACE='sed -i'
else
    SED_INPLACE='sed -i ""'
fi
rm -f "$_tmp"

git diff-index \
	"$(git merge-base origin/development HEAD)" \
	--name-only \
	--relative . |\
	tr '\n' '\0' | xargs -0 $SED_INPLACE 's/ *$//'
