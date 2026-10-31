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
   touches, after any commits the recipe says to make before it. Reword and
   "Fold an existing commit" are the exceptions: they run prep before
   `git reword`, because prep exits 4 on the commit that `git reword` makes.
   Read each `WARN` line. A `BLOCK` line stops you: tell the user what it says.
   Exit 3 means the commit is already on the upstream branch; ask before
   rewriting it, and rerun with `--allow-published` once they agree. Exit 4
   means `fixup!`, `squash!` or `amend!` commits that you did not make are
   waiting in the range. The user may keep them to fold later, so ask before
   folding them, and rerun with `--allow-fixups` only once they agree.
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

One `git reword` per commit; give prep all of them and run one rebase. `git log`
shows every new message before the rebase runs.

### Fold new fixes into earlier commits

Commit each new fix on top of HEAD as a `fixup!` commit; one autosquash rebase
folds them all in. Git puts each `fixup` line right after its target, also
inside a side branch merged into HEAD, and redoes the merge.

```bash
start=$(git rev-parse HEAD)
git add <the fix for target 1>
git commit --fixup=<target1>
git add <the fix for target 2>
git commit --fixup=<target2>
git rebase-i-prep --allow-fixups-from="$start" <target1> <target2>
GIT_SEQUENCE_EDITOR="git rebase-i-todo" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autosquash --autostash --rebase-merges --update-refs <base>
```

- One file with fixes for two targets: stage each part with interactive-staging.
- Before committing, check that the targets are on one line of history: one of
  them must be an ancestor of all the others (`git merge-base --is-ancestor`).
  If they are on different lines of a merge, prep refuses. Commit only one
  line's fixes, leave the rest unstaged (`--autostash` keeps them), and fold the
  next line in another pass.
- Commit the fixes before prep, so its backup includes them and the check
  reports the tree identical.
- Record `start` before the first `git commit --fixup`. Prep allows only the
  `fixup!`, `squash!` and `amend!` commits made since then, and exits 4 for an
  older one. Autosquash would fold that one too, so ask the user first; if they
  agree, pass `--allow-fixups` and include it in step 2's expected change.
- A fix to lines that a later commit also changed conflicts twice: at its fold,
  and again at that later commit. At the fold, keep only the target's version
  plus the fix, without the later commit's lines; resolve the later commit as
  usual.

### Drop

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo drop=<sha>" \
  git -c rebase.autoSquash=false -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

Expect the check to report a tree difference: the dropped change.

### Fold an existing commit

Fold `<sha>`, a commit already in the range, into `<target>`, an ancestor of
`<sha>`. Git folds only `fixup!` and `squash!` commits, so this takes two
rebases: the first rewords `<sha>` into a `fixup!` commit, the second folds it
with autosquash. Run the whole Procedure for each, with the base its prep
prints, and the checks below in its step 4.

```bash
start=$(git rev-parse HEAD)
git rebase-i-prep --fold-into=<target> <sha>
git reword <sha> -m "fixup! $(git log -1 --format=%s <target>)"
GIT_SEQUENCE_EDITOR="git rebase-i-todo" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autosquash --autostash --rebase-merges --update-refs <base1>
git rebase-i-check --expect-fixup=<target>

git rebase-i-prep --allow-fixups-from="$start" <target>
GIT_SEQUENCE_EDITOR="git rebase-i-todo" git -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autosquash --autostash --rebase-merges --update-refs <base2>
git rebase-i-check
git rebase-i-check "$start" <base2>
```

- A `BLOCK` from the first prep's `--fold-into` means `<target>` is not an
  ancestor of `<sha>`, for example when one of them is on a side branch that is
  merged in after the other. Autosquash cannot fold across that, and moving the
  change to another branch is a topology change: stop and ask the user, and see
  `references/topology.md`.
- In the first rebase only `<sha>`'s message changes. With `--expect-fixup`, the
  check names `<sha>`'s new `fixup!` commit as expected and ends in `result ok`.
  Any other `fixup!`, `squash!` or `amend!` commit left in the range still
  warns.
- Record `start` before the first prep. The second prep then allows the `fixup!`
  commit that the first rebase made, and exits 4 for one that was in the range
  before.
- The last check compares the tip from before both rebases with the result: only
  `<target>` changes, `<sha>` is gone, and the tree is identical.
- `fixup!` keeps `<target>`'s message. `squash!` concatenates the two, because
  the editor is `true`; for a new message, fold and then reword.

### Reorder

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo move=<sha>:<after>" \
  git -c rebase.autoSquash=false -c notes.rewriteRef='refs/notes/*' \
  rebase -i --autostash --rebase-merges --update-refs <base>
```

`<sha>` is replayed right after `<after>`. A move across a merge, label or reset
line is refused: on the far side of such a line a commit is built on a different
parent, so it lands on a different branch. That is a topology change, see the
references.

### Edit: split a commit, or remove part of it

```bash
GIT_SEQUENCE_EDITOR="git rebase-i-todo edit=<sha>" \
  git -c rebase.autoSquash=false -c notes.rewriteRef='refs/notes/*' \
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
- **Newest first, one operation per rebase.** Rewords and new fixes are the
  exception: one autosquash folds them all.
- **Keep the printed flags.** `--rebase-merges` keeps merges, `--update-refs`
  carries the branches inside the range, `--autostash` handles a dirty tree
  (staged changes come back unstaged), `notes.rewriteRef` keeps notes. Add
  `--autosquash` only where a recipe's command has it: it folds every `fixup!`,
  `squash!` and `amend!` commit in the range, not only yours. Every other
  command sets `-c rebase.autoSquash=false`, since the user's config may turn
  autosquash on for every `git rebase -i`; keep it.
- **Signatures do not survive a rewrite.** Prep warns when the range has signed
  commits; pass `-S` to the rebase if the user signs, or say that they are gone.
- **The report, not a summary.** The check's output goes into the reply whole.
