#!/bin/sh

config="$1"

awk '{ if ($1 ~ /^\[/) { section=$0; printf "%s\t\n", $0 } else { printf section; print $0 } }' "$config" |
	sort -t ']' -k '1,1' |
	sed '/\t$/{s@@@;p;d};s@^[^\t]*@@' |
	sponge.sh "$config"
