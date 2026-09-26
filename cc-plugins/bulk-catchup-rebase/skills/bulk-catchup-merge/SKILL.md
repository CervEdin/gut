---
name: bulk-catchup-merge
description: >
  Catch up a long-lived branch that trails upstream by many commits by merging
  upstream in steps — through tagged releases or other intermediate points —
  with `git rerere` recording each conflict resolution, then taking one final
  merge of the upstream tip. Use this skill whenever the user wants to merge
  main into a stale branch, catch a branch up by merging, has too many conflicts
  merging upstream in one go, or wants to break a big upstream merge into
  smaller chunks. Also the rerere-priming merge pass that bulk-catchup-rebase
  runs before its rebase. Do NOT use when the user wants a linear history — that
  is bulk-catchup-rebase.
allowed-tools: Bash, Read, Edit, Write, Agent
---

# Bulk Catch-up Merge

An iterative merge for catching up a long-lived branch that has fallen far
behind upstream. A single `git merge origin/HEAD` produces an unmanageable wall
of conflicts; this approach walks upstream one intermediate point at a time so
each conflict set stays small and `git rerere` captures each resolution. A final
merge of the upstream tip then completes in one shot.

## When to use this skill

Use this skill when the branch is far enough behind that a one-shot merge is
unmanageable — tens to hundreds of upstream commits, possibly spanning months or
years — and a merge commit is an acceptable result: the branch's commit identity
isn't worth preserving, or the project's workflow prefers merge commits.

Do NOT use for:

