#!/bin/sh

printf '%s\n' $@ |\
	cat .gitignore - |\
	sort -n -o .gitignore
