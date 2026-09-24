---
name: bulk-catchup-rebase
description: >
  Bulk-rebase a long-lived branch that trails upstream by many commits, using
  iterative merges through tagged releases (or other intermediate points) so
  `git rerere` captures each conflict resolution and replays it during the final
  rebase. Use this skill whenever the user mentions a stale or long-lived
  branch, a branch that is far behind main/master, hundreds of commits behind
  upstream, a rebase that produced too many conflicts to handle in one pass, or
  wants to break a big upstream catch-up into smaller chunks. For merge-only
  catch-up (one final merge commit, no rebase) use bulk-catchup-merge. Do NOT
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

- **Merge-only catch-up** (a merge commit is fine, no linear history needed) →
  use `bulk-catchup-merge`
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

The prerequisites are those of the `bulk-catchup-merge` skill, which runs Step
1: `rerere.enabled` MUST be on, and every merge and rebase command carries the
`git -c merge.conflictstyle=zdiff3` prefix. See that skill's Prerequisites for
the reasons. Keep the prefix on every rebase command below too; do not propose
dropping it to "simplify" the commands.

## Step 0: Test merge first

**Orientation is read-only — do not fetch.** The whole run (probe, Step 1,
Step 2) must see a single upstream state, and that invariant is achieved by NOT
fetching: operate on the remote-tracking refs as they are. A fetch moves those
refs — it can shift the rebase target and invalidate conflict fingerprints, and
the user may have deliberately pinned the refs they want to catch up to. If the
refs look stale, say so and ask the user whether to fetch before anything
starts; never fetch on your own initiative.

Before starting the iterative loop, get a quick read on what the conflict
landscape actually looks like:

```sh
git -c merge.conflictstyle=zdiff3 merge --no-commit --no-ff origin/HEAD
git merge --abort
```

This probe runs in seconds and shows you — without committing anything — every
file that would conflict if you merged today. Use it to judge scope: a handful
of files in familiar packages is manageable in one session; dozens of unrelated
files across generated code may warrant regenerating sources first.

**If the probe is fully clean, try a one-shot rebase before reaching for the
bulk machinery.** Run the topology check (see Step 2) to pick the flags, then:

```sh
git -c merge.conflictstyle=zdiff3 rebase origin/HEAD   # --rebase-merges per the topology answer
```

A clean probe does not _guarantee_ a clean rebase — the probe tests one
tip-vs-tip merge, while a rebase replays each commit individually and any one of
them can conflict on the way. That's why this is a _try_: if the one-shot stops
at a conflict, `git rebase --abort` and fall back to Step 1 — nothing is lost by
the attempt. If it completes, skip straight to the sanity checks at the end of
this skill. Walking every intermediate point through a conflict-free landscape
is pure ceremony; the probe result, not the size of the gap, is the decision
point.

If the probe showed conflicts, note what you saw and proceed to Step 1.

**Verify the branch's own build is clean before starting the loop.** If the
branch is already broken at HEAD, no compile gate during the iterative loop is
trustworthy — you cannot tell whether a new build break comes from a merge or
was pre-existing. Ideally every commit on the branch is bisectable, but that is
not a hard requirement here — what _is_ required is a clean build at the branch
tip before the loop starts.

## Step 1: Iterative merge with rerere

Invoke the `bulk-catchup-merge` skill to run the iterative merge loop. Tell it
that `bulk-catchup-rebase` is driving and a rebase follows, so that it:

- skips its orientation (Step 0 above already ran the probe and the clean-build
  check),
- stops after the loop and returns, and does **not** take its final merge of
  `origin/HEAD` — Step 2 captures the merges the loop committed, and an extra
  merge would change that list, and
- returns here instead of trying a final merge if it bails out of a streak of
  clean merges. Run the topology check (Step 2), then _try_ a one-shot rebase
  from where you are, same as the clean-probe exit in Step 0. If the one-shot
  stops at a conflict, abort it and resume the loop where you left off.

When the loop completes with no conflicts, rerere should have a recorded
resolution for every conflict. Continue at Step 2.

## Step 2: Iterative rebase over the captured merges

Once Step 1 completes, convert the merge-commit history back to a linear rebase.
**First run the topology check (below) — it decides whether the `$sha^2` loop
here is even the right shape.** This iterative loop is **required** — do not
skip straight to `git rebase origin/HEAD`. A direct rebase against the remote
tip defeats rerere entirely: the cached resolutions from Step 1 were recorded at
specific conflict boundaries (one release worth of delta at a time), and a
single-shot rebase against the full upstream history presents conflicts at
different boundaries where the cached fingerprints do not match. The rerere
cache will appear to do nothing, and every conflict must be resolved by hand
again.

