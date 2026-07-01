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
allowed-tools: Bash, Read, Edit, Write, Agent
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

### Conflict style: zdiff3 (recommended)

`zdiff3` produces richer conflict markers that include the common ancestor's
version of each hunk alongside both sides, giving more context when resolving.
It is noticeably easier to interpret than the default `merge` style — especially
for LLM-assisted resolution.

Set it **per-command** with `git -c` so no config file is touched:

```sh
git -c merge.conflictstyle=zdiff3 merge  ...
git -c merge.conflictstyle=zdiff3 rebase ...
```

All merge and rebase commands in the steps below are written with this prefix.
If you prefer to skip it for a particular run, just drop the `-c` argument — the
skill works without it.

## Step 0: Test merge first

Before starting the iterative loop, get a quick read on what the conflict
landscape actually looks like:

```sh
git -c merge.conflictstyle=zdiff3 merge --no-commit --no-ff origin/HEAD
git merge --abort
```

This probe runs in seconds and shows you — without committing anything — every
file that would conflict if you merged today. Use it to judge scope: a handful
of files in familiar packages is manageable in one session; dozens of unrelated
files across generated code may warrant regenerating sources first. Run this
once, note what you see, then proceed to Step 1.

**Verify the branch's own build is clean before starting the loop.** If the
branch is already broken at HEAD, no compile gate during the iterative loop is
trustworthy — you cannot tell whether a new build break comes from a merge or
was pre-existing. Ideally every commit on the branch is bisectable, but that is
not a hard requirement here — what _is_ required is a clean build at the branch
tip before the loop starts.

## Step 1: Iterative merge with rerere

For each suitable intermediate point on the upstream branch — tagged releases
work well — attempt a no-commit merge. Clean merges are discarded; conflicts
stop the loop so you can resolve them:

```sh
for v in $(git tag --sort=version:refname --list 'v*' --no-merged HEAD --merged origin/HEAD); do
  if git -c merge.conflictstyle=zdiff3 merge --no-commit --no-ff "$v"; then
    git merge --abort                                       # clean: exit 0 — discard, keep walking
  elif ! git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    echo "Merge of $v failed for a non-conflict reason — stop and investigate"; break
  elif ! git diff --check >/dev/null 2>&1; then
    echo "Conflict at $v — manual resolution needed"; break
  else
    echo "Conflict at $v — rerere resolved fully; verify, then commit"; break
  fi
done
```

The loop classifies each stop so later steps don't rediscover it — and so a
rerere replay can't masquerade as a clean merge. Exit 0 is a **clean** merge
(discarded). A nonzero exit with no `MERGE_HEAD` is a **hard failure** (bad ref,
dirty tree, unrelated histories) — stop and investigate, don't treat it as a
conflict. A nonzero exit with `MERGE_HEAD` set is a real conflict stop, split by
whether leftover markers remain (`git diff --check`): **manual** if they do,
**rerere-resolved** if rerere replayed a cached resolution and the tree came out
clean. Manual and rerere-resolved are handled _identically_ below — the split is
carried forward only to frame the resolution and the pacing, never to skip the
audit.

Rerere caching is half of why the loop exists. The other half is **bisection**:
each intermediate point localizes one cluster of conflicts to one small upstream
stride. Semantic breaks — deleted APIs, removed infrastructure, renamed types —
surface against a narrow surrounding context instead of all at once. Skipping
the loop because rerere "wouldn't fire on these conflicts anyway" gives up the
bisection benefit too, which is often the more valuable half.

**Default: trust the loop.** Do not preemptively sample every Nth tag, skip
iterations, or shortcut because the tag count looks like a lot. Clean iterations
only add ~50–100ms of delay each — they aren't the cost to optimize.

**The real goal is decomposing conflicts.** Fine strides keep each conflict set
small and coherent — one intermediate point's worth of upstream changes at a
time. The thing to avoid is _compounded conflicts_: if merging A would conflict
and merging B (after A) would also conflict, you almost always want to resolve A
first and B second, not bundle them into one stop. The intermediate state after
A often makes B's resolution obvious in a way it wouldn't be if you faced both
at once.

