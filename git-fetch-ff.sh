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
	s@\(.*\)\t\([^/]*\)/\(.*\)@\1\t\2\t\3@ # local, remote, upstream
	p
}' |
	awk -F '\t' '
NR==1 {
	# remote, local, upstream
	upstream[$2][$1] = $3
} NR>1 {
	upstream[$2][$1] = upstream[$2][$1] $3
} END {
	for (r in upstream) {
		args = r
		for (l in upstream[r]) {
			args = args FS upstream[r][l]":"l
		}
		print args
	}
}' |
	xargs -L 1 git fetch
