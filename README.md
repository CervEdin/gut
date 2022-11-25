# Gut

Gut is a collection of scripts for git.
Basically, it's a collection of git helper scripts that I use and that help me
in my usage of git.
I try and adher to conventions of the git-project and I aim for POSIX
compliance.
That said, these scripts are very much developed after my needs and personal taste.
PRs are welcome.

```
 ______________
< Gut is good! >
 --------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||

```

# Overview
- `git arch`\
Creates and manges "archive" tags.
- `git branch-status`\
Displays status of local branches, tracking or not, compared to remote branches.
- `git delete-both`\
Deletes a branch, and IFF it's tracking, its remote counterpart.
- `git delorean`\
Creates fixup commits from staged changes, to go back in time and fix things.
- `git env`\
Sources a git environment into the current shell.
- `git fetch-ff`\
Fast-forward fetches all tracking, non checked out branches from their remote.
- `git gone-local`\
Lists tracking branches where remote is "gone".
- `git ignore`\
Adds filenames and/or patterns to `./.gitignore` and sorts `./.gitignore`.
- `git mark`\
"Marks" branches, by prepending a char (default `+`) to the name.
- `git mebase`\
Git rebase helper script, automatically or interactivelly finds the closest "parent" ref to rebase (with auto fixup/squash) onto.
- `git parents`\
Lists parent refs of current HEAD, sorted by committerdate, latest first.
- `git push-interactive`\
A git push helper script, lists the diff of upstream and prompt to push or force push.
- `git prune-local`\
Prunes tracking branches where upstream is "gone".
- `git pull-request-message`\
Creates pull request message, designed for Azure DevOps, from git log (includes message and not just subject.)
- `git rebase-indent`\
Indents branches in the rebase todo list.
- `git rebase-retag`\
Updates tags during rebase, similar to the git-rebase --update-refs feature except for tags.
- `git resolve`\
Resolves merge conflicts, in favor of either ours/theirs/both while retaining non-merge conflict changes.
- `git search-replace`\
Search and replace string across the repository, starting at `./`.
- `git stash-drop-range`\
Drops a range of stash items from stash.

# Installation

1. Put files somewhere in path.
Like `~/bin/` or run `make INSTALL_DIR=/bin/ all`,
which copies them into `/bin/` or whichever `INSTALL_DIR` you specify.
2. Run command like so: `git arch`
3. 💲💲💲

# Warranty

100% without any sort of warranty/guarantee.
