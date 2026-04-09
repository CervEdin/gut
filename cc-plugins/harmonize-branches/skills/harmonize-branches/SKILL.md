---
name: harmonize-branches
description: Analyze branch topology, consolidate divergent branches, and resolve conflicts encountered along the way
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
---

# Branch Topology Analysis and Harmonization

A workflow for reducing topological complexity in branch histories — finding
duplicates, consolidating divergent branches, and resolving conflicts when they
arise during the process.

## Three modes of operation

1. **Analyze** — scan the topology for duplicates, divergent branches, and conflicts
2. **Consolidate** — restructure branches to harmonize parallel histories
3. **Resolve** — fix conflicts encountered during a rebase

## Phase 1: Analyze topology

Run `find-conflicts.py` (in the repo root) to identify all merges in the
topology that would produce conflicts:

```
python3 find-conflicts.py [ref]
```

Default ref is HEAD. This reports each conflicting merge, its base/p1/p2, the
conflicting files, and what each side uniquely changes.

## Phase 2: Consolidate branches

Analyze the topology and restructure it to eliminate divergence and conflicts.
Run `find-conflicts.py` after each iteration.

### Strategy: make parallel branches identical

When two parallel branches independently make the same change, their merge
conflicts even though the result is identical. The fix is to make the branches
carry the same commits.

**Rules:**
1. **Start with later history** — changes later in the topology cascade less
   when modified
2. **Make branches identical first** — before hoisting changes to common
   ancestors
3. **Never drop a duplicate** without ensuring the change exists on the other
   branch — dropping one copy means the change is missing on that branch,
   causing more conflicts

### Common patterns

**Identical duplicate commits on parallel branches:**
Find them with pygit2 — same subject, same diff, different commit objects.
If both branches have the same commit, merges between them resolve cleanly.
If only one has it, cherry-pick it onto the other.

**Modify/delete conflicts:**
One side modifies a file, the other deletes it. Usually caused by a commit
that bulk-deletes files existing on a branch that doesn't need them. Fix by
dropping the delete commit from that branch.

**Divergent duplicates:**
Same subject but different diffs — usually because one copy includes unrelated
formatting changes. Split the formatting out so the logical change becomes
identical on both branches, then one copy can be consolidated.

**Commit only on one branch that conflicts with the other:**
A commit modifies a line that the other branch also modifies or deletes. Either:
- Add it to both branches (if both need it)
- Drop it (if the other branch's change makes it redundant)

## Phase 3: Resolve a conflict

When stopped at a conflict during rebase, follow this process **exactly**.
Mistakes here cascade — a wrong resolution changes the file state going forward,
breaks rerere fingerprints for downstream conflicts, and the bad resolution gets
cached.

### Step 1: Understand the conflict

```
git status --short
git diff                          # show conflict markers
git rev-parse REBASE_HEAD         # the original merge being replayed
git rev-parse MERGE_HEAD          # the branch being merged in (if merge)
```

Key refs:
- **REBASE_HEAD** — the original merge commit being replayed; this is a
  reference point for what the result should look like (topology may differ)
- **MERGE_HEAD** — one of the inputs to the new merge (the branch side)
- **HEAD** — the other input (the mainline side)

### Step 2: Check the original resolution

```
git show REBASE_HEAD:<file>
```

This shows how the original merge resolved the file. This is the target state,
**adjusted for topology differences** (see Step 3).

### Step 3: Consider topology differences

The rebase may have reordered commits. Changes that came after this merge in the
original history may now come before it. Check:

- Does HEAD already contain changes that weren't in the original p1?
- Has a commit been moved earlier in the topology (e.g. a whitespace commit)?
- If so, the original REBASE_HEAD resolution isn't a perfect match — you need
  to keep the changes that are already in HEAD while applying only what this
  merge is supposed to bring in.

Check the final ref (the branch being rebased) to understand the final intended
state:

```
git show <final-ref>:<file>
```

### Step 4: Resolve individual hunks

**NEVER checkout an entire file from MERGE_HEAD.** This replaces the whole file
and may drop changes from HEAD that should be preserved, causing cascading
failures.

Instead, resolve each conflict hunk individually:
- For each `<<<<<<<`/`=======`/`>>>>>>>` block, decide which side to take
  based on the original resolution and topology context
- Use the Edit tool to replace each conflict block

### Step 5: Verify

After staging the resolution, sanity check against REBASE_HEAD:

```
git add <file>
git diff REBASE_HEAD:<file> :<file>
```

This should be empty — unless topology changes justify a known difference
(e.g. a whitespace commit was reordered). If there's a difference, understand
exactly why before proceeding.

### Step 6: Handle rerere

If rerere applied a **wrong** cached resolution:

```
git rerere forget <file>
```

Then resolve correctly and re-record:

```
git add <file>
git rerere
```

### Rerere limitations

Rerere only handles **content conflicts** (conflicting hunks with conflict
markers). It cannot learn resolutions for:
- **Modify/delete conflicts** — one side modified, other side deleted
- These must be resolved manually every time, or the topology must be fixed
  to eliminate them

## Important rules

- **NEVER use `git checkout MERGE_HEAD -- <file>`** to resolve conflicts. This
  replaces the entire file and drops HEAD-side changes.
- **Always sanity check against REBASE_HEAD** after resolving — it's a reference
  point, not ground truth (topology may differ).
- **Always check the final ref (the branch being rebased)** when topology
  differences make the original resolution ambiguous.
- **Be meticulous.** Time spent verifying saves time not redoing rebases.
- **NEVER use `git -C`** when already inside the repo.
