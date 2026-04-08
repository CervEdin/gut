#!/bin/bash

# Detect sed -i syntax (GNU vs BSD)
_tmp=$(mktemp)
echo "test" > "$_tmp"
if sed -i 's/test/test/' "$_tmp" 2>/dev/null; then
    SED_INPLACE='sed -i'
else
    SED_INPLACE='sed -i ""'
fi
rm -f "$_tmp"

search_for="$1"
replace_with="$2"

path=${3:-.}

git grep -l "$search_for" -- "$path" |\
	tr '\n' '\0' | xargs -0 $SED_INPLACE "s@$search_for@$replace_with@g"
