---
name: resolve-merge-conflicts
description:
  Resolve merge conflicts in the working tree during an active merge, rebase, or
  cherry-pick. Triggers when git reports unmerged paths ("both modified",
  "deleted by us/them"), when conflict markers (<<<<<<<) appear in files, or
  when the user asks to resolve, abort, or inspect an in-progress merge.
  Distinct from inspect-merge-conflicts (that one is for historical merge
  commits).
allowed-tools: Bash, Read, Edit
---

# Resolve Merge Conflicts

Work through live conflicts in the working tree — files with `<<<<<<<` markers,
unmerged index entries, and paused merges/rebases/cherry-picks.

## 1. Orientation

Understand the current state before touching anything:

```bash
git status                                    # unmerged paths, in-progress operation
git diff --name-only --diff-filter=U          # just the conflicted filenames
git log --merge --left-right --oneline        # commits from each side that caused conflicts
```

`git status` shows which operation is in progress (merging, rebasing,
cherry-picking) and which files are unmerged. Start here every time.

## 2. Inspect the three stages

Git stores three versions of every conflicted file in the index:

| Stage | Meaning | Access             |
| ----- | ------- | ------------------ |
| 1     | Base    | `git show :1:file` |
| 2     | Ours    | `git show :2:file` |
| 3     | Theirs  | `git show :3:file` |

Read all three for each conflicted file before resolving:

```bash
git show :1:path/to/file    # common ancestor
git show :2:path/to/file    # our side
git show :3:path/to/file    # their side
```

Then look at what each side actually changed relative to the base:

```bash
git diff :1:file :2:file    # base → ours (what our side did)
git diff :1:file :3:file    # base → theirs (what their side did)
git diff :2:file :3:file    # ours vs theirs (direct comparison)
```

Most resolution mistakes come from skipping the base. The base tells you _why_
the conflict exists — which side added what, and what the two changes are
actually trying to accomplish.

## 3. Choose the right resolution strategy

### a. Hand-edit the conflict markers (default)

For any textual conflict where either side has real content worth thinking
about, open the file and edit the `<<<<<<<` / `=======` / `>>>>>>>` regions
directly.

To see the common ancestor between the markers (often clarifies intent):

```bash
git checkout --conflict=zdiff3 file   # rewrites markers to show base inline
```

This is safe — it updates marker style without losing index state.

After editing, every conflict marker must be removed before staging.

### b. `git resolve --ours` / `--theirs` / `--both` (take one side per conflict block)

Use when you want to take one side for every conflict block in a file without
discarding lines git already auto-merged cleanly elsewhere. This is the right
tool for "I want ours/theirs everywhere this file conflicted":

```bash
git resolve --ours file       # keep our side in every conflict hunk
git resolve --theirs file     # keep their side in every conflict hunk
git resolve --both file       # keep both sides, strip the markers
git resolve --ours            # resolve all unmerged files at once
git resolve --ours --add      # resolve + git add in one step
```

`git resolve` is a gut marketplace helper — just invoke it. If it fails (not on
PATH), fall back to hand-editing.

**`--both` with zdiff3:** `--both` only strips marker lines, so the
`||||||| base` section from zdiff3 style is left in the file. If you need
`--both` and are using zdiff3, switch marker style first:

```bash
git checkout --conflict=merge file
git resolve --both file
```

### c. `git checkout --ours` / `--theirs` (last resort — whole-file replacement)

```bash
git checkout --ours file && git add file
git checkout --theirs file && git add file
```

This replaces the **entire file** with one side — including lines git had
already auto-merged cleanly. Any changes the other branch made outside the
conflict regions are silently discarded.

Use only when you genuinely mean "take this side entirely": binary files where
merging is impossible, or an explicit "drop their version" decision. For textual
files with real content on both sides, prefer hand-editing or `git resolve`.

### d. Artifacts (generated or fetched files)

Some files in the repo are derived from something else: generated from local
source, or fetched/vendored by a local script. Recognize these before reaching
for any of the strategies above — the right place to resolve the conflict is the
_source_, not the artifact.

**Recognition cues:**

- _Generated text_: `DO NOT EDIT` header (often naming the generator), paths
  under `gen/` or `internal/gen/`, filenames like `foo.pb.go`, `foo_grpc.pb.go`,
  `schema.json`.
- _Generated or fetched binary_: protobuf descriptors, schema snapshots,
  compiled assets, vendored blobs pulled by a Makefile target, `npm`
  postinstall, or a fetch script in the repo.

Don't hand-edit an artifact to resolve a conflict. Artifacts are _products_ —
they should come out of the generator, not your editor. Best case, you redo the
same merge twice and the next regeneration overwrites your work. Worst case, you
resolve the source one way and the artifact another, and ship the drift as a
bug.

Resolve the source and re-derive:

1. Resolve the conflict in the _source_ (`.proto`, schema source, grammar, asset
   manifest, fetch script).
