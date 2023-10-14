#!/bin/sh

printf '%s\n' $@ |\
	cat - .gitignore |\
	sed '1{/^$/d};# skip empty first line if no args TODO: something better?' |\
	sort --ignore-case --unique -o .gitignore
