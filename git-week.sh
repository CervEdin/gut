#!/bin/sh

start_date="$1"
if [ -z "$1" ]; then
	start_date='1 week ago'
fi
start_date="$(date -d "$start_date" +%Y-%m-%d)"

if [ -z "$END_DATE" ]; then
	end_date='today'
fi
end_date="$(date -d "$END_DATE" +%Y-%m-%d)"

exlude_pattern='^review\|^bug/minizinc\|^release\|^wip\|^carrierToRadio\|^+'
exlude_pattern='^review\|^bug/minizinc\|^release\|^carrierToRadio\|^+'

echo "Start date: $start_date" >&2
echo "END DATE: $END_DATE" >&2
echo "End date: $end_date" >&2

git branch-status --no-merged HEAD 'refs/heads/**' |\
	grep -v "$exlude_pattern" |\
	awk \
	-v start_date="$start_date" \
	-v end_date="$end_date" \
	'$2 > start_date && (end_date == "" || $2 < end_date)'
