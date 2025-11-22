#!/bin/bash

usage="\
git prune-merged.bash

Deletes all branches on remote origin already merged into origin/development that is authored by the current configured author (determined by email) that starts with either feature/ or maintenance/
--
h,help  Show the help"

eval "$(echo "$usage" | git rev-parse --parseopt -- "$@" || echo exit $?)"

git fetch --prune &&
  git for-each-ref --merged origin/development |
  cut -f 2 |
  sed -n '/^refs\/remotes\//{s@@@;p}' |
  grep '^feature/\|^maintenance/' |
  xargs -I% git rev-list -n1 --author=$(git config user.email) % -- |
  sort -u |
  xargs -I% -n1 git for-each-ref --points-at % |
  cut -f 2 |
  sed -n '/refs\/remotes\//{s@@@;s@^origin/@@;p}' |
  xargs -I% -n1 git push --delete origin %
