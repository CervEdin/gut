#!/bin/bash
set -euo pipefail
set -x

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

printf 'args before update : %q\n' "$@" >&2
set -- "${args[@]}"
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
FILES=${@:$OPTIND}
if [ -z "$FILES" ]; then
  FILES='.'
fi

printf 'args after getopts  : %q\n' "$@" >&2
printf 'FILES (a pathspec) after getopts  : %q\n' "$FILES" >&2

if [ "$ours" == false ] && [ "$theirs" == false ] && [ "$both" == false ]; then
 die "You need to specify --ours, --theirs or --both"
fi

cd "$(git rev-parse --show-toplevel)"

ffiles() { git ls-files --unmerged -- $@ | cut -f 2 | uniq; }
ffiles "$FILES" | xargs -d '\n'  stat -- || die "Files not found"

if [ "$both" = true ]; then
  ffiles "$FILES" |\
    xargs -d '\n' sed -i -e '/^<\{7\}/d' -e '/^=\{7\}/d' -e '/^>\{7\}/d' --
elif [ "$ours" = true ]; then
  ffiles "$FILES" |\
    xargs -d '\n' sed -i -e '/^<\{7\}/d' -e '/^=\{7\}/,/^>\{7\}/d' --
elif [ "$theirs" = true ]; then
  ffiles "$FILES" |\
    xargs -d '\n' sed -i -e '/^<\{7\}/,/^=\{7\}/d' -e '/^>\{7\}/d' --
fi

if [ "$add" = true ]; then
	ffiles $FILES | xargs -d '\n' git add --sparse --
fi
