#!/bin/sh

git diff-index \
	"$(git merge-base origin/development HEAD)" \
	--name-only \
	--relative . |\
	xargs sed -i 's/ *$//'
