---
name: claude-rebase
description: Interactive rebase via patches — reorder, edit, squash, and reword commits without git rebase -i
argument-hint: [base-ref]
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
---

# Claude Rebase

An interactive rebase workflow that works without `git rebase -i`. Exports
commits as patches, then reapplies them in a user-specified order with optional
message rewrites — all driven conversationally.

## Arguments

- `$0` — the base ref (tag, commit, or branch) to reset to. All commits from
  this ref to HEAD will be reordered. **This IS a ref** — use it directly in
  `git log $0..HEAD` etc. Do NOT substitute `origin/master` or any other ref.
  Run `git rev-parse $0` once to confirm it resolves; if it doesn't, ask for
  clarification.

## Prerequisites

Before running this skill, the user should have:

1. A **plan file** describing the new commit order and any message corrections.
   Ask the user for this — it may be in conversation context, a file, or they
   may want to create one interactively.

## Workflow

### Phase 1: Preparation

0. Run `git rev-parse $0`. THIS is the base. NOT something else, like
   `origin/master`.

1. Handle uncommitted changes. Untracked files are fine — leave them alone. If
   there are modified or staged files, stash them using plumbing to get an
   atomic SHA:

   ```
   STASH_SHA=$(git stash create "claude-rebase: auto-stash")
   ```

   `git stash create` returns the SHA directly — no race condition. If the
   output is empty, there was nothing to stash.

   If `STASH_SHA` is non-empty, store it in the reflog so it survives GC, then
   clean the working tree:

   ```
   git stash store -m "claude-rebase: auto-stash" "$STASH_SHA"
   git reset --hard HEAD
   ```

   Keep `STASH_SHA` for the entire session. Always restore using the SHA
   directly (`git stash apply $STASH_SHA`), never by reflog position.

2. Save the current HEAD for later comparison. Run these as two separate
   commands — assigning and echoing in one command triggers an unnecessary
   permission prompt:

   ```
   ORIGINAL_HEAD=$(git rev-parse HEAD)
   ```

   ```
   echo ORIGINAL_HEAD=$ORIGINAL_HEAD
   ```

3. Save the name of the branch we are rebasing

   ```
   CLAUDE_REBASE_BRANCH=$(git branch --show-current)
   ```

   ```
   echo CLAUDE_REBASE_BRANCH=$CLAUDE_REBASE_BRANCH
   ```

4. List all commits to be reordered:

   ```
   git log --oneline <base-ref>..HEAD
   ```

5. Export patches (if not already exported):

   ```
   git format-patch <base-ref>..HEAD -o patches/ --no-stat --notes
   ```

   `--notes` includes any `git notes` content in the patch after the `---` line.
   Notes don't survive `git am` roundtrips (they're stripped on apply), but
   they're preserved in the patch files for reference. If notes must be restored
   after replay, re-add them manually with `git notes add`.

   If `patches/` already exists and contains the right number of patches, ask
   the user whether to re-export or reuse existing patches.

   **Notes recovery**: Notes are keyed by SHA and don't survive rebases. After
   replay, re-apply notes by parsing the `Notes:` section from patch files and
   matching commits by subject. When piping note content to git, use
   `/dev/stdin` (not `-`) as the file argument:

   ```
   echo "note content" | git notes add -F /dev/stdin <sha>
   ```

   Then **ask the user** before cleaning up orphaned notes from the old range:

   ```
   git rev-list <base-ref>..<old-HEAD> | while read h; do
     git notes remove "$h" 2>/dev/null
   done
   ```

6. If you the plan is to split the branch, start by moving the patches into
   subfolders, one for each branch

   ```
   mkdir patches/branch-name
   ```

   ```
   mv patches/NNNN-*.patch patches/branch-name/
   ```

7. Confirm the plan with the user before proceeding. Show the mapping from
   original order to new order.

### Phase 2a: Apply patches in new linear order

1. Reset to the base ref:

   ```
   git reset --hard <base-ref>
   ```

2. Apply each patch in the order specified by the plan:

   ```
   git am -3 patches/NNNN-*.patch
   ```

3. For patches that require a message correction (per the plan), **edit the
   `Subject:` line directly in the patch file before applying** — this is
   simpler and faster than apply-then-amend:

   ```
   sed -i '' 's/^Subject: \[PATCH NN\/MM\] old subject/Subject: [PATCH NN\/MM] new subject/' patches/NNNN-*.patch
   ```

   Or use the Edit tool on the patch file. Then apply normally with `git am`.

   If the body also needs changes, edit the body in the patch file too (the
   message body follows the Subject line, separated by a blank line).

   Fallback: if editing the patch is impractical, apply first then amend:

   ```
   git commit --amend -m "$(cat <<'EOF'
   corrected message here
   EOF
   )"
   ```

### Phase 2b: Apply patches with merges

1. Reset to the base ref:
   ```
   git reset --hard <base-ref>
   ```
2. Do the steps in Phase 2a
3. Switch back to the branch we are rebasing
   ```
   git switch $CLAUDE_REBASE_BRANCH
   ```
4. Merge the branch we just created
   ```
   git merge --no-ff branch-name
   ```

### Phase 2c: Squash commits into earlier ancestors

When the plan calls for squashing small commits into earlier targets (e.g.
folding a 1-line follow-up into the feature commit that should have included
it), **do NOT reorder the patches manually**. Moving a patch earlier causes
context mismatches when intermediate commits modify the same files — even
`git am -3` struggles because the 3-way merge base comes from a much later state
(after all the intermediate patches), making the base-vs-ours diff enormous and
unrelated to the actual change.