2. Regenerate or refetch with the project's build target:
   ```bash
   make -C proto generate    # or: mvn generate-sources, npm run generate,
                             #     bazel build //...:generated, etc.
   ```
3. Stage the result:
   ```bash
   git add -u
   ```

**Fallback — genuinely opaque content.** If a binary file is _not_ an artifact
(a real photograph, audio you authored in place, a font with no source), git
cannot merge it; pick one side:

```bash
git checkout --ours file && git add file
git checkout --theirs file && git add file
```

> Some projects mark generated/fetched artifacts as binary in `.gitattributes` —
> this forces whole-file resolution (no marker merging) and makes the derived
> nature explicit at the repo level.

### e. Special cases

**Delete/modify conflict** — one side deleted the file, the other modified it:

```bash
git add file    # keep the modified version
git rm file     # accept the deletion
```

**Submodule conflicts** — usually a disagreement about which commit to point to:

```bash
git diff          # shows the two commit SHAs
(cd submodule && git checkout <chosen-sha>)
git add submodule
```

## 4. Verify before staging

After resolving but before `git add`:

```bash
git diff AUTO_MERGE        # changes from the auto-merge attempt (ort strategy artifact)
git diff                   # working tree vs unresolved index
git diff --cached          # what's already staged
```

`AUTO_MERGE` is a ref the `ort` merge strategy writes to `.git/AUTO_MERGE` — it
captures git's auto-merge result before conflicts were introduced. Diffing
against it shows only what you changed during resolution, not the full conflict
noise.

Check that no stray conflict markers remain:

```bash
git diff --check
```

## 5. Stage and continue

Stage each resolved file:

```bash
git add path/to/file
```

Then continue the in-progress operation. Detect it from the git state:

```bash
# Merge in progress:
test -f .git/MERGE_HEAD && git merge --continue

# Rebase in progress:
test -f .git/REBASE_HEAD && git rebase --continue

# Cherry-pick in progress:
test -f .git/CHERRY_PICK_HEAD && git cherry-pick --continue
```

During a rebase, each commit is replayed individually — resolve, stage, and
`--continue` once per commit. Use `git rebase --skip` to drop a commit entirely.

## 6. Abort and restart

To abandon the in-progress operation entirely:

```bash
git merge --abort
git rebase --abort
git cherry-pick --abort
```

`--abort` returns the working tree and index to their pre-operation state.

To restart with an automatic strategy option:

```bash
git merge --abort
git merge -X theirs branch    # auto-resolve conflicting hunks in favor of theirs
git merge -X ours branch      # auto-resolve conflicting hunks in favor of ours
```

`-X ours`/`-X theirs` is a per-hunk strategy option — it only fires where both
sides conflict. Non-conflicting changes from both sides are still merged
normally. It is not a whole-file replacement.

## 7. One-time setup (suggest if not configured)

If `git config merge.conflictStyle` is not `zdiff3`, suggest enabling it:

```bash
git config --global merge.conflictStyle zdiff3
```

`zdiff3` inserts the common ancestor between the markers, making it obvious what
each side changed relative to the base.

If `git config rerere.enabled` is not `true`, suggest enabling it:

```bash
git config --global rerere.enabled true
```

With `rerere` enabled, git records how you resolve each unique conflict. If the
same conflict reappears (common during iterative rebases), git auto-applies your
previous resolution.

```bash
git rerere status       # files with recorded resolutions
git rerere diff         # what rerere would apply
git rerere forget file  # discard a bad resolution
```

## Quick reference

| Task                           | Command                                    |
| ------------------------------ | ------------------------------------------ |
| List conflicted files          | `git diff --name-only --diff-filter=U`     |
| Why did this conflict?         | `git log --merge --left-right --oneline`   |
| View base / ours / theirs      | `git show :1:file` / `:2:file` / `:3:file` |
| What our side changed          | `git diff :1:file :2:file`                 |
| What their side changed        | `git diff :1:file :3:file`                 |
| Show ancestor in markers       | `git checkout --conflict=zdiff3 file`      |
| Take ours per conflict block   | `git resolve --ours file`                  |
| Take theirs per conflict block | `git resolve --theirs file`                |
| Take ours (whole file)         | `git checkout --ours file && git add file` |
| Resolve artifact (gen'd/fetch) | Resolve source → regenerate → `git add -u` |
| Check resolution vs auto       | `git diff AUTO_MERGE`                      |
| Check for stray markers        | `git diff --check`                         |
| Continue merge / rebase / cp   | `git merge/rebase/cherry-pick --continue`  |
| Abort                          | `git merge/rebase/cherry-pick --abort`     |
| Rerere state                   | `git rerere status`                        |
| Forget bad rerere              | `git rerere forget file`                   |
| Restore conflict markers       | `git checkout --merge <file>`              |
