#!/bin/sh
# next..seen
case "$#,$1" in
1,-u|1,-d)
	exec Meta/Reintegrate "$1" "$0"
esac
Meta/Reintegrate "$@" <<\EOF
claude/contributing-expand
EOF
