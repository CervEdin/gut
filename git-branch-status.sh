#!/bin/sh

# Default to refs/heads if no arguments are provided
if [ "$#" -eq 0 ]; then
    set -- "refs/heads"

# Otherwise classify each argument for git for-each-ref:
#   * a leading `-` is a for-each-ref flag (a dash cannot begin a branch
#     name), passed through untouched
#   * a refs/* value is a ref pattern, used as-is
#   * anything else is treated as a branch pattern, expanded to
#     refs/heads/<name>
#
# A `--` separator is accepted but, since each argument is classified on
# its own, it has no effect on the result.
else
    n=$#
    # Consume the original args from the front, appending each (possibly
    # rewritten) result to the back until the original n are processed.
    while [ "$n" -gt 0 ]; do
        arg=$1
        shift
        n=$((n - 1))

        case "$arg" in
            --)
                # Tolerated separator; drop it.
                ;;
            -*|refs/*)
                # A for-each-ref flag or an explicit ref pattern: as-is.
                set -- "$@" "$arg"
                ;;
            *)
                # A branch shortname: expand to its full ref.
                set -- "$@" "refs/heads/$arg"
                ;;
        esac
    done
fi

git for-each-ref \
    --no-contains origin/HEAD \
    --sort='committerdate' \
    --format='%(refname:short)%09%(committerdate:short)%09%(upstream:track)%09%(upstream:remotename)%09%(ahead-behind:origin/HEAD)' \
    "$@" |\
    column -t -s '	'
git for-each-ref \
    --contains origin/HEAD \
    --sort='committerdate' \
    --format='%(refname:short)%09%(committerdate:short)%09%(upstream:track)%09%(upstream:remotename)%09%(ahead-behind:origin/HEAD)' \
    "$@" |\
    column -t -s '	'