- **Linear history** (the branch's commits replayed on top of upstream) → use
  `bulk-catchup-rebase`, which runs this skill as its first pass
- **A single live conflict** you're already stopped at → use
  `resolve-merge-conflicts`

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
```

All merge commands in the sections below are written with this prefix. Keep it
on every command, even when the user's config already sets zdiff3 globally — the
flag is idempotent, costs nothing, and makes each command self-documenting. Do
not propose dropping it to "simplify" the commands.

## Orientation: test merge first

**Orientation is read-only — do not fetch.** The whole run (probe, loop, final
merge) must see a single upstream state, and that invariant is achieved by NOT
fetching: operate on the remote-tracking refs as they are. A fetch moves those
refs — it can shift the merge target and invalidate conflict fingerprints, and
the user may have deliberately pinned the refs they want to catch up to. If the
refs look stale, say so and ask the user whether to fetch before anything
starts; never fetch on your own initiative.

If `bulk-catchup-rebase` invoked this skill, it has already run the probe and
the clean-build check — skip straight to the loop.

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

**If the probe is fully clean, just merge `origin/HEAD`** (see Finish). Walking
every intermediate point through a conflict-free landscape is pure ceremony; the
probe result, not the size of the gap, is the decision point.

If the probe showed conflicts, note what you saw and proceed to the loop.

**Verify the branch's own build is clean before starting the loop.** If the
branch is already broken at HEAD, no compile gate during the iterative loop is
trustworthy — you cannot tell whether a new build break comes from a merge or
was pre-existing. Ideally every commit on the branch is bisectable, but that is
not a hard requirement here — what _is_ required is a clean build at the branch
tip before the loop starts.

## Iterative merge with rerere

For each suitable intermediate point on the upstream branch — tagged releases
work well — attempt a no-commit merge. Clean merges are discarded; conflicts
stop the loop so you can resolve them:

```sh
for v in $(git tag --sort=version:refname --list 'v*' --no-merged HEAD --merged origin/HEAD); do
  if git -c merge.conflictstyle=zdiff3 merge --no-commit --no-ff "$v"; then
    git merge --abort                                       # clean: exit 0 — discard, keep walking
  elif ! git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    echo "Merge of $v failed for a non-conflict reason — stop and investigate"; break
  elif git status --porcelain | grep -E '^(DU|UD|AU|UA|DD|AA) '; then
    echo "Conflict at $v above — structural (add/delete); rerere never caches these, manual decision needed"; break
  elif ! git diff --check; then
    echo "Conflict at $v above — manual resolution needed"; break
  else
    echo "Conflict at $v — rerere resolved fully; verify, then commit"; break
  fi
done
```

The loop classifies each stop so later steps don't rediscover it — and so a
rerere replay can't masquerade as a clean merge. Exit 0 is a **clean** merge
(discarded). A nonzero exit with no `MERGE_HEAD` is a **hard failure** (bad ref,
dirty tree, unrelated histories) — stop and investigate, don't treat it as a
conflict. A nonzero exit with `MERGE_HEAD` set is a real conflict stop,
classified as **structural** (add/delete — rerere never caches these),
**manual** (a real text conflict with no cached answer), or **rerere-resolved**
(the cache replayed cleanly). See `references/conflict-classification.md` for
why the checks run in that order and why two of them print instead of staying
quiet.

All three are handled _identically_ below in terms of audit — the split is
carried forward only to frame the resolution and (per step 2) the pacing, never
to skip the audit. But don't read "structural" and "manual" as synonyms for
"hard": rerere skips add/delete conflicts unconditionally, no matter how many
times the same shape recurs, so a structural stop says nothing about how much
thought the resolution needs — see step 2.

Rerere caching is half of why the loop exists. The other half is **bisection**:
each intermediate point localizes one cluster of conflicts to one small upstream
stride. Semantic breaks — deleted APIs, removed infrastructure, renamed types —
surface against a narrow surrounding context instead of all at once. Skipping
the loop because rerere "wouldn't fire on these conflicts anyway" gives up the
bisection benefit too, which is often the more valuable half.

**Default: trust the loop.** Do not preemptively sample every Nth tag, skip
iterations, or shortcut because the tag count looks like a lot. Clean iterations
only add ~50–100ms of delay each — they aren't the cost to optimize.

**But bail out when the loop turns into pure ceremony.** If iteration after
iteration merges clean with no conflict in sight, stop walking and _try_ the
final merge of `origin/HEAD` from where you are (see Finish), with `--no-commit`
so a conflict costs nothing. If it conflicts, `git merge --abort` and resume the
loop where you left off. When `bulk-catchup-rebase` is driving, return to it
instead — it tries a one-shot rebase at this point. This is not the preemptive
shortcutting warned against above — the trigger is observed evidence (a streak
of clean merges), not tag-count anxiety, and the try costs one abort if it turns
out wrong.

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

When the loop stops, it has already classified the stop as **structural**,
**manual**, or **rerere-resolved** (or broken out for a clean merge / hard
failure). All three are handled the same way here. A rerere replay is still a
conflict stop — something was applied silently, so it gets a quick sanity check
and a provenance record — but not a full re-resolution; the reasoning already
happened when the resolution was first recorded.

1. **Delegate the resolution to a sub-agent running `resolve-merge-conflicts`.**
   Spawn a general-purpose sub-agent (a default sub-agent shares this working
   tree, so it sees the in-progress merge and its commit lands here), dispatched
   on Sonnet (`model: sonnet`) by default — conflict stops are frequent and
   mostly mechanical, so the cheaper model is the right fit; escalate to a
   stronger model only for a stop that already looks hard — and tell it to use
   the `resolve-merge-conflicts` skill to handle the stop end-to-end: read both
   sides, resolve it — or, for a rerere replay, run that skill's quick sanity
   checks (build, reasonableness, and the source resolution's recorded
   reasoning) rather than re-deriving it — build-verify on the unstaged tree,
   write the summary, stage, commit, and record the git note. Delegating keeps
   the heavy diff-reading out of this loop's context; the sub-agent returns a
   compact report instead of flooding the orchestration layer.

   How it commits and where it records the note belong to the
   resolve-merge-conflicts skill, not here. Pass the sub-agent inputs and
   intent, not a commit procedure: do **not** script the commit or pin a notes
   ref in the dispatch. A dispatched procedure silently overrides the resolver's
   own — which is exactly how a stale convention slips back in, replacing the
   commit and audit the resolver would have made with whatever the dispatch
   happened to dictate.

   Pass it the operation type (`merge`), the conflicted paths, and the loop's
   classification. Require it to report back — provenance (hand-resolved vs.
   rerere-replayed, and which cached resolution if identifiable), Judgment
   (mechanical vs. reconciled behavior from both sides — this is what step 2
   below actually paces on, not provenance), the build result, anomalies (a
   surprising state, a resolution it isn't confident in), and the commit it
   created — or that it is **blocked** and why.

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

   **Don't key this off structural/manual vs. rerere-resolved.** That split
   answers "has this exact conflict fingerprint been seen before on this run,"
   not "did resolving it take thought" — and two ordinary situations make
   non-rerere resolutions the norm rather than the exception:
   - Early in the loop the cache starts empty, so almost every stop is manual by
     construction (the "frequent manual stops ... are the expected working
     state" note below) — that's the normal shape of a first pass, not a run of
     hard calls.
   - A structural (add/delete) stop is _never_ cached by rerere, no matter how
     many times the same shape recurs, so it will always report as non-rerere —
     but resolving it is usually a one-line `git add`/`git rm` call
     (`resolve-merge-conflicts` §3e), not a hard one.

   Treating "not rerere-resolved" itself as the non-trivial trigger stops the
   loop at nearly every conflict during a first pass and at every add/delete —
   exactly the opposite of what the loop exists to do. Instead, read the
   resolver's **Judgment** field (see that skill's report section) alongside
   build and anomalies:

   - **Trivial** — build passed, no anomalies, and Judgment says mechanical
     (this covers a clean rerere replay _and_ a hand resolution that was an
     unambiguous accept-one-side, an artifact regen, a no-stakes add/delete, or
     a build fix in a conflict-free file that only carries one side's own change
     into the line it missed): show a one-line summary and continue without
     waiting.
   - **Non-trivial** — the resolution is genuinely ambiguous: Judgment says it
     reconciled behavior or intent from both sides, or more than one resolution
     was defensible and the resolver picked one; the build is still red; the
     resolver flagged an anomaly or is **blocked**. Stop and surface the report
     and the committed resolution (`git show`, or the git note) for explicit
     approval. A committed resolution is fully reversible — reset it if you
     reject it.

   Touching a file outside the conflicted set is not a pause trigger on its own.
   A merge can leave a conflict-free file uncompilable
   (`resolve-merge-conflicts` §3f); when the fix follows the incoming side's
   change and the build goes green, that is the mechanical case above, and it
   belongs in the one-line summary with the file named. Pausing there is the
   "not rerere-resolved" mistake in another shape: the loop stops at every step
   that took any work, instead of at the ones where the resolver had to choose.

   Provenance (structural/manual vs. rerere-replayed) is still worth relaying in
   the one-line summary as audit context, but it doesn't gate the pause decision
   by itself.

   **In-session pauses are binding regardless.** If the user told you to stop,
   stop and surface state — a green build and a clean rerere replay are not
   approval to continue. The loop has the strongest "barrel through" momentum,
   which is exactly where a pause instruction is most easily overridden by
   accident.

3. **Rerun the loop.** The tag you just merged is now an ancestor of HEAD, so
   the `--no-merged HEAD` filter excludes it and the walk advances to the next
   conflict — that, not rerere, is why this conflict won't stop you again, and
   rerere's payoff comes in the final merge, or in the replay if
   `bulk-catchup-rebase` is driving: frequent manual stops (and a near-empty
   cache) during this first pass are the expected working state, not a fault.

Repeat until the loop runs to completion with no conflicts. At that point rerere
should have a recorded resolution for every conflict, ready to replay.

**Generated files** are resolved at their source, not the artifact — the
`resolve-merge-conflicts` skill handles that (its artifacts section). One
bulk-loop caveat to pass along to the sub-agent: after regenerating, stage
**all** output with `git add -u`, never `git add <specific-file>` — a generator
often emits several files, and leaving siblings unstaged trips the next
iteration.

## Lock contention is normal in the loop

When running merge commands in a tight loop, you may occasionally hit
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

## Finish: merge the upstream tip

**If `bulk-catchup-rebase` invoked this skill, stop after the loop and return.
Do not take the final merge** — the rebase pass replays the intermediate merges
the loop committed, and an extra merge of `origin/HEAD` would change that list.

Otherwise, once the loop completes with no conflicts, run:

```sh
git -c merge.conflictstyle=zdiff3 merge origin/HEAD
```

Rerere replays every cached resolution and the merge completes cleanly in one
shot. If it stops anyway, treat it like any other loop stop: delegate and pace
as above.

## Pitfalls

- **Forgetting `rerere.enabled`** — no resolutions are cached; every iteration
  re-conflicts from scratch. Enable it before the loop, not after.

- **Fetching mid-run** — a fetch moves remote-tracking refs, so the merge target
  shifts and the loop's conflict fingerprints may not match the conflicts the
  final merge (or `bulk-catchup-rebase`'s replay) presents. The "same upstream
  state throughout" invariant is achieved by not fetching at all — not by
  fetching early. Don't bundle a fetch into orientation; if the refs look stale,
  ask the user before starting (see Orientation).

- **`CONFLICT (modify/delete)` is never cached by rerere** — rerere only caches
  three-way content conflicts. Add/remove conflicts (`CONFLICT (modify/delete)`)
  are structural: one side deleted a file the other modified. These require a
  manual decision every time they appear — `git rm <file>` to accept the
  deletion, or restore + edit to keep it. Do not wait for rerere to kick in; it
  won't.

- **A corrupted stage must be redone, not patched forward.** If a stage in the
  loop went wrong — wrong files staged, wrong resolution applied, dirty tree
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

See `references/rerere-cheatsheet.md` for inspecting what rerere recorded or
replayed.

## When stuck, escalate to the user

Mistakes during a long-lived catch-up are expensive: they corrupt intermediate
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
command doing the wrong thing, merges failing the build — bring the situation to
the user. If the question is genuinely a knowledge gap (e.g., "what does this
merge error mean?"), consulting the advisor is fine, but most of the time the
right escalation is to the user.
