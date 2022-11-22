#!/bin/sh

git for-each-ref \
	--format='%(refname:short)%09'\
'%(upstream:track)%09'\
'%(upstream:short)' |
	'refs/heads/*' |
	column -t -s $'\t' |
	sed -n '
/ *\[behind [0-9]*\] */{
	s@@\t@
	s@\(.*\)\t\(.*\)@\2\t\1:\1@
	p
}' |
	awk -F '\t' '
NR==1 {
	o[$1] = $2
} NR>1 {
	o[$1] = o[$1] FS $2
} END {
	for (x in o) print x, o[x]
}' |
	xargs git fetch