The loop below replays your commits through the same incremental boundaries so
rerere's fingerprints fire at the right moments. Only after the loop completes
do you perform a final `git rebase --no-rebase-merges origin/HEAD` to land on
the current tip cleanly.

MUST be done against the same upstream state as Step 1 — which means **no
fetching**, not "fetch first." The remote-tracking refs you started with ARE the
target; leave them alone until both passes are done (see Step 0).

**Check that no branch commit comes after the first Step 1 merge:**

```sh
git log --no-merges --first-parent --format=%h \
  $(git log --merges --first-parent --format=%H origin/HEAD..HEAD | tail -1)..HEAD
```

- Empty output: all the branch's own commits come before the Step 1 merges. Each
  loop iteration must then give the same tree as its merge `$sha`, and the loop
  below checks this.
- Non-empty output: the capture and reset commands below assume the other order.
  The capture finds only the merges after the newest branch commit, and the
  reset needs a merge at `HEAD`. Stop and ask the user how to continue. If the
  loop runs on a merge list made another way, the replayed trees also contain
  the commits listed, so they do not match the earlier merges. Tell the user
  that the per-iteration check does not apply. Remove the
  `git diff --quiet $sha HEAD` line from the loop, and after the last iteration
  compare with the old tip instead: `git diff --quiet $(cat /tmp/old-tip) HEAD`.

**Capture the merge SHAs in oldest-first order, and the old tip:**

```sh
git log --merges --format=%H $(git log --no-merges --format=%H -1 origin/HEAD..HEAD)..HEAD | tac > /tmp/merges
git rev-parse HEAD > /tmp/old-tip
```

`/tmp/old-tip` is the reference for the fallback tree check above and the
`<old-tip>` for the `range-diff` in the sanity checks.

**Reset to the first non-merge commit** (the original tip of your branch before
any of the Step 1 merges):

```sh
git reset --hard $(git log --no-merges --format=%H -1 HEAD^2..HEAD)
```

**Rebase onto each merge point in order, and check the tree after each one:**

```sh
for sha in $(cat /tmp/merges); do
  git -c merge.conflictstyle=zdiff3 rebase --no-rebase-merges $sha^2 || break
  git diff --quiet $sha HEAD || { echo "tree differs from $sha"; break; }
done
```

The tree check must run on every iteration, not only at conflict stops. A clean
replay never stops. A change that exists only in the merge, in a file that did
not conflict, therefore goes through with no stop and no signal. rerere stores
only conflict resolutions, and the rebase replays only the branch commit's diff,
so nothing else carries such a change into Step 2. A difference means either a
change that exists only in the merge (for example a KPI regeneration or a
formatter run), or a rerere replay that does not match what Step 1 recorded. See
"When the tree differs from the merge" below.

When the loop stops, it does not continue by itself. After you handle the stop,
start the loop again with only the merges that are not yet done, for example
`sed -n '<n>,$p' /tmp/merges` in place of `cat /tmp/merges`.

`git rebase` will stop at each conflict even when rerere has fully resolved it —
this is expected, and it is still a conflict stop to be audited, not skipped.
**Delegate it to a sub-agent running `resolve-merge-conflicts`, exactly as in
Step 1** (see step 1 of the loop in the `bulk-catchup-merge` skill): pass the
operation type (`rebase`), the conflicted paths, and the conflict's
classification (structural, manual, or rerere-resolved — same three categories
as Step 1), and require the same report back. Also require the output of
`git diff --cached --stat $sha` in the report. At a stop in the middle of a
series, this also shows the differences from the branch commits that are not yet
replayed, so it is information, not the decision. The check after the iteration
decides. The sub-agent reads both sides — for a replay it runs the quick sanity
checks rather than a full re-derivation: rerere matches on text fingerprints, so
a clean text resolution can still reference a symbol the surrounding upstream
delta removed in a different file (only the build catches that), and the source
resolution itself can have misread the history it reconciled — here the Step 1
commit and its audit note make that check cheap, since the recorded reasoning is
already written down and only needs to hold up, not be re-derived —
build-verifies on the unstaged tree, writes the audit, and commits the replayed
commit.

Unlike a merge, the sub-agent's commit does **not** conclude the operation —
this loop owns the continue. After the sub-agent returns and you have applied
the same pacing decision as Step 1 (step 2 of the loop in the
`bulk-catchup-merge` skill), advance:

```sh
git rebase --continue
```

`git rebase --continue` moves forward; if rerere left anything unresolved,
`--continue` will tell you.

When the rebase is complete, run the same tree check before you go on to the
next `$sha`:

```sh
git diff --quiet $sha HEAD || echo "tree differs from $sha"
```