Instead, apply patches in original order and mark squash sources with git
plumbing:

1. **Reset and apply all patches in original order** as in Phase 2a. When you
   reach a squash-source patch, apply it then immediately re-commit it as a
   squash marker:

   ```
   git am -3 patches/NNNN-squash-source.patch
   git reset --soft HEAD~1
   git commit --squash=<target-sha> -C ORIG_HEAD
   ```

   - `git reset --soft HEAD~1` undoes the commit but keeps changes staged.
     `ORIG_HEAD` is set to the commit that was just removed.
   - `--squash=<target-sha>` sets the subject to `squash! <target subject>` (git
     reads the target's subject from the object store — no manual matching, no !
     escaping issues).
   - `-C ORIG_HEAD` reuses the original commit's message body and authorship
     without opening an editor.

   For non-squash patches, apply normally with `git am -3`.

2. **Verify tree matches** before autosquash (safety check):

   ```
   git diff $ORIGINAL_HEAD
   ```

3. **Run autosquash** to fold the marked commits into their targets:

   ```
   GIT_SEQUENCE_EDITOR=cat git rebase --autosquash <base-ref>
   ```

4. **`squash` vs `fixup`**: Use `--squash` to concatenate all commit messages
   into the target. Use `--fixup` to discard the folded commit's message. Ask
   the user which they prefer if not specified.

**Notes recovery caveat**: Squashed-away commits no longer exist as separate
commits. Skip them when restoring notes — match only the surviving commits by
subject.

### Phase 3: Handle failures

If `git am -3` fails for a patch:

1. **Do NOT force it through.** Run `git am --abort`.

2. Diagnose which file(s) have mismatched context.

3. Choose a strategy:

   **Strategy A — Reorder**: If the conflict indicates a missed dependency, fix
   the ordering and `git reset --hard <base-ref>` to start over.

   **Strategy B — Split the patch**: If a patch mixes independent concerns, use
   `git am --include/--exclude` to apply it as two separate commits:

   ```
   git am -3 --include='path/to/part-a/*' patches/NNNN-*.patch
   git commit --amend -m "$(cat <<'EOF'
   subject for part A
   EOF
   )"
   git am -3 --exclude='path/to/part-a/*' patches/NNNN-*.patch
   git commit --amend -m "$(cat <<'EOF'
   subject for part B
   EOF
   )"
   ```

   The `--include`/`--exclude` flags filter which files the patch touches. Apply
   complementary filters to get clean splits. Always amend the subject after
   each half so both commits have accurate descriptions.

4. **Always ask the user** before choosing a recovery strategy.

### Phase 3b: Fix small mistakes with fixup + autosquash

If verification (Phase 4) reveals a non-empty diff, don't re-export and replay
all patches. Instead:

1. Fix the file(s) and find which commit to target using `git blame`. Look at
   the region around the problem, not just the exact line — blank lines and
   whitespace are commonly attributed to unrelated commits, so check neighboring
   content lines to identify which commit owns that section:

   ```
   git blame -L <start>,<end> <file>
   ```

2. Create a fixup commit targeting the SHA from blame. **Always use
   `--fixup=<SHA>`** — never manually write `-m "fixup! ..."` because the Bash
   tool escapes ! to \\!, producing a malformed subject:

   ```
   git add <file>
   git commit --fixup=<SHA-from-blame>
   ```

3. Autosquash it in:

   ```
   GIT_SEQUENCE_EDITOR=cat git rebase --autosquash <base-ref>
   ```

   `cat` works as a no-op sequence editor because it reads the todo file and
   exits 0 without modifying it. **`:` and `true` do NOT work** — they ignore
   the file argument entirely and produce an empty todo.

4. **Cascading conflicts from file-deleting fixups**: When a fixup removes files
   that were modified by later commits, autosquash causes modify/delete
   conflicts on every subsequent commit that touched those files. Resolve each
   by running `git rm <files>` then `git rebase --continue`. This is expected
   and mechanical — just keep deleting and continuing.

### Phase 4: Verification

After all patches are applied, run these checks:

1. **Commit count**: `git log --oneline <base-ref>..HEAD` — verify expected
   number of commits.
2. **Tree diff**: `git diff $ORIGINAL_HEAD` — show the result to the user. A
   pure reorder should produce an empty diff. If the rebase intentionally
   modified, squashed, or dropped commits, a diff is expected — confirm with the
   user that it looks correct.
3. **Formatting**: Run the project's formatter (if any) and check
   `git diff --quiet`. If the formatter produces changes, amend the relevant
   commit.
4. **Build**: Run the project's build/compile command to verify it still builds.
5. **Clean up patches**: Remove the exported patch files:
   ```
   rm patches/*.patch
   ```
6. **Restore stash**: If `STASH_SHA` was set, restore the stashed changes:
   ```
   git stash apply $STASH_SHA
   ```

## Important rules

- **NEVER use `git add -A`** — use `git add -u` or explicit pathspecs.
- **NEVER use `git -C`** when already inside the repo.
- **Use heredocs** for all commit messages to preserve formatting.
- **Save ORIGINAL_HEAD** before reset so you can always compare or recover.
- **Ask before destructive actions** — the `git reset --hard` is the only
  expected destructive operation, and it happens once at the start.
