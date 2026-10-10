---
name: git-rebase-i
description: >-
  Any change to a commit behind HEAD is a history rewrite that needs `git rebase
  -i`, and under Claude Code a bare `git rebase -i` runs its todo list unedited
  and silently changes nothing, so you MUST use this skill, which drives the
  rebase through a scripted sequence editor. Invoke it as your first step
  (before any git command) when the user wants to: reword or fix the message of
  an earlier commit (named by SHA or "N commits back"); fold, squash, or absorb
  a typo/fix/"oops" commit into the earlier commit it belongs to; split one
  commit into several; strip debug logging, stray hunks, or files out of an
  older commit while keeping the rest; drop or reorder commits; purge a file
  from the whole branch; restructure commits onto a side branch merged back in;
  or tidy up a branch's commit series before review or sending patches. Even if
  the request sounds like a small edit, if the target commit isn't the tip, it's
  a history rewrite — use this skill. Do not use it when only the newest commit
  changes (`git commit --amend`), or for plain rebase-onto-upstream,
  cherry-pick, revert, or PR squash-merge.
argument-hint: <operation> <sha> [new-message]
allowed-tools: Bash
---

# Scripted git rebase -i

Rewrite commits behind HEAD with `git rebase -i`, driven by four helpers from
this plugin's `bin/`. That directory is on PATH while the plugin is installed;
if `git rebase-i-prep` is not found, call the scripts as
`${CLAUDE_SKILL_DIR}/../../bin/<name>`.

| helper                          | job                                                                         |
| ------------------------------- | --------------------------------------------------------------------------- |
| `git rebase-i-prep <commit>...` | checks the range, saves a way back, prints the rebase command               |
| `git rebase-i-todo <action>...` | the sequence editor: edits todo lines by commit, ends the todo with `break` |
| `git reword <commit> -m\|-F`    | an `amend!` commit that autosquash folds into `<commit>`                    |
| `git rebase-i-check`            | the report: tree, range-diff, notes, signatures, authors, branches          |

`$ARGUMENTS` is a free-form request, such as `reword abc1234 "new subject"` or
`drop abc1234`.

## Procedure

Every operation runs the same way. The recipes below only differ in the actions.

1. **Prep.** `git rebase-i-prep <commit>...` with every commit the operation
   touches. Read each `WARN` line. A `BLOCK` line stops you: tell the user what
   it says. Exit 3 means the commit is already on the upstream branch; ask
   before rewriting it, and rerun with `--allow-published` once they agree. Exit
   4 means `fixup!` or `squash!` commits are waiting in the range and an
   autosquash would fold them in; ask whether to fold them first.
2. **Say what should change.** Before the rebase, state the expected range-diff
   in a sentence: "only commit 3's message changes", or "commit 2 is gone and
   the tree loses debug.log".
3. **Rebase.** Run the `rebase` command prep printed, with the recipe's actions
   in `GIT_SEQUENCE_EDITOR`. The helper resolves each commit before it touches
   the todo, and fails the rebase before it starts if a commit has no todo line.
   The rebase pauses at a final `break`: the new history is on a detached HEAD
   and the branch has not moved.
4. **Check, then finish.** `git rebase-i-check`. Paste the whole report into
   your reply and compare it with step 2. If it matches and ends with
   `result ok`, run the `next` command it prints,
   `git -c notes.rewriteRef='refs/notes/*' rebase --continue`: the branch moves,
   `--update-refs` moves the branches inside the range, and the notes are copied
   by this command, so the `-c` has to reach it. Run `git rebase-i-check` once
   more to confirm those three. If the report does not match,
   `git rebase --abort` and report what it showed.
5. **Clean up.** `git status` must show no rebase in progress. Then forget the
   backup refs:

   ```bash
   git for-each-ref --format='%(refname)' refs/rebase-i | xargs -n1 git update-ref -d
   ```

## Recipes

Actions take any revision, but resolve the shas with `git rev-parse` first:
`HEAD~N` changes meaning as soon as a commit is added.

### Reword

Prep first: an `amend!` commit already in the range makes prep stop.

```bash
git rebase-i-prep <sha>
git reword <sha> -F - <<'EOF'
new subject

new body
EOF
GIT_SEQUENCE_EDITOR="git rebase-i-todo" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autosquash --autostash --rebase-merges --update-refs <base>
```

One `git reword` per commit; give prep all of them and run one rebase. The
`amend!` commits name their target by sha, so two commits with the same subject
cannot be confused, and `git log` shows every new message before the rebase
runs. `--autosquash` is needed here; the other recipes do not pass it.

### Drop

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo drop=<sha>" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

Expect the check to report a tree difference: the dropped change.

### Fixup or squash

Fold `<sha>` into the earlier `<target>`:

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo fixup=<sha>:<target>" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

`fixup` keeps `<target>`'s message. `squash` concatenates the two messages,
because the editor is `true`; for a new message, fixup and then reword.

### Reorder

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo move=<sha>:<after>" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

`<sha>` is replayed right after `<after>`. A move across a merge, label or reset
line is refused: that is a topology change, see the references.

### Edit: split a commit, or remove part of it

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo edit=<sha>" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

The rebase stops with `<sha>` replayed as HEAD. Confirm it:
`git log -1 --format='%h %s'` must show the target. Then invoke the
interactive-staging skill and follow its "Split committed work" section with
`<orig>` = HEAD. Commit each piece with the original author and date:

```bash
git commit --author="$(git log -1 --format='%an <%ae>' <orig>)" \
  --date="$(git log -1 --format=%aD <orig>)" -F <msg>
```

To remove part of the commit, commit only the pieces you keep, then discard the
rest:

```bash
git restore --staged --worktree -- :/
```

A bare `git restore -- .` leaves the intent-to-add entries of dropped files, and
`git rebase --continue` then refuses with "You must edit all merge conflicts".
Finally `git rebase --continue` replays the rest and reaches the break. Later
commits that touched removed lines conflict; resolve by dropping the removed
content from the incoming side, and `git rm <path>` for a modify/delete conflict
on a removed file.

### Purge a file from history; branch topology

Rare. Read `references/purge.md` or `references/topology.md` when asked for one.

## When the rebase stops anywhere else

- **A conflict.** Hand off to the resolve-merge-conflicts skill, then
  `git rebase --continue`.
- **"The previous cherry-pick is now empty."** The commit's change is already in
  the tree: `git rebase --skip`.
- **An edit stop at the wrong commit, or anything you cannot name.**
  `git rebase --abort` and report. Never `git rebase --quit`.

`git rebase --abort` restores every branch, including the ones `--update-refs`
would have moved. Notes missing after the continue are not lost: the second
check prints the `git notes copy --stdin` line that restores them from the
rewrite list saved at the break. After a `--continue`, the way back is
`git reset --keep refs/rebase-i/orig` on the branch and
`git update-ref refs/heads/<name> refs/rebase-i/heads/<name>` for each saved
branch; those two are the only ref moves this skill allows by hand.

## Rules

- **Never switch branches, never move a branch by hand** with `update-ref`,
  `reset` or plumbing. If no recipe fits, stop and ask.
- **Newest first, one operation per rebase.** Rewords are the exception: one
  autosquash folds them all.
- **Keep the printed flags.** `--rebase-merges` keeps merges, `--update-refs`
  carries the branches inside the range, `--autostash` handles a dirty tree
  (staged changes come back unstaged), `notes.rewriteRef` keeps notes.
- **Signatures do not survive a rewrite.** Prep warns when the range has signed
  commits; pass `-S` to the rebase if the user signs, or say that they are gone.
- **The report, not a summary.** The check's output goes into the reply whole.
