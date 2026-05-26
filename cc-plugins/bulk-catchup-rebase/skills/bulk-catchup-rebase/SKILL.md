---
name: bulk-catchup-rebase
description: >
  Bulk-rebase a long-lived branch that trails upstream by many commits, using
  iterative merges through tagged releases (or other intermediate points) so
  `git rerere` captures each conflict resolution and replays it during the final
  rebase. Use this skill whenever the user mentions a stale or long-lived
  branch, a branch that is far behind main/master, hundreds of commits behind
  upstream, a rebase that produced too many conflicts to handle in one pass, or
  wants to break a big upstream catch-up into smaller chunks. Also applies to
  the pure-merge variant (skip the rebase, take one final merge commit). Do NOT
  use for short-range interactive rebases (reorder/squash/reword) — those belong
  to claude-rebase or git-rebase-i.
allowed-tools: Bash, Read, Edit, Write
---

# Bulk Catch-up Rebase

A two-pass strategy for rebasing a long-lived branch that has fallen far behind
upstream. A single `git rebase origin/HEAD` produces an unmanageable wall of
conflicts; this approach breaks the problem into bite-sized incremental merges
so `git rerere` captures each resolution, then replays them during a final
rebase pass.

## When to use this skill

Use this skill when the branch is far enough behind that a one-shot rebase is
unmanageable — tens to hundreds of upstream commits, possibly spanning months or
years. The tell is that resolving one pass produces a flood of conflicts with no
obvious thread connecting them.

Do NOT use for:

- **Short-range rebase** (reorder, squash, reword a handful of commits) → use
  `claude-rebase` or `git-rebase-i`
- **A single live conflict** you're already stopped at → use
  `resolve-merge-conflicts`
- **Topology cleanup** (duplicate commits, divergent parallel branches) → use
  `harmonize-branches`

## Why this works

Intermediate merge points keep each conflict set small and coherent — changes
from one release worth of upstream history rather than all of it at once.
`git rerere` caches every resolution by conflict fingerprint. The second pass
replays the branch commits one-by-one via `git rebase`, stopping at each
conflict point — but because rerere already has the answer, it auto-applies the
cached resolution and `git rebase --continue` glides through.

## Prerequisites

Rerere MUST be enabled. Verify once, then forget it:

```sh
git config rerere.enabled true    # or: git config --global rerere.enabled true
```

Without this, no resolutions are cached and every iteration re-conflicts from
scratch.

## Step 0: Test merge first

Before starting the iterative loop, get a quick read on what the conflict
landscape actually looks like:

```sh
git merge --no-commit --no-ff origin/HEAD
git merge --abort
```

This probe runs in seconds and shows you — without committing anything — every
file that would conflict if you merged today. Use it to judge scope: a handful
of files in familiar packages is manageable in one session; dozens of unrelated
files across generated code may warrant regenerating sources first. Run this
once, note what you see, then proceed to Step 1.

## Step 1: Iterative merge with rerere

For each suitable intermediate point on the upstream branch — tagged releases
work well — attempt a no-commit merge. Clean merges are discarded; conflicts
stop the loop so you can resolve them:

```sh
for v in $(git tag --sort=version:refname --list 'v*' --no-merged HEAD); do
  git merge --no-commit --no-ff "$v"
  if [ $? -eq 0 ]; then
    git merge --abort  # clean merge — discard and continue
  else
    echo "Conflict at $v — resolve, then commit"
    break
  fi
done
```

**Trust the loop.** The loop _is_ the optimization — do not sample every Nth
tag, skip iterations, or shortcut because the tag count "looks like a lot".
`git merge --no-commit --no-ff` is fast (247 tags ran in seconds); each
iteration either discards cleanly in milliseconds or stops at a real conflict.
Stop only when a conflict requires your attention; do not skip steps.

When the loop stops:

1. Resolve the conflicts (see `resolve-merge-conflicts` for per-conflict
   mechanics).
2. Stage and commit: `git add -u && git merge --continue`
3. Rerun the loop — rerere records the resolution, so the same conflict won't
   stop you again.

Repeat until the loop runs to completion with no conflicts. At that point every
conflict fingerprint is cached in `.git/rr-cache/`.

**Generated files.** If the conflict is in a generated file (`.pb.go`, paths
under `gen/`, a `DO NOT EDIT` header), resolve the _source_ file (`.proto`,
schema source, etc.) and regenerate — rerere still records the correct
index-level resolution and replays it on the next iteration.

## Choosing iteration points

Tagged releases are ideal when upstream tags regularly. If they don't:

- **Monthly commits** —
  `git log --after="2024-01-01" --before="2024-02-01" --format=%H origin/HEAD | tail -1`
  to find the last commit of each month
