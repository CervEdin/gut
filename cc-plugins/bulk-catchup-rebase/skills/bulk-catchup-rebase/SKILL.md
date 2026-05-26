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
upstream. A single `git rebase origin/master` produces an unmanageable wall of
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

When the loop stops:

1. Resolve the conflicts (see `resolve-merge-conflicts` for per-conflict
   mechanics).
2. Stage and commit: `git add -u && git merge --continue --no-edit`
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
  `git log --after="2024-01-01" --before="2024-02-01" --format=%H origin/master | tail -1`
  to find the last commit of each month
- **Release branches** — iterate over `origin/release/*` branch tips in
  chronological order
- **Merge commits** —
  `git log --merges --first-parent --format=%H origin/master` for projects that
  merge feature branches into main

Smaller steps mean smaller conflict sets per iteration. The tradeoff is more
iterations. For a one-year gap, monthly or per-release granularity is usually
right.

## Step 2: Iterative rebase over the captured merges

Once Step 1 completes, convert the merge-commit history back to a linear rebase.
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
git log --oneline origin/master..HEAD
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
git range-diff <old-base>..<old-tip> origin/master..HEAD
```

Replace `<old-base>` and `<old-tip>` with your branch's base and tip _before_
the rebase — use `git reflog` to find them if needed.

## Variant: pure merge instead of rebase

If the goal is a single merge commit rather than a linear history, do Step 1
only. Once the loop completes with no conflicts, run:

```sh
git merge origin/master
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
  `git log origin/master..HEAD` (count) and `git range-diff` (content). A commit
  dropped because it became empty is often benign, but not always.

- **`git rebase --continue` stopping again after rerere** — check
  `git rerere status`. If the index is clean and rerere has nothing pending, the
  commit is truly empty; use `git rebase --skip` to drop it.
