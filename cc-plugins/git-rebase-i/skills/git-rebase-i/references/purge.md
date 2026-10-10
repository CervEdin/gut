# Purge files from history

Files were added in commit A, changed in B..N and deleted in Z. The goal is a
history in which they never appear. Follow the Procedure in SKILL.md; this page
gives the actions and the stops.

Find A and Z:

```bash
git log --diff-filter=A --format='%h %s' -- <files>   # the last line is A
git log --diff-filter=D --format='%h %s' -- <files>   # Z
```

Prep with both and stop at both:

```bash
git rebase-i-prep <A> <Z>
GIT_SEQUENCE_EDITOR="git rebase-i-todo edit=<A> edit=<Z>" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

At A, remove the files and amend:

```bash
git rm -q <files>
git commit --amend --no-edit
git rebase --continue
```

At each conflict in B..N the files no longer exist on our side. Remove them and
go on:

```bash
git rm -q --ignore-unmatch <files>
git rebase --continue
```

At Z there is nothing left to delete. If the stop says "The previous cherry-pick
is now empty", Z only deleted the files: `git rebase --skip`. Otherwise
`git status` names Z as the last command done and HEAD is Z's replay; review
`git show --stat` and amend the message for what remains:

```bash
git commit --amend -m "<message for the remaining changes>"
git rebase --continue
```

At the break, the check reports a tree difference of exactly the purged files,
and one commit fewer when Z was skipped. Tell the user that the content is still
reachable from the reflog, from `refs/rebase-i/orig` until the cleanup step, and
from any remote that has the old commits.