If `git rebase --continue` itself stops again, check `git status` and
`git rerere status`. If rerere has no pending resolutions and the index is
clean, the commit may have become empty — run `git rebase --skip` to drop it
(see Pitfalls below). To confirm what a replay actually applied, ask rerere's
porcelain (`git rerere diff`, `remaining`) rather than inspecting the cache
directory; if you do need the directory, `git rev-parse --git-path rr-cache`
locates it (not `.git/rr-cache`). See
`../bulk-catchup-merge/references/rerere-cheatsheet.md`.

### When the tree differs from the merge

Show the paths that differ:

```sh
git diff --stat $sha HEAD
```

- **Generated files** (KPI JSON and similar): take the merge's version with
  `git checkout $sha -- <paths>`. This agrees with the rule to regenerate and
  never take a side, because the merge holds the regenerated output.
- **Other files:** send them to the resolver sub-agent or to the user. Do not
  take the merge's version without review.

Where the fix goes:

- At a conflict stop: fold the fix into the commit that is being replayed.
- After a clean replay: add the fix as a fixup to the branch commit that touched
  those paths (use the `git-rebase-i` skill), or as a separate commit when no
  branch commit touched them. Ask the user which one.

Then run the tree check again. Continue the loop only when it passes.

### Topology check — run before ANY rebase

Before any rebase this skill performs — the Step 2 loop, the final rebase onto
`origin/HEAD`, or a one-shot — check for internal merge commits:

```sh
git log --merges --oneline origin/HEAD..HEAD
```

Non-empty output → STOP and ask the user whether to preserve the branch's merge
topology (`--rebase-merges`) or flatten it. The trigger is mechanical on
purpose: never classify a merge as "just a catch-up" or "not meaningful
topology" on your own. A judgment-framed check is exactly what gets talked-past
mid-run, and a branch flattened without permission is expensive to undo. Whether
a merge commit matters is the user's call; the cost of asking is one question.

Repo merge policy is not evidence here. Squash-only settings, a rebase-only
merge queue, or branch protection describe how PRs land on the **default**
branch — they say nothing about what shape the user wants a local branch to
keep.

If the user chooses to preserve topology, the `$sha^2` loop above is not the
right shape. The working approach: start Step 2 with `git reset --hard` back to
the original branch tip (before any of the Step 1 merges), then rebase with
`--rebase-merges --update-refs` instead of `--no-rebase-merges`. Two runs
support this so far — a zero-conflict one-shot `git rebase --rebase-merges`
whose commits came out byte-identical under `git range-diff`, and a full Step
1 + Step 2 run that carried `--rebase-merges --update-refs` through the replay
and the final rebase, preserving the internal merge across one real conflict
stop. Evidence is still thin for conflict-heavy replays, so verify with
`git range-diff` afterward and watch the merge commits closely. The
per-iteration tree check applies only to the linear `$sha^2` loop. For this
variant, compare the final tree with the old tip:
`git diff --quiet $(cat /tmp/old-tip) HEAD`.

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
the rebase. Step 2 saved the old tip in `/tmp/old-tip`; use `git reflog` to find
the base if needed.

## Pitfalls

The pitfalls of the merge pass — forgetting `rerere.enabled`, fetching mid-run,
`CONFLICT (modify/delete)` never being cached, and redoing a corrupted stage —
are in the `bulk-catchup-merge` skill. The ones below belong to the rebase.

- **Letting the cache expire between passes** — `git gc` prunes recorded
  resolutions (`gc.rerereResolved`, 60 days by default; unresolved entries at
  15), so a long gap between Step 1 and Step 2 can empty the cache and make Step
  2 re-conflict everywhere as if rerere never ran. Run the two passes close
  together; if a Step 2 that should replay is instead stopping manually
  throughout, redo the relevant Step 1 merges to re-record before rebasing.

- **Changes that exist only in a Step 1 merge** — a KPI regeneration or an
  anomaly fix made in the merge, in a file that did not conflict, has no carrier
  into Step 2. rerere stores only conflict resolutions, and the rebase replays
  only the branch commit's diff, so Step 2 drops the change without a stop. The
  tree check after each iteration catches this; see "When the tree differs from
  the merge".

- **Treating `git diff @{1}` as a sanity check** — it shows upstream delta, not
  commit survival. Use `git range-diff` as described above.

- **Silently-dropped empty commits** — verify with both
  `git log origin/HEAD..HEAD` (count) and `git range-diff` (content). A commit
  dropped because it became empty is often benign, but not always.

- **`git rebase --continue` stopping again after rerere** — check
  `git rerere status`. If the index is clean and rerere has nothing pending, the
  commit is truly empty; use `git rebase --skip` to drop it.

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
