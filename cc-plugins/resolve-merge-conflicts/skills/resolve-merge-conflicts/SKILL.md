---
name: resolve-merge-conflicts
description:
  Resolve merge conflicts in the working tree during an active merge, rebase, or
  cherry-pick. Use this skill immediately whenever conflict markers (<<<<<<<)
  appear in files, git reports unmerged paths ("both modified", "deleted by
  us/them"), or any merge/rebase/cherry-pick is paused mid-flight — even if the
  user just pastes git status output without explicitly asking to "resolve
  conflicts." Distinct from inspect-merge-conflicts, which is for reviewing
  historical merge commits after the fact.
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
cherry-picking) and which files are unmerged. Start here every time. (If
`rerere.autoUpdate=true`, rerere stages its replay and the unmerged-path list
can be empty even though `MERGE_HEAD` is set — the in-progress operation, not
the empty list, is the signal there is work to resolve and audit.)

Determine the operation type next — it affects ours/theirs semantics and how the
summary is recorded:

```sh
if git rev-parse -q --verify MERGE_HEAD >/dev/null; then
  OP_TYPE=merge
elif git rev-parse -q --verify REBASE_HEAD >/dev/null; then
  OP_TYPE=replay
  REPLAY_HEAD=REBASE_HEAD
else
  OP_TYPE=replay
  REPLAY_HEAD=CHERRY_PICK_HEAD
fi
```

**Ours/theirs semantics:**

- **Merge**: ours = current branch (HEAD), theirs = incoming branch (MERGE_HEAD)
- **Replay** (rebase/cherry-pick): ours = upstream (the base you're rebasing
  onto), theirs = your commit being replayed

This distinction matters when deciding which side of a conflict to keep and when
explaining the resolution in the summary.

Set up the working directory for resolution artifacts (idempotent — safe to
re-run if the skill is interrupted and restarted):

```sh
: ${WORKDIR:=$(mktemp -d -t git-conflict-resolution)}
MERGED_BY=<model-identifier>   # e.g. claude-sonnet-4-6 — fill in the running model
```

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

### Inspect the incoming side as a commit

Stage 3 is a blob — the file content as the incoming side has it. But
`MERGE_HEAD` is a full commit and gives you something stage 3 cannot: author,
message, parents, neighboring files, and the history of the lines being changed.

```bash
git show MERGE_HEAD                                        # incoming commit message + author
git show MERGE_HEAD:path/to/file                           # file as the incoming side has it
git log -p MERGE_HEAD -- path/to/file                      # history of the file on the incoming side
git blame MERGE_HEAD -L <start>,<end> -- path/to/file      # which commit last touched these lines
```

Read the motivation of the incoming change, not just its diff. A commit message
often explains why a symbol was renamed or deleted and whether the branch-side
caller is still sensible — information that is invisible from the diff alone.

**During rebase or cherry-pick**, substitute the appropriate ref:

- `MERGE_HEAD` → `REBASE_HEAD` during a rebase
- `MERGE_HEAD` → `CHERRY_PICK_HEAD` during a cherry-pick

### Investigation order before touching code (CO/CT protocol)

Every conflict has two sides: **CO** (the commit that introduced our version of
the hunk) and **CT** (the commit that introduced their version — `REBASE_HEAD` /
`MERGE_HEAD` / `CHERRY_PICK_HEAD`). Before writing a single line of resolution,
run these three steps in order:

```bash
# 1. Read both commit messages first
git show -q <CO> <CT>

# 2. See what each side changed in the conflicting file
git show --stat <CO> <CT> -- <conflicting-path>

# 3. Diff the two versions of the file
git diff <CO> <CT> -- <conflicting-path>
```

Use `git log -1 HEAD -- <path>` or `git blame :2:<path>` to find CO.

A mechanical fix that makes the build pass can still be semantically wrong.
Reading the commit messages first reveals whether the incoming side hardcoded
behavior, deleted something intentionally, or renamed a concept — context that
is invisible from the diff alone and that determines whether your resolution
preserves the authors' intent.

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

### f. Conflict-free hunks that still break the build

Some merges produce a clean text result — no conflict markers, rerere fires
cleanly — but the resulting tree does not compile. The failure shape:

- Your side retains a caller of `Foo.bar()`
- The incoming side removed `Foo.bar()` in a **different file**
- Git auto-merges both sides (no textual overlap, no conflict markers)
- The tree compiles only if the caller is also updated or removed

This class of failure is not surfaced by conflict markers, `git diff --check`,
or rerere. **The build catches it; the build is what you should trust.**

As a sanity check before kicking off the build, `git grep -n <symbol>` can make
the failure mode visible:

```bash
git grep -n "Foo\.bar"   # find remaining callers of a potentially-removed symbol
```

But the check that matters is the build, not the grep.

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

When surfacing a resolution for user review, walk through hunks in the order
they appear in `git diff AUTO_MERGE` — not grouped by file type, component, or
importance. Diff order is the natural reading order the user can follow along
with.

**Run the project's build or typecheck before staging.** A clean text check does
not mean a clean build, and rerere caches whatever you commit — including a
broken resolution. Run this on the _unstaged_ working tree, before `git add`:

```bash
go build ./...             # Go
mvn -q -DskipTests compile # Java / Maven
npm run typecheck          # JS / TS
cargo check                # Rust
```

## 4.5. Document the resolution

Before staging, write a forensic record of what you did and why. This forces a
reasoned decision before committing and creates an audit trail for later.

