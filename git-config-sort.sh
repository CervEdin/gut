#!/bin/sh

awk '{ if ($1 ~ /^\[/) { section=$0; printf "%s\t\n", $0 } else { printf section; print $0 } }' .gitconfig |
	sort -t ']' -k '1,1' |
	sed '/\t$/{s@@@;p;d};s@^[^\t]*@@' |
	sponge.sh .gitconfig
