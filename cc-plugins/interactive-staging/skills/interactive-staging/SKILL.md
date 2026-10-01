---
description:
  Selectively stage changes into discrete commits. Use when multiple logical
  changes have accumulated across files and need to be committed separately.
  Replaces interactive `git add -p` with git plumbing (hash-object +
  update-index).
---

# Interactive Staging

Stage accumulated changes as discrete, logical commits — without interactive TUI
tools.

## Approach

Uses the same technique as vim-fugitive: write desired content as a blob via
`git hash-object -w`, then point the index at it via
`git update-index --cacheinfo`. A helper script at
`${CLAUDE_SKILL_DIR}/scripts/git-stage-partial` wraps this into a single atomic
operation.

## Split committed work

When the changes are already committed — the user asks to split the last commit,
or says part of it is its own commit — take them back out of the commit, then
continue at Step 1. The work tree does not change.

1. Record the commit, so its message and notes stay reachable:

   ```bash
   git rev-parse HEAD
   ```

   Call the printed sha `<orig>`. `git log -1 <orig>` shows the old message, and
   `git notes show <orig>` its notes.

2. Undo the commit, keeping its changes, and unstage them:

   ```bash
   git reset --soft HEAD~1    # or <base>, to split a squashed range
   git reset -N
   ```

   Use `-N`, not a bare `git reset`. A bare reset moves paths that don't exist
   in HEAD all the way to untracked. `-N` marks them as intent-to-add instead,
   so new files keep showing up in `git status` as `A` and in `git diff` with
   their content — they can't get lost among unrelated untracked files, and
   diff-based tooling still sees them.

   If the changes are staged but not committed, run only `git reset -N`.

3. Continue at Step 1. After the last group is committed, `git diff <orig> HEAD`
   prints nothing: together the new commits hold exactly the old change.

For a commit behind HEAD, git-rebase-i stops at that commit, and this section
applies there.

## Step 1: Analysis

Understand what has changed and group changes into logical commits.

1. Run `git status` and `git diff --stat` to see the overall picture
2. Run `git diff` to read the full diff
3. Read the changed files as needed to understand context
4. Group changes into logical commits — each commit should be a single coherent
   change (bug fix, feature, refactor, etc.)

## Step 2: Present Plan

Show the user the proposed commit grouping:

```
Proposed commits:
1. <summary> — files: <list>, partial: <list with description of which hunks>
2. <summary> — files: <list>
...
```

**Wait for user confirmation before staging anything.** The user may want to
adjust the grouping.

## Step 3: Staging Loop

For each proposed commit, stage the relevant changes:

### Whole files

When all changes in a file belong to one commit:

```bash
git add -- <path>
```

### Partial files

When only some changes in a file belong to this commit:

1. **Once per file** (at the start of the session), save the current index
   version (the base) and a working copy. Both go in a `stage` directory inside
   the git dir (one per worktree), never in the work tree:

   ```bash
   d=$(git rev-parse --path-format=absolute --git-path stage)
   mkdir -p "$d" && echo "$d"
   ${CLAUDE_SKILL_DIR}/scripts/git-stage-partial --base <path> > "$d/base-<name>"
   cp "$d/base-<name>" "$d/<name>"
   ```

   `--base` resolves `<path>` the same way as staging does: relative to the
   current directory, or absolute. For a new file that is not in the index yet,
   it prints nothing, so the base is empty.

   Shell variables do not carry over between commands. Where the steps below say
   `$d`, use the path that `echo` printed.

2. Edit `$d/<name>` to apply **only** the changes relevant to this commit.

3. Stage via the helper script:

   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/git-stage-partial <path> "$d/<name>"
   ```

4. For subsequent commits to the same file, just keep editing `$d/<name>` — it
   already reflects all changes staged so far, so there's no need to re-extract
   from the index.

5. Keep `$d/base-<name>` for the duration of the session — it allows reverting a
   stage:

   ```bash
   # To undo partial staging:
   ${CLAUDE_SKILL_DIR}/scripts/git-stage-partial <path> "$d/base-<name>"
   ```

6. After the last commit, remove the directory: `rm -r "$d"`.

### Deleted files

For files that should be removed in this commit:

```bash
${CLAUDE_SKILL_DIR}/scripts/git-stage-partial --remove <path>
```

### Verify

After staging all changes for a commit, show the user what's staged:

```bash
git diff --cached --stat
git diff --cached
```

Confirm the staged diff looks correct. If something is wrong, restage the base
file to revert (see above) or `git reset HEAD -- <path>` to fully unstage.

### Commit

Hand off to the user. Do **not** commit automatically — the user may use
`/commit`, `/peff-commit`, or their own preferred workflow. Simply inform them
that the changes are staged and ready.

### Repeat

After the user commits, proceed to stage the next group. Run `git diff --stat`
to confirm remaining changes match expectations before continuing.

## Edge Cases

- **New files (not in index):** The base is empty. Construct the intermediate
  version containing only the lines relevant to this commit. The helper script
  detects new files and assigns mode from filesystem permissions.
- **Deleted files:** Use `git-stage-partial --remove <path>` to record the
  deletion in the index.
- **Binary files:** Cannot be partially staged. Stage as whole files only
  (`git add`).
- **File mode changes:** The helper script preserves the existing index mode, or
  detects from filesystem for new files.
- **Renamed files:** Stage as deletion of old path + addition of new path
  (partial or whole as appropriate).