```sh
git diff AUTO_MERGE > $WORKDIR/resolution.diff
```

Write `$WORKDIR/resolution-summary.md` covering each conflict region:

- No title header — the merge commit subject provides it
- Section headers are H2, filename + line range, setext style:
  ```
  ChargersSchedule.java, lines 50–88
  -----------------------------------
  ```
  Do not use `##` ATX headers — git strips lines starting with `##`
- Name commits inline in the prose; no separate CO/CT bullet lists
- For each conflict region, cover: which commit introduced our version and why;
  which commit introduced their version and why; what specific lines or method
  conflicted; what was kept and why — functional reasoning, not "it was ours"
- Reference commits by running `git show --pretty=reference <SHA>` and quoting
  the full output inline — e.g.
  `cb152f0370 (fixup! ~wip: add diagnostic logging, 2026-05-30)`. Do not drop
  bare SHAs without the subject and date.
- The reasoning should stand on its own — file paths are in the diff

**Rerere replays get the full treatment, not a free pass.** When rerere replayed
a cached resolution, the working tree came out clean without you deciding
anything — but the audit still requires all of the above, written _as if you had
resolved the hunk by hand_: read both sides and justify why the resolution is
correct. "rerere replayed it" is never an acceptable reason to accept a
resolution. On top of that reasoning, record provenance — note that rerere
replayed it and, where identifiable, which earlier resolution
(`git rerere status`, the `.git/rr-cache/` entry). Provenance is _additive_; it
never substitutes for the reasoning.

Then re-read the summary. Does the reasoning hold up? Would a future reader
understand the decision without looking at the diff first? If not, revise.

Format the summary before committing:

```sh
pandoc --wrap=auto --columns=72 --markdown-headings=setext -f gfm -t gfm \
  $WORKDIR/resolution-summary.md > $WORKDIR/resolution-summary-fmt.md
```

## 5. Stage and commit

Stage all resolved files:

```sh
git add -u
```

**For merge (`OP_TYPE=merge`):**

Build the commit message from the subject, formatted summary, and trailer:

```sh
sed '/^$/q' "$(git rev-parse --git-dir)/MERGE_MSG" > $WORKDIR/msg.txt
cat $WORKDIR/resolution-summary-fmt.md >> $WORKDIR/msg.txt
git commit -F $WORKDIR/msg.txt --trailer "merged-by: $MERGED_BY"
```

`sed '/^$/q'` extracts the subject line and its trailing blank line, stopping
before the auto-generated `# Conflicts:` block that `--no-edit` would include.
`--trailer` appends the trailer with the correct blank-line separator.

Add the diff as a note (summary is already in the commit message):

```sh
git notes --ref=claude-conflict-resolutions add -F $WORKDIR/resolution.diff
```

**For replay (`OP_TYPE=replay`):**

Review the original commit message to see if the resolution made it outdated:

```sh
git log -1 --format=%B $REPLAY_HEAD > $WORKDIR/original-message.txt
```

Ask: did the resolution rename a symbol mentioned in the message? Remove
described functionality? Change the approach significantly? If yes, edit
`$WORKDIR/original-message.txt` and commit with the updated message:

```sh
git commit -F $WORKDIR/original-message.txt
```

Otherwise commit with the original message unchanged:

```sh
git commit --no-edit
```

Add summary and diff together as a note:

```sh
git notes --ref=claude-conflict-resolutions add \
  -F $WORKDIR/resolution-summary.md \
  --separator='---' \
  -F $WORKDIR/resolution.diff
```

The caller (bulk-catchup-rebase or the user) is responsible for
`git rebase --continue` / `git cherry-pick --continue` after this skill
completes.

### Report what you resolved

End by surfacing a compact report — a few lines, not a retelling of the diff.
This is what a caller acts on, and the only thing that crosses the boundary when
this skill runs inside a delegated sub-agent:

- **Provenance** — per conflict, hand-resolved or rerere-replayed (and which
  cached resolution, where identifiable).
- **Build** — the verify command you ran and its result.
- **Anomalies** — anything unexpected: `CONFLICT (modify/delete)`, an unapproved
  path, a dirty or surprising state, a resolution you are not confident in.
- **Commit** — the SHA and subject you created.
- Or, if you could not resolve it cleanly: **blocked**, and why — never commit a
  guessed or build-breaking resolution just to clear the stop.

The report does not decide pacing; whether to pause for review is the caller's
call. Your job is to resolve, record the audit, and report honestly.

## 6. Start a file's resolution over

If your edits to a conflicted file went wrong, recreate the original conflicted
state — markers and all — and resolve it again:

```bash
git checkout --merge file     # re-create conflict markers for one file
git checkout --merge :/       # re-create them for every conflicted file
```

This is the same plumbing as the marker re-styling in §3a (`--conflict` implies
`--merge`); the intent here is different — discard a botched resolution rather
than preview the base. It honors your configured conflict style (zdiff3 if set),
and while the operation is still in progress it restores the markers even for
files you had already `git add`ed — a clean way to throw away resolution work
and start fresh. It does not touch the in-progress merge/rebase/cherry-pick
itself.

Aborting the operation entirely (`git merge --abort`, `git rebase --abort`,
`git cherry-pick --abort`) is the caller's responsibility, not this skill's —
the same division of labor as `--continue` in §5.

## 7. One-time setup and quick reference

See `references/quick-reference.md` for the command cheat sheet and one-time
setup recommendations (`zdiff3`, `rerere`). Suggest both if not already
configured when you first orient in a new repo.
