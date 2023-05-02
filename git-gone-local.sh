#!/bin/sh

usage=''

LC_ALL=C git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads/ |\
	sed -n '/ *\[gone\].*$/{s@@@;p}'