- **Release branches** — iterate over `origin/release/*` branch tips in
  chronological order
- **Merge commits** — `git log --merges --first-parent --format=%H origin/HEAD`
  for projects that merge feature branches into main

Smaller steps mean smaller conflict sets per iteration. The tradeoff is more
iterations. For a one-year gap, monthly or per-release granularity is usually
right.

## Step 2: Iterative rebase over the captured merges

Once Step 1 completes, convert the merge-commit history back to a linear rebase.
This iterative loop is **required** — do not skip straight to
`git rebase origin/HEAD`. A direct rebase against the remote tip defeats rerere
entirely: the cached resolutions from Step 1 were recorded at specific conflict
boundaries (one release worth of delta at a time), and a single-shot rebase
against the full upstream history presents conflicts at different boundaries
where the cached fingerprints do not match. The rerere cache will appear to do
nothing, and every conflict must be resolved by hand again.

The loop below replays your commits through the same incremental boundaries so
rerere's fingerprints fire at the right moments. Only after the loop completes
do you perform a final `git rebase --no-rebase-merges origin/HEAD` to land on
the current tip cleanly.

MUST be done against the same upstream state — fetch once before starting, then
don't fetch again until done.

**Capture the merge SHAs in oldest-first order:**

```sh
git log --merges --format=%H HEAD^2..HEAD | tac > /tmp/merges
```

**Reset to the first non-merge commit** (the original tip of your branch before
any of the Step 1 merges):

```sh
git reset --hard $(git log --no-merges --format=%H -1 HEAD^2..HEAD)
```

**Rebase onto each merge point in order:**

```sh
for sha in $(cat /tmp/merges); do
  git rebase --no-rebase-merges $sha^2 || git rebase --continue
done
```

`git rebase` will stop at each conflict even when rerere has fully resolved it —
this is expected. Running `git rebase --continue` moves forward; if rerere left
anything unresolved, `--continue` will tell you.

If `git rebase --continue` itself stops again, check `git status` and
`git rerere status`. If rerere has no pending resolutions and the index is
clean, the commit may have become empty — run `git rebase --skip` to drop it
(see Pitfalls below).

## Sanity checks

After the rebase completes, verify your commits survived intact:

```sh
git log --oneline origin/HEAD..HEAD
```

Commits whose diff becomes empty after rerere applies a resolution are
**silently dropped** by `git rebase`. This is often correct — upstream already
incorporated the same change — but verify intentionally, since a missing commit
isn't always obvious from the log.

**Use `git range-diff`, not `git diff @{1}`.** `git diff @{1}` is misleading
here: it shows the full delta from the pre-rebase tip, which is dominated by all
the upstream changes just incorporated, not by whether your commits survived.
Use `range-diff` instead:

```sh
git range-diff <old-base>..<old-tip> origin/HEAD..HEAD
```

Replace `<old-base>` and `<old-tip>` with your branch's base and tip _before_
the rebase — use `git reflog` to find them if needed.

## Variant: pure merge instead of rebase

If the goal is a single merge commit rather than a linear history, do Step 1
only. Once the loop completes with no conflicts, run:

```sh
git merge origin/HEAD
```

Rerere replays every cached resolution and the merge completes cleanly in one
shot. Useful for branches whose commit identity isn't worth preserving, or when
the project's workflow prefers merge commits.

## Pitfalls

- **Forgetting `rerere.enabled`** — no resolutions are cached; every iteration
  re-conflicts from scratch. Enable it before Step 1, not after.

- **Doing Step 2 against a moving target** — fetch once, then don't fetch again
  until both passes are done. If upstream moves between passes, the conflict
  fingerprints from Step 1 may not match the conflicts in Step 2.

- **Treating `git diff @{1}` as a sanity check** — it shows upstream delta, not
  commit survival. Use `git range-diff` as described above.

- **Silently-dropped empty commits** — verify with both
  `git log origin/HEAD..HEAD` (count) and `git range-diff` (content). A commit
  dropped because it became empty is often benign, but not always.

- **`git rebase --continue` stopping again after rerere** — check
  `git rerere status`. If the index is clean and rerere has nothing pending, the
  commit is truly empty; use `git rebase --skip` to drop it.

- **`CONFLICT (modify/delete)` is never cached by rerere** — rerere only caches
  three-way content conflicts. Add/remove conflicts (`CONFLICT (modify/delete)`)
  are structural: one side deleted a file the other modified. These require a
  manual decision every time they appear — `git rm <file>` to accept the
  deletion, or restore + edit to keep it. Do not wait for rerere to kick in; it
  won't.
