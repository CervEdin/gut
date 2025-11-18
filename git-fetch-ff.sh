#!/bin/sh

worktree_list="$(mktemp)"

git worktree list --porcelain |
	sed -n '/^branch /{s@@@;p;}' |
	sort > "$worktree_list"


git for-each-ref --format='%(refname)' 'refs/heads/**/*' |
	sort |
	comm -23 - "$worktree_list" |
		tr '\n' ' ' |
		xargs git for-each-ref \
	--format='%(refname:short)%09'\
'%(upstream:track)%09'\
'%(upstream:remotename)%09'\
'%(upstream:remoteref)' |
	sed -n '
/\t*\[behind [0-9]*\]\t*/{
	s@@\t@
	p;
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
