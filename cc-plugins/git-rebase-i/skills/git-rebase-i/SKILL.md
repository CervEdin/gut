---
name: git-rebase-i
description: Scripted git rebase -i — reword, edit, or drop commits without interactive mode
argument-hint: <operation> <sha> [new-message]
allowed-tools: Bash
---

# Scripted git rebase -i

Perform `git rebase -i` operations non-interactively using `GIT_SEQUENCE_EDITOR`
and `GIT_EDITOR`.

## Arguments

- `$ARGS` — free-form description of what to do. Examples:
  - `reword abc1234 "new subject line"`
  - `reword abc1234 and def5678` (will ask for new messages)
  - `drop abc1234`

## Preparation

Before any rebase, check the working tree state and for an existing `.rebase/`
directory (another rebase may be in progress — ask the user before proceeding),
then save the original HEAD:

```bash
git status
if [ -d .rebase ]; then
  echo ".rebase/ already exists — another rebase may be in progress"
  # Ask the user before proceeding
fi
mkdir -p .rebase
git rev-parse HEAD > .rebase/ORIGINAL_HEAD
```

If `git status` shows a rebase is already in progress, do NOT start a new one —
ask the user how to proceed.

## Cleanup

After the rebase completes and `git diff` verification passes, remove the
temporary `.rebase/` directory:

```bash
rm -r .rebase/
```

## Rewording commits

Rewording only changes commit messages — no tree or content changes. This means
there are no cascading conflicts to worry about, so multiple rewords can safely
be batched into a single rebase using `exec` lines. Doing them incrementally
would also cause SHAs to shift after each rebase, adding unnecessary complexity.

### Single commit

Use `edit` + `amend`:

#### 1. Write the sed script

```bash
cat > .rebase/edit.sed <<'EOF'
s/^(pick|p) <sha>/e <sha>/
$a\
break
EOF
```

#### 2. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i <sha>^
```

#### 3. Amend and continue

```bash
GIT_EDITOR="sed -i '' '1s/.*/new subject/'" git commit --amend
git rebase --continue
```

For subject-only rewording, `GIT_EDITOR` sed is the right tool. When the full
message context matters (e.g. the subject depends on remaining changes after
editing), use `git show --stat` to review, then `git commit --amend -m "..."`.

After the rebase, verify with `git diff $(cat .rebase/ORIGINAL_HEAD)` — it
should be empty.

### Multiple commits (batch reword)

Write a sed script with one `1s` substitution per commit — exact old subject →
exact new subject. Each rule only fires on the matching commit; all others are
no-ops.

#### 1. Write the reword sed script

```bash
cat > .rebase/reword.sed <<'SEDEOF'
1s/^old subject one/new subject one/
1s/^old subject two/new subject two/
SEDEOF
```

**POSIX note:** sed does not interpret `\t` as a tab character. If the
replacement text needs literal tabs, the file must contain actual tab bytes.

#### 2. Write the sequence editor sed script

Insert an `exec` line after each `pick` that needs rewording:

```bash
cat > .rebase/edit.sed <<'EOF'
/^(pick|p) <sha-1>/{
a\
x GIT_EDITOR='sed -i "" -f .rebase/reword.sed' git commit --amend
}
/^(pick|p) <sha-2>/{
a\
x GIT_EDITOR='sed -i "" -f .rebase/reword.sed' git commit --amend
}
$a\
break
EOF
```

#### 3. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i --rebase-merges --update-refs <oldest-sha>^
```

#### 4. Verify at break

```bash
git diff $(cat .rebase/ORIGINAL_HEAD)   # should be empty
git log --oneline                       # check subjects
git rebase --continue                   # finalize
```

## Dropping a commit

### 1. Write the sed script

```bash
cat > .rebase/edit.sed <<'EOF'
s/^(pick|p) <sha>/d <sha>/
$a\
break
EOF
```

### 2. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i <sha>^
```

## Fixup (absorb a commit into a specific earlier commit)

Two-rebase approach: first mark the fixup, then autosquash.

### 1. Write the sed script

```bash
cat > .rebase/edit.sed <<'EOF'
s/^(pick|p) <sha-to-absorb>/e <sha-to-absorb>/
$a\
break
EOF
```

### 2. Stop at the commit to absorb

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i <sha-to-absorb>^
```

### 3. Mark it as a fixup for the target

```bash
git commit --amend --fixup=<target-sha>
git rebase --continue
```

### 4. Autosquash to fold it in

```bash
GIT_SEQUENCE_EDITOR=cat git rebase -i --autosquash --rebase-merges --update-refs <target-sha>^
```

Verify with `git diff $(cat .rebase/ORIGINAL_HEAD)` after each rebase.

## Edit (remove parts of a commit)

Stop at the commit, reset, selectively re-stage only what you want to keep.

### 1. Write the sed script

```bash
cat > .rebase/edit.sed <<'EOF'
s/^(pick|p) <sha>/e <sha>/
$a\
break
EOF
```

