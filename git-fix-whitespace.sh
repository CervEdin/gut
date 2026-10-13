#!/bin/sh

# Detect sed -i syntax (GNU vs BSD)
_tmp=$(mktemp)
if sed -i 'p' "$_tmp" 2>/dev/null; then
    set -- sed -i
else
    set -- sed -i ''
fi
rm -f "$_tmp"

git diff-index \
	"$(git merge-base origin/development HEAD)" \
	--name-only \
	--relative . |\
	tr '\n' '\0' | xargs -0 "$@" 's/ *$//'