**Adjust to larger strides when conflicts repeat without value.** Some conflict
shapes recur at every iteration but rerere never replays them — typically a
segment of a file that gets bumped at every release (a version number, a build
counter). The conflict structure is identical but the bumped value is different
each time, so each iteration is a fresh rerere fingerprint. Walking the log to
find the exact commits worth resolving is more work than just jumping further
out and letting one resolution cover the stretch — that's the cheap, good-enough
heuristic.

Strides aren't a one-way ratchet. If a larger stride bundles together unrelated
compounded conflicts, drop back to finer granularity for that segment. You can
flip between strides mid-run; the right stride is the one that keeps conflicts
decomposable while not making you re-resolve the same trivially-repeating
pattern over and over.

When the loop stops, it has already classified the stop as **manual** or
**rerere-resolved** (or broken out for a clean merge / hard failure). Both
conflict cases are handled the same way here. A rerere replay is still a
conflict stop — the cached resolution being textually clean is _precisely_ when
the audit matters, because something was applied silently and nothing else
records what or why.

1. **Delegate the resolution to a sub-agent running `resolve-merge-conflicts`.**
   Spawn a general-purpose sub-agent (a default sub-agent shares this working
   tree, so it sees the in-progress merge and its commit lands here) and tell it
   to use the `resolve-merge-conflicts` skill to handle the stop end-to-end:
   read both sides, resolve it — or, for a rerere replay, verify and justify the
   replayed resolution _as if it had made it by hand_, never "rerere said so" —
   build-verify on the unstaged tree, write the summary, stage, commit, and
   record the git note. Delegating keeps the heavy diff-reading out of this
   loop's context; the sub-agent returns a compact report instead of flooding
   the orchestration layer.

   How it commits and where it records the note belong to the
   resolve-merge-conflicts skill, not here. Pass the sub-agent inputs and
   intent, not a commit procedure: do **not** script the commit or pin a notes
   ref in the dispatch. A dispatched procedure silently overrides the resolver's
   own — which is exactly how a stale convention slips back in, replacing the
   commit and audit the resolver would have made with whatever the dispatch
   happened to dictate.

   Pass it the operation type (`merge`), the conflicted paths, and the loop's
   classification. Require it to report back — provenance (hand-resolved vs.
   rerere-replayed, and which cached resolution if identifiable), the build
   result, anything unexpected (`CONFLICT (modify/delete)`, an unapproved path,
   a surprising state), and the commit it created — or that it is **blocked**
   and why.

   The sub-agent's commit concludes the merge. **Do not** run `git add` or
   `git merge --continue` yourself afterward: `MERGE_HEAD` is already gone, so a
   manual `git merge --continue` dies with "no merge in progress." (Verify still
   precedes stage, for the reason it always has — rerere caches whatever gets
   committed, so a broken resolution must never reach the cache. The sub-agent
   does this; you don't repeat it.)

2. **Decide whether to pause — this loop owns pacing; the resolver does not.**
   The audit trail already exists (step 1 committed it); this is only the
   question of whether to keep walking autonomously or hand back for review,
   read off the sub-agent's report:
   - **Trivial** — rerere-resolved, build passed, report clean: show a one-line
     summary and continue without waiting.
   - **Non-trivial** — manual resolution, build trouble, a flagged anomaly, or a
     **blocked** sub-agent: stop and surface the report and the committed
     resolution (`git show`, or the git note) for explicit approval. A committed
     resolution is fully reversible — reset it if you reject it.

   **In-session pauses are binding regardless.** If the user told you to stop,
   stop and surface state — a green build and a clean rerere replay are not
   approval to continue. The loop has the strongest "barrel through" momentum,
   which is exactly where a pause instruction is most easily overridden by
   accident.

3. **Rerun the loop.** The tag you just merged is now an ancestor of HEAD, so
   the `--no-merged HEAD` filter excludes it and the walk advances to the next
   conflict — that, not rerere, is why this conflict won't stop you again, and
   rerere's payoff comes in Step 2's replay: frequent manual stops (and a
   near-empty cache) during this first pass are the expected working state, not
   a fault.

Repeat until the loop runs to completion with no conflicts. At that point rerere
should have a recorded resolution for every conflict, ready to replay in Step 2.

**Generated files** are resolved at their source, not the artifact — the
`resolve-merge-conflicts` skill handles that (its artifacts section). One
bulk-loop caveat to pass along to the sub-agent: after regenerating, stage
**all** output with `git add -u`, never `git add <specific-file>` — a generator
often emits several files, and leaving siblings unstaged trips the next
iteration.

## Lock contention is normal in the loop

When running merge/rebase commands in a tight loop, you may occasionally hit
`fatal: Unable to create '.git/index.lock': File exists.` or "Another git
process seems to be running." This is **normal** in this skill — a previous
iteration's git process is still finishing up when the next one starts.

**Wait.** Do not remove `.git/index.lock`. Not under any circumstances. The lock
means git has exclusive control of the index; removing it while a git process is
live corrupts the index. There is no safe "first check if a process is running"
heuristic — the risk is catastrophic and the correct action is always the same:
wait. If unsure whether a process is still running, wait longer. Do not reason
about whether removing it is safe. Re-run the failing command after the lock
clears.

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
git log --merges --format=%H $(git log --no-merges --format=%H -1 origin/HEAD..HEAD)..HEAD | tac > /tmp/merges
```

**Reset to the first non-merge commit** (the original tip of your branch before
any of the Step 1 merges):

```sh
git reset --hard $(git log --no-merges --format=%H -1 HEAD^2..HEAD)
```

**Rebase onto each merge point in order:**

```sh
for sha in $(cat /tmp/merges); do
  git -c merge.conflictstyle=zdiff3 rebase --no-rebase-merges $sha^2 || git rebase --continue
done
```

`git rebase` will stop at each conflict even when rerere has fully resolved it —
this is expected, and it is still a conflict stop to be audited, not skipped.
**Delegate it to a sub-agent running `resolve-merge-conflicts`, exactly as in
Step 1**: pass the operation type (`rebase`), the conflicted paths, and the
loop's manual/rerere-resolved classification, and require the same report back.
The sub-agent reads both sides — for a replay it verifies and justifies the
resolution rather than trusting it, because rerere matches on text fingerprints
and a clean text resolution can still reference a symbol the surrounding
upstream delta removed in a different file (only the build catches that) —
build-verifies on the unstaged tree, writes the audit, and commits the replayed
commit.

Unlike a merge, the sub-agent's commit does **not** conclude the operation —
this loop owns the continue. After the sub-agent returns and you have applied
the same pacing decision as Step 1, advance:

```sh
git rebase --continue
```

`git rebase --continue` moves forward; if rerere left anything unresolved,
`--continue` will tell you.

If `git rebase --continue` itself stops again, check `git status` and
`git rerere status`. If rerere has no pending resolutions and the index is
clean, the commit may have become empty — run `git rebase --skip` to drop it
(see Pitfalls below). To confirm what a replay actually applied, ask rerere's
porcelain (`git rerere diff`, `remaining`) rather than inspecting the cache
directory; if you do need the directory, `git rev-parse --git-path rr-cache`
locates it (not `.git/rr-cache`). See `references/rerere-cheatsheet.md`.

### When the branch has meaningful internal merge topology

This skill prescribes `--no-rebase-merges` throughout Step 2. That is the right
shape for a branch with a linear commit history. If your branch's internal merge
topology is meaningful — sub-branches whose merge commits you need to preserve —
the `$sha^2` loop above is not the right shape.

There is a sketch of a working approach: start Step 2 by running
`git reset --hard` back to the original branch tip (before any of the Step 1
merges), then rebase with `--rebase-merges --update-refs` instead of the loop.
This approach has not been fully written up here yet and needs more lived
experience before it belongs in a skill.

**Surface the topology question before starting Step 2.** If your branch has
sub-branch merges you intend to keep, stop and ask the user how they want to
proceed rather than silently picking a loop shape that doesn't fit.

## Step 3: triage before rebasing

Before starting Step 2, run:

```sh
git diff origin/HEAD --stat
git log --no-merges --oneline origin/HEAD..HEAD | wc -l
git log --no-merges --oneline origin/HEAD..HEAD | head -10
git log --merges --oneline origin/HEAD..HEAD | grep -v "Merge tag" | head -5
```

The diff stat shows what a rebase would produce. The log commands give a cheap
read on the payload: how many commits need rebasing, what they look like, and
whether the branch has internal sub-branch merges worth knowing about. Use
`wc -l` + `head` — never dump the full log into context.

Use this to decide what to do next:

- **Empty diff:** the branch contains nothing not already on upstream. The
  rebase is a no-op. Stop. Ask the user whether to delete the branch before
  doing anything else — this is the user's decision, not yours.

- **Non-empty diff:** review each file. For each change, ask: is this still
  relevant? Was it subsumed by another branch? Is it accidental (whitespace,
  generated output)? Is it aligned with the branch's stated purpose? Only
  proceed to Step 2 once the triage confirms there is something worth rebasing.

_"Not really rebasing"_ — extracting a few keepers, abandoning the original
branch, splitting work — is an acceptable outcome. But it is the user's call,
not yours. Surface the triage result and ask.

### When the branch is a mix of keepers and drops

For a catch-all branch where some changes are worth keeping and others aren't,
do not try to construct a `git rebase --onto` invocation that drops the unwanted
commits.

1. **Rebase first.** Try the standard rebase:

   ```sh
   git rebase --onto origin/HEAD \
     $(git log --format=%H --no-merges --ancestry-path origin/HEAD..HEAD | tail -1)~
   ```

   The `~` makes the oldest non-merge commit's _parent_ the upstream so the
   commit itself is replayed.

2. **Fresh-commit fallback if rebase dropped keepers.** `git rebase` replays
   _diffs_, not tree states. A cleanup commit whose diff is entirely reverts
   relative to the new base becomes empty and is silently dropped — even if its
   tree contained keepers via merge-chain inheritance. If that happens, reset to
   upstream and re-stage only the keepers from the branch tip:

   ```sh
   git checkout origin/HEAD -- .         # all tracked files match upstream
   git checkout <branch-tip> -- path/to/keeper.json
   git commit -m "..."
   ```

   The diff IS the keepers — nothing can be dropped as empty.

If keepers are unrelated to the branch's stated purpose, put them on their own
focused branch rather than bundling with the feature work.

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
git -c merge.conflictstyle=zdiff3 merge origin/HEAD
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

- **Letting the cache expire between passes** — `git gc` prunes recorded
  resolutions (`gc.rerereResolved`, 60 days by default; unresolved entries at
  15), so a long gap between Step 1 and Step 2 can empty the cache and make Step
  2 re-conflict everywhere as if rerere never ran. Run the two passes close
  together; if a Step 2 that should replay is instead stopping manually
  throughout, redo the relevant Step 1 merges to re-record before rebasing.

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

- **A corrupted stage must be redone, not patched forward.** If a stage in Step
  1 went wrong — wrong files staged, wrong resolution applied, dirty tree
  carried into the loop — reset to the last clean checkpoint (`git log` →
  `git reset --hard <sha>`) and redo that stage properly. Do not try to fix the
  broken state in place; patching forward compounds the error and makes the
  history unreadable.

  **Rerere caveat.** If the bad resolution was learned by rerere, plain redo
  will let rerere re-apply the wrong fix. Two options before redoing:
  - `git rerere forget <pathspec>` while still in the conflicted state to drop
    the cached resolution for the files involved, then redo normally; or
  - `git -c rerere.enabled=false merge ...` for the redo iteration, which
    bypasses rerere for that one command (there is no `--no-rerere` flag).

## When stuck, escalate to the user

Mistakes during a long-lived rebase are expensive: they corrupt intermediate
state, leave the working tree in confusing partial-resolve conditions, and
compound silently if you push through. The user has better context on the
branch's purpose and a faster intuition for what "looks wrong" — escalate sooner
than you would for ordinary tasks.

When the state is unclear, stop and orient first:

```sh
git status
git log --oneline -5
git diff
```

If after orientation an approach is not converging — same error recurring,
command doing the wrong thing, sanity checks failing — bring the situation to
the user. If the question is genuinely a knowledge gap (e.g., "what does this
rebase error mean?"), consulting the advisor is fine, but most of the time the
right escalation is to the user.
