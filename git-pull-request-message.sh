#!/bin/sh

usage=''

TARGET=$1

if [ -z "$1" ]; then
  TARGET=HEAD
fi

git log --pretty=format:"- ##%s%n%n%b" main.."$TARGET" --reverse
