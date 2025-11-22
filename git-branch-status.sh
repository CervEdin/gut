#!/bin/sh

# Default to refs/heads if no arguments are provided
if [ "$#" -eq 0 ]; then
    set -- "refs/heads"

# If the last argument doesn't start with refs/
# treat it as a branch name
else
    last=$(
        for arg; do :; done
        printf '%s\n' "$arg"
    )
    case "$last" in
        refs/*)
            # already a ref, do nothing
            ;;
        *)
            # Get everything except the last argument
            args=$(printf '%s\n' "$@" | sed '$d')
            set --
            for arg in $args; do
                set -- "$@" "$arg"
            done
            # Append transformed last argument
            set -- "$@" "refs/heads/$last"
            ;;
    esac
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
