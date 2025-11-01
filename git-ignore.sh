#!/bin/sh

# sort flags: -f (fold case/ignore case), -u (unique), -o (output file)
printf '%s\n' "$@" |\
	cat - .gitignore |\
	sed '1{/^$/d};# skip empty first line if no args TODO: something better?' |\
	sort -f -u -o .gitignore
