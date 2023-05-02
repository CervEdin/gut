#!/bin/sh

usage=''

# sort by committerdate, latest first
git for-each-ref --merged HEAD --no-contains HEAD \
	--sort="-committerdate" \
	--sort="-creatordate" \
	--format="%(refname:short)" \
  -- 'refs/heads/' 'refs/tags/' |\
  grep -v 'archive/*'
