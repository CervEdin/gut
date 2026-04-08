---
description: Selectively stage changes into discrete commits. Use when multiple logical changes have accumulated across files and need to be committed separately. Replaces interactive `git add -p` with git plumbing (hash-object + update-index).
---

# Interactive Staging

Stage accumulated changes as discrete, logical commits — without interactive TUI tools.

## Approach

Uses the same technique as vim-fugitive: write desired content as a blob via `git hash-object -w`, then point the index at it via `git update-index --cacheinfo`. A helper script at `scripts/git-stage-partial` (relative to this skill) wraps this into a single atomic operation.

## Step 1: Analysis

Understand what has changed and group changes into logical commits.

1. Run `git status` and `git diff --stat` to see the overall picture
2. Run `git diff` to read the full diff
3. Read the changed files as needed to understand context
4. Group changes into logical commits — each commit should be a single coherent change (bug fix, feature, refactor, etc.)

## Step 2: Present Plan

Show the user the proposed commit grouping:

```
Proposed commits:
1. <summary> — files: <list>, partial: <list with description of which hunks>
2. <summary> — files: <list>
...
```

**Wait for user confirmation before staging anything.** The user may want to adjust the grouping.

## Step 3: Staging Loop

For each proposed commit, stage the relevant changes:

### Whole files

When all changes in a file belong to one commit:
```bash
git add -- <path>
```

### Partial files

When only some changes in a file belong to this commit:

1. **Once per file** (at the start of the session), save the current index version (the base) and a working copy:
   ```bash
   git show :0:<path> > .stage-base-<name>
   cp .stage-base-<name> .stage-<name>
   ```
   For new files not yet in the index, the base is empty (`/dev/null` or empty file).

2. Edit `.stage-<name>` to apply **only** the changes relevant to this commit.

3. Stage via the helper script:
   ```bash
   .claude/plugins/interactive-staging/scripts/git-stage-partial <path> .stage-<name>
   ```

4. For subsequent commits to the same file, just keep editing `.stage-<name>` — it already reflects all changes staged so far, so there's no need to re-extract from the index.

5. Keep `.stage-base-<name>` for the duration of the session — it allows reverting a stage:
   ```bash
   # To undo partial staging:
   .claude/plugins/interactive-staging/scripts/git-stage-partial <path> .stage-base-<name>
   ```

6. Clean up both temp files after the last commit for that file.

### Deleted files

For files that should be removed in this commit:
```bash
.claude/plugins/interactive-staging/scripts/git-stage-partial --remove <path>
```

### Verify

After staging all changes for a commit, show the user what's staged:

```bash
git diff --cached --stat
git diff --cached
```

Confirm the staged diff looks correct. If something is wrong, restage the base file to revert (see above) or `git reset HEAD -- <path>` to fully unstage.

### Commit

Hand off to the user. Do **not** commit automatically — the user may use `/commit`, `/peff-commit`, or their own preferred workflow. Simply inform them that the changes are staged and ready.

### Repeat

After the user commits, proceed to stage the next group. Run `git diff --stat` to confirm remaining changes match expectations before continuing.

## Edge Cases

- **New files (not in index):** The base is empty. Construct the intermediate version containing only the lines relevant to this commit. The helper script detects new files and assigns mode from filesystem permissions.
- **Deleted files:** Use `git-stage-partial --remove <path>` to record the deletion in the index.
- **Binary files:** Cannot be partially staged. Stage as whole files only (`git add`).
- **File mode changes:** The helper script preserves the existing index mode, or detects from filesystem for new files.
- **Renamed files:** Stage as deletion of old path + addition of new path (partial or whole as appropriate).
