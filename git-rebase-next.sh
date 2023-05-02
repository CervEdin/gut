#!/bin/sh

usage=''

# Get the SHA of the next todo item
sed -n '1{s@^[a-z]* \([0-9a-f]\{40,\}\) .*@\1@;p}' .git/rebase-merge/git-rebase-todo
