#!/bin/bash

# This script syncs a git repository between a Windows host and its WSL counterpart.
# WSL is slow at accessing Windows files, so this script is used to keep the Windows and its WSL counterpart in sync.


is_win=false
if [[ "$OSTYPE" == "msys" ]]; then
		is_win=true
fi

cd "$(git rev-parse --show-toplevel)" ||
	exit 1

name=$(basename "$PWD")

if [[ "$is_win" == true ]]; then
	if ! wsl 'git -C ~/repos/ clone --origin win '"'$PWD'"; then
		wsl 'git -C ~/repos/'"$PWD"' remote get-url win && git pull win'
	fi
	wsl_path=$(wsl 'wslpath -w ~/repos/'"$name"'')
	git remote add wsl "$wsl_path"
	git fetch wsl
else
	if ! git remote get-url win; then
		git remote add win '/mnt/c/Users/'"$USER"'/repos/'"$name"''
	fi
	git fetch win
fi
