#!/usr/bin/env bash

die() { echo "ERROR: $*. Aborting" >&2; exit 1; }

eval "$(
    git rev-parse --parseopt -- "$@" <<'SPEC' || echo exit $?
git conflict-blame [options] [<pathspec>...]

Show a blamed view of every conflict hunk in the working tree.
--
c,commits   print only the unique non-zero short SHAs involved
SPEC
)"

commits_only=false
while test $# != 0; do
    case "$1" in
    -c|--commits) commits_only=true ;;
    --) shift; break ;;
    esac
    shift
done
# remaining $@ is the pathspec

# unmerged files matching pathspec (all unmerged if no pathspec given)
mapfile -t conflict_files < <(
    git ls-files -u -- "$@" | cut -f2 | sort -u
)
if [ "${#conflict_files[@]}" -eq 0 ]; then
    echo "no unmerged files found" >&2
    exit 0
fi

all_shas=()

for f in "${conflict_files[@]}"; do
    # pair <<<<<<< / >>>>>>> line numbers into -Lstart,end ranges
    mapfile -t ranges < <(
        grep -nE '^(<{7}|>{7})' "$f" | cut -d: -f1 | paste - - |
            sed 's/^/-L/; s/	/,/'
    )
    # skip files with no conflict markers
    [ "${#ranges[@]}" -gt 0 ] || continue

    if $commits_only; then
        # --root suppresses the ^ prefix git blame adds to root-commit lines
        mapfile -t shas < <(
            git blame --root "${ranges[@]}" -- "$f" |
                cut -d' ' -f1 | grep -vE '^0+$' | sort -u
        )
        all_shas+=("${shas[@]}")
    else
        # combined view: marker lines appear as 00000000 (Not Committed Yet)
        [ "${#conflict_files[@]}" -gt 1 ] && echo "=== $f ==="
        git blame "${ranges[@]}" -- "$f"
    fi
done

if $commits_only; then
    # deduplicate across files, print as a single space-separated line
    [ "${#all_shas[@]}" -gt 0 ] || exit 0
    printf '%s\n' "${all_shas[@]}" | sort -u | xargs
fi
