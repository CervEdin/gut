#!/bin/sh

usage=''

git gone-local |
	xargs git branch -D