### 2. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i <sha>^
```

### 3. Reset, re-stage, and continue

```bash
git reset HEAD^                  # undo commit, unstage all changes
# Edit the worktree to keep only what you want
git add <files>                  # stage the desired changes
git commit -m "new message"
git rebase --continue
```

Expect downstream conflicts on lines that were removed — resolve by dropping the
removed content from the incoming side.

## Purge files from history

For when files were added in commit A, modified in B..N, deleted in Z — goal is
to remove them from all commits so they never appear in history.

First, identify the commits. Find deletions on the current branch (commit Z):

```bash
git log --diff-filter=D --stat --oneline origin/HEAD..
```

Then find where those files were originally added (commit A):

```bash
git log --diff-filter=A --stat --oneline origin/HEAD..
```

1. Write the sed script and start the rebase:

```bash
cat > .rebase/edit.sed <<'EOF'
s/^(pick|p) <sha-A>/e <sha-A>/
s/^(pick|p) <sha-Z>/e <sha-Z>/
$a\
break
EOF
```

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i <sha-A>^
```

2. At A: remove the files and amend:

```bash
git rm <files>
git commit --amend --no-edit
git rebase --continue
```

3. At each conflict (B..N): the files no longer exist on our side — remove and
   continue:

```bash
git rm <files> 2>/dev/null; true
git rebase --continue
```

4. At Z: the deletion commit now has nothing to delete. Amend the message with
   `-m` to reflect the remaining changes (or drop the commit if it's empty):

```bash
git show --stat     # review what's left in the commit
git commit --amend -m "new message for remaining changes"
git rebase --continue
```

5. At break: verify the rebase is content-preserving:

```bash
git diff $(cat .rebase/ORIGINAL_HEAD)
```

6. If the diff is empty (as expected), finalize:

```bash
git rebase --continue
```

## Branch topology (split linear commits into a side branch)

Move a range of linear commits onto a side branch with a merge, using
`--rebase-merges`. Useful for organizing commits into a categorized topology.

Given a linear history where commits A..Z should be on a side branch (shown in
`git log` order, newest first):

```
* <later-commits>
* Z  last commit of the group (newest)
* ...
* A  first commit of the group (oldest)
* M  commit before the group (rebase base)
```

Note: in the rebase edit-todo, the order is reversed — A appears first (top) and
Z appears last (bottom).

### 1. Write the sed script

Insert `label`/`update-ref`/`reset`/`merge` commands around the commit range.
The todo format depends on user config — match both long and short commands.

```bash
cat > .rebase/edit.sed <<'EOF'
/^(pick|p) <first-sha>/{
i\
label bp-name
}
/^(pick|p) <last-sha>/{
a\
update-ref refs/heads/<branch-name>\
label <branch-label>\
reset bp-name\
merge <branch-label>
}
$a\
break
EOF
```

- `<first-sha>` — A, the oldest commit in the group (first in the edit-todo)
- `<last-sha>` — Z, the newest commit in the group (last in the edit-todo)
- `bp-name` — unique label for the branch point (e.g. `bp-map`)
- `branch-label` — label for the side branch tip (e.g. `stub-map`)
- `<branch-name>` — the actual branch ref to update (e.g. `stub/map`)

### 2. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="sed -i '' -E -f .rebase/edit.sed" git rebase -i --rebase-merges <base>^
```

### 3. Verify and finalize

At break, verify the merge has two parents and the diff is empty:

```bash
git cat-file -p <new-merge-sha> | head -5   # should show two parents
git diff $(cat .rebase/ORIGINAL_HEAD)        # should be empty
git rebase --continue
```

## Rules

- **Never switch branches.** Work on the current branch. If you think a branch
  switch is needed, ask the user first — target commits may be reachable from
  the current branch via merges.
- **Newest commit first.** When operating on multiple commits, process them in
  reverse chronological order (newest first). This keeps older SHAs intact until
  you touch them, avoiding unnecessary rewrites and minimizing merge conflicts.
- **Preserve merge topology.** Use `--rebase-merges` by default to keep existing
  merge commits. Only linearize if explicitly asked.
- **One operation per rebase** — except for rewords. Rewords don't change
  content, so batching them via exec lines is safe and avoids SHA-tracking
  complexity. For operations that change tree content (edit, drop, fixup),
  sequential rebases are simpler and more reliable.
- **Save ORIGINAL_HEAD** to `.rebase/` before starting. This is more reliable
  than `@{1}` which can give wrong results after multi-step rebases.
- **Always append `break`** as the last sequence editor line — this pauses
  before refs update, so you can verify and abort cheaply if something is wrong.
- **Always `git diff $(cat .rebase/ORIGINAL_HEAD)`** after each rebase to verify
  no content changed (unless the operation intentionally changes content, e.g.
  drop or purge).
- **Use `sed -E` with alternation** `(pick|p)` to match both short and long todo
  formats.
- **All temporary files go in `.rebase/`.** Sed scripts, saved state, everything.
  This keeps rebase artifacts together and ensures cleanup removes them all.
