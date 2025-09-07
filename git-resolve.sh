#!/bin/bash

die () {
  echo "ERROR: $*. Aborting" >&2
  exit 1
}

args=( )

for arg; do
  case "$arg" in
    --help|-h)
      args+=( -h ) ;;
    --ours|-o)
      args+=( -o ) ;;
    --theirs|-t)
      args+=( -t ) ;;
    --both|-b)
      args+=( -b ) ;;
    --add|-a)
      args+=( -a ) ;;
    *)
      args+=( "$arg" ) ;;
  esac
done

[[ $- =~ x ]] &&
	printf 'args before update : %q\n' "$@" >&2
set -- "${args[@]}"
[[ $- =~ x ]] &&
	printf 'args after update  : %q\n' "$@" >&2

ours=false
theirs=false
both=false
add=false

while getopts ":otba" opt; do
    case $opt in
    o ) if [ "$theirs" = true ]; then die "Cannot specify ours and theirs" ;fi
      ours=true ;;
    t ) if [ "$ours" = true ]; then die "Cannot specify ours and theirs" ;fi
      theirs=true ;;
    b ) both=true ;;
    a ) add=true ;;
    \?) die "Unknown option: -$OPTARG. Abort" ;;
    : ) die "Missing option: -$OPTARG. Abort" ;;
    * ) die "Unimplemented option: -$OPTARG. Abort" ;;
  esac
done

files=("${@:$OPTIND}")

case "${files[@]}" in
	'')
		# Default is everything (.) relative to PWD
		files=('.')
		;;
	'-')
		files=('/dev/stdin')
		;;
esac

[[ $- =~ x ]] &&
	printf 'args after getopts	: %q\n' "$@" >&2 &&
	printf 'files (a pathspec) after getopts	: %q\n' "${files[@]}" >&2

if [ "$ours" == false ] && [ "$theirs" == false ] && [ "$both" == false ]; then
 die "You need to specify --ours, --theirs or --both"
fi

ffiles() {
  git ls-files --unmerged -- "$@" |
    cut -f 2 |
    uniq
}

if [ "$both" = true ]; then
	sed_script='
# Just delete all conflict markers
/^<\{7\}/d
/^[|=]\{7\}/d
/^>\{7\}/d'
elif [ "$ours" = true ]; then
	sed_script='
# Delete "our" markers
/^<\{7\}/d
# Delete everything in "their" conflicts
/^[|=]\{7\}/,/^>\{7\}/d'
elif [ "$theirs" = true ]; then
	sed_script='
# Delete everything in "our" conflicts
/^<\{7\}/,/^=\{7\}/d
# Delete "their" markers
/^>\{7\}/d'
fi

case ${files[0]} in
	- | /dev/stdin )
		sed "$sed_script" /dev/stdin &&
			exit 0

		;;
	*)
		ffiles "${files[@]}" |
			xargs -d '\n' -I%  find % |
			xargs -d '\n' -I% sed -i "$sed_script" % ||
			die "Files not found"

		ffiles "${files[@]}" |
		if [ "$add" = true ]; then
			tee >(xargs -d '\n' git add --update --sparse --)
		else
			cat
		fi
		;;
esac
