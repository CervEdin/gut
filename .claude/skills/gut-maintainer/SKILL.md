---
name: gut-maintainer
description: >-
  Maintain the gut project — apply posted patches with git am, manage the
  main/next/seen integration branches, post "What's cooking" status, handle
  rerolls, semantic conflicts, and SQUASH fix-ups. Use when acting as the gut
  maintainer: integrating a posted topic, rebuilding next or seen, graduating a
  topic to main, posting What's cooking, or deciding whether a topic is ready to
  advance. The contributor side (sending patches, bug reports, replies) lives in
  the gut-mailing-list skill.
disable-model-invocation: false
---

# gut-maintainer

This skill covers the **maintainer** half of the gut workflow. The contributor
half — sending patches, bug reports, and replies — lives in `gut-mailing-list`.

gut adapts Junio C Hamano's Git workflow. The conventions in this skill are
derived from Junio's published maintainer workflow for the Git project, and
quoted where useful.

## Branch policy

gut runs four integration branches (no `jch` — the project is small enough that
a single maintainer's daily-driver branch isn't needed):

| Branch  | Role                                                                     |
| ------- | ------------------------------------------------------------------------ |
| `maint` | Bugfixes for the most recent release. **Never rewound.** Tagged vX.Y.Z.  |
| `main`  | Next feature release. **Never rewound.** Tagged vX.Y.0.                  |
| `next`  | Accepted topics cooking before main. Rewound only at start of a cycle.   |
| `seen`  | All proposed topics. Rebuilt on top of `next` each round, force-push OK. |

Normally `seen` ⊇ `next` ⊇ `main` ⊇ `maint`. A topic graduates
`seen → next → main` as it earns confidence; the cooking time in `next` is the
regression buffer. Bugfixes that need to ship as a point release land on `maint`
first and then merge up to `main`.

### Lifecycle of `maint`

After a feature release vX.Y.0 ships, fast-forward `maint` to the release tag:

```bash
git checkout maint
git merge --ff-only vX.Y.0
```

Bugfixes accumulate on `maint`; tag `vX.Y.1`, `vX.Y.2`, … as maintenance
releases ship. Because `main` contains all of `maint`, the fixes propagate up
automatically the next time `maint` merges into `main` (or via a periodic
`git merge maint` on `main`).

Until gut's first feature release, `maint` and `main` point at the same commit
and behave identically — `maint` exists so the workflow is in place when the
first release ships.

## Topic branches

- **Naming: `ai/topic`** — `ai` is the author's two-letter initials, `topic` is
  a short descriptive name. From Junio's workflow:

  > A topic branch is named as ai/topic where "ai" is two-letter string named
  > after author's initial and "topic" is a descriptive name of the topic.

  Initials registry for gut:

  | Initials | Author           |
  | -------- | ---------------- |
  | `cc/`    | Claude           |
  | `ec/`    | Erik Cervin-Edin |

  Real examples from git.git: `en/backfill-fixes-and-edges` (Elijah Newren),
  `tb/pseudo-merge-bugfixes` (Taylor Blau), `ps/odb-in-memory` (Patrick
  Steinhardt).

- **No kind prefix.** Do not use `feat/`, `fix/`, `wip/`, `acked-` etc. Junio's
  WoW puts kind in the commit message and review state in `whats-cooking.txt`,
  not in the branch name. The exception is `wip/` for genuinely-not-ready work
  the author wants flagged ("don't merge this"); historical gut branches use it
  and we keep that until they graduate or are discarded.

- **Maint topics** that target the released version (bugfixes for the prior
  feature release) are conventionally `ai/maint-topic` and fork from `maint`,
  not `main`. Matches Junio's `ai/maint-topic` form.

- Forked from `main` (or `maint`, or the oldest integration branch the change
  applies to — see `CONTRIBUTING.md`).

- Rerolls update the same topic ref via the reroll pattern below.

## A maintainer day

1. **Scan the list.** Read replies, reviews, new submissions. Save each topic's
   thread to its own mbox.
2. **Apply patches** (`git am`) to a fresh topic branch off `main`, or re-apply
   to an existing topic branch for a reroll.
3. **Decide** what each topic is ready for: direct-to-`main` (rare), merge to
   `next`, merge to `seen`, or stay on the topic branch.
4. **Rebuild `seen`** (and `next` if changed) from a declarative recipe.
5. **Post "What's cooking"** summarizing the state.
6. **Push** the integration branches.

## Mechanics

### Saving a thread to mbox

himalaya can export individual messages; for a series, concatenate them. The
thread view groups them:

```bash
himalaya envelope thread -f .gut -i <id>          # see the conversation
himalaya message export -F -d /tmp/foo.eml <id>   # raw RFC-5322 message
```

For a multi-patch series, export each `[PATCH n/N]` message and `cat` them in
order (the cover letter `[PATCH 0/N]` doesn't apply with `git am` — drop it or
let `am` skip it). The result is a Maildir-style mbox that `git am` accepts.

A pragmatic alternative: ask the contributor to point at a `format-patch` output
range, and reproduce it locally from their topic ref if you have it. For
genuinely list-only patches, the export-and-concat path is the one that scales.

### Initial application of a new topic

```bash
git checkout -b ai/foo main
git am -sc3 /tmp/foo.mbox
./git-sanity.sh    # or whatever the topic touches
```

`-sc3`:

- `-s` adds `Signed-off-by:` (from committer; only meaningful if the maintainer
  is also adding their own SoB — most patches arrive with the author's SoB
  already)
- `-c` enables scissors-line handling (`-- >8 --` cuts headers)
- `-3` falls back to a 3-way merge when context lines have shifted — fixes most
  "patch does not apply" failures

If `git am -3` still fails, fall back to `git apply -3 -C1 patch.patch` (allows
context lines to shift further than `git am -3` does); if that also fails,
investigate the patch structure manually.

### amlog: the Message-Id audit trail

`git am` invokes the `post-applypatch` hook (installed at
`.git/hooks/post-applypatch` as a symlink to `Meta/post-applypatch`). That hook
reads the source email's `Message-Id:` header from the in-progress mailbox under
`$GIT_DIR/rebase-apply/`, and records it as a git note on the resulting commit
under `refs/notes/amlog`:

```
$ git show -s --notes=amlog HEAD
... commit ...
Notes (amlog):
    Message-Id: <20260424184015.49946-1-claude@gut.local>
```

This is what populates the `source:` lines in `whats-cooking.txt` — read back
with `git log --notes=amlog --first-parent --format=%N ^main TOPIC`.

**One-time install per clone** (already done; recorded here for new clones):

```bash
ln -s ../../Meta/post-applypatch .git/hooks/post-applypatch
ln -s ../../Meta/pre-applypatch  .git/hooks/pre-applypatch
git config notes.rewriteRef refs/notes/amlog
```

The `notes.rewriteRef` config keeps the note attached when the commit gets
rebased — without it, rerolls would lose the audit trail.

**Pushing the audit trail.** Notes don't push by default. To share amlog with
other clones (or just back up):

```bash
git push origin refs/notes/amlog
```

Add it to `remote.origin.push` if you want every `git push` to include it;
otherwise push manually after batches of `git am`.

The companion `pre-applypatch` hook is git-specific (test-number collision
check) and effectively a no-op for gut. Kept for parity.

### Reroll — replacing a topic that's NOT yet in next

The reroll pattern from Junio's workflow:

```bash
git checkout main...ai/foo        # detach at the fork point
git am -sc3 /tmp/foo-v2.mbox
git range-diff @{-1}...                # what changed since v1
git diff @{-1}                          # tree-level review
git checkout -B @{-1}                   # update ai/foo to here
```

`main...ai/foo` is the "merge base of main and ai/foo" — i.e. where the topic
forked. Reapplying onto the same fork point keeps the topic's base stable across
rerolls, which keeps `range-diff` meaningful.

Tag the previous tip first if you want to preserve it (the contributor should
already be doing this for their own range-diff per `gut-mailing-list`'s tagging
convention `<topic>/v<N>`).

For quick triage of what a reroll changed, `range-diff` accepts `--left-only`
and `--right-only` to show only patches unique to one side. `--left-only` shows
commits that v1 had but v2 dropped; `--right-only` shows commits v2 added. Both
suppress the paired (modified) commits, so for a large series where most patches
are unchanged, they cut the noise to just what moved.

### Reroll — replacing a topic that's ALREADY in next

Don't. Once a topic is in `next`, its history is fixed — replacement happens by
**applying fix-up patches on top of the topic** and re-merging the topic to
`next`. From Junio's workflow:

> Replacement patches to an existing topic are accepted only for commits not in
> 'next'.

So: if v1 went to `seen` only, the reroll pattern above works. If v1 was merged
to `next`, the v2 has to come as incremental fix-ups, not a ground-up rewrite.

### Don't patch `seen` in place

When a v2 reroll arrives for a topic already in `seen`, follow the "Reroll — NOT
yet in next" procedure above (replace the topic branch on its merge base, then
rebuild `seen` via the recipe below). Do **not** sit on `seen` and `git am` the
v2 patches there.

`git am` against `seen` directly produces a "both added" conflict:
`git format-patch` writes a new-file patch with base = `origin/main` (where the
file does not exist), but `seen` already has the file from v1's integration.
`-3` does not help — there is no pre-image blob to three-way against.

The reason this isn't worth working around is that `seen` is rebuilt directly on
`main` each cycle. From Junio's workflow:

> `seen` contains all the topics merged to `next`, but is rebuilt directly on
> `master`.

Individual reroll merges into `seen` aren't preserved across iterations, so
there is nothing to revert and nothing to patch in place. Replace the topic
branch and rebuild `seen` from `main`.

### Direct-to-main / direct-to-maint commits

For obviously correct fixes (typo, docfix) that target `main`, a topic branch is
overkill:

```bash
git checkout main
git am -sc3 /tmp/typofix.mbox
./git-sanity.sh
```

The same shortcut applies to `maint` for bugfixes that pertain to the released
version — apply directly to `maint`, then merge `maint` into `main` so the fix
propagates:

```bash
git checkout maint
git am -sc3 /tmp/bugfix.mbox
./git-sanity.sh
git checkout main && git merge --no-ff maint
```

This should be rare. When in doubt, route through a topic branch and let it cook
in `seen`/`next` first.

### The `todo` orphan branch

gut keeps maintainer tooling on a separate **orphan** branch named `todo`,
mirroring the convention Junio has used in git.git since 2005-08-26. The branch
shares no history with `main` (`git merge-base todo main` exits 1) and holds:

```
README.cooking      — explains the branch and the Meta/ worktree pin
Reintegrate         — per-topic merge primitive (echo TOPIC | ./Reintegrate)
redo-next.sh        — declarative recipe to rebuild 'next' from 'main'
redo-seen.sh        — declarative recipe to rebuild 'seen' from 'next'
whats-cooking.txt   — current state of the integration tree
```

**Why orphan, not a `Meta/` directory on `main`:** keeps maintainer machinery
out of release tarballs and contributor checkouts; gives `whats-cooking.txt` a
real diffable history; can never be merged into `main` by accident. Tradeoff:
two refs to track and a one-time worktree setup. See the rationale block in
`README.cooking`.

**Worktree pin.** Mount `todo` at `Meta/` inside the `main` checkout so the
scripts are reachable from a `main` shell:

```bash
git worktree add Meta todo
echo /Meta/ >>.git/info/exclude    # hide from `git status` on other branches
```

After that, `Meta/Reintegrate`, `Meta/redo-seen.sh`, `Meta/whats-cooking.txt`
all work from the project root. The `Meta/` name is a worktree pin **only** —
there is no `Meta/` directory on the `todo` branch itself. This matches Junio's
casual references in his maintainer doc to `Meta/cook` and `Meta/Reintegrate`.

`.git/info/exclude` (per-clone, untracked) is preferred over a tracked
`.gitignore` entry because the worktree pin is a maintainer-local choice, not
something every contributor's clone should carry.

### Rebuilding `next` and `seen` from a recipe

The recipes are **declarative** — the script is the source of truth for what's
in the branch. To change `next` or `seen`, edit the script and re-run from a
clean base. Don't patch the branch in place.

`Reintegrate` reads topic refs from stdin and merges each one with `--no-ff`,
squashing `refs/merge-fix/<topic>` on top if that ref exists (see "merge-fix for
semantic conflicts" below). `redo-next.sh` and `redo-seen.sh` are thin wrappers
that pipe a topic list into it:

```sh
# Meta/redo-seen.sh
./Reintegrate <<'EOF'
cc/contributing-expand
EOF
```

Rebuild flow:

```bash
git checkout --detach main
sh Meta/redo-next.sh
git checkout -B next

git checkout -B seen next
sh Meta/redo-seen.sh
```

When a topic graduates from `seen` to `next`, move its line from `redo-seen.sh`
to `redo-next.sh`. When it graduates to `main`, drop it from both.

To audit what each merge brought in after a rebuild, use `git log --dd`. It
shows only the diff each merge introduced (the symmetric difference between
parent trees), skipping commits that are reachable from the first parent. This
gives a per-topic view of what landed, which is useful for verifying the rebuilt
branch matches expectations.

**Merge subjects.** Use git's default — never pass `-m` to `git merge`. With
`seen` checked out, `git merge --no-ff ai/foo` produces
`Merge branch 'ai/foo' into seen` automatically (the "into seen" suffix is git's
default for non-master/non-main current branches). This matches Junio's
convention exactly (e.g. `Merge branch 'en/backfill-fixes-and-edges' into seen`
in git.git origin/seen) and is what Reintegrate's parser expects. Custom
prefixes like `seen: merge X` break the parser and produce `Huh?:` warnings
during redo-script generation.

### Trial-merge before promoting

Before merging a topic to `next`, build-test it merged into the current `next`.
Before posting "What's cooking" promising a merge, build-test the rebuilt
branch. Semantic conflicts (textual clean, semantic broken) are caught here, not
in CI later.

### SQUASH??? fix-ups

When a topic doesn't quite build but the fix is one line, add a commit on top
with subject `SQUASH??? <description>`. The author is expected to fold it into
their next reroll. If they disagree, drop it from the next round. From Junio's
workflow:

> These changes are what the maintainer is not 100% committed to (...) so that
> they can be removed easily as needed. The expectation is that the original
> author will make corrections in a reroll.

Mention SQUASH??? commits explicitly in the topic's "What's cooking" entry so
the author notices. Don't squash the SQUASH??? into the topic yourself — leave
it visible.

### merge-fix for semantic conflicts

When two topics merge textually but the result doesn't build (e.g. A renames a
variable, B adds a use of the old name), record a merge-fix under
`refs/merge-fix/<topic>`:

```bash
git checkout seen~N             # the problem merge
# edit working tree to fix the semantic conflict
git commit -m 'merge-fix/ai/foo' -a
git update-ref refs/merge-fix/ai/foo HEAD
```

Then have the recipe replay it when merging that topic:

```sh
git merge --rerere-autoupdate --no-ff ai/foo
git cherry-pick -n refs/merge-fix/ai/foo
git commit --amend --no-edit
```

## "What's cooking in gut.git"

Post a status email to `gut@mbp.localdomain` whenever the integration state
moves meaningfully (new topics arrived, a topic graduated, a topic stalled).
Junio posts ~weekly; for gut, post when there's something to say.

### Subject

```
What's cooking in gut.git (Apr 2026, #01)
```

`<Mon> <YYYY>, #NN` — month, year, issue number within that month.

### Body shape

Open with a short paragraph: what's new this issue, anything notable (release
just shipped, you're offline next week, etc.). Then sections, omitting empty
ones:

- `[New Topics]` — appeared on the list since last issue
- `[Cooking]` — currently in `next` or `seen`, awaiting graduation
- `[Graduated to main]` — landed since last issue
- `[Stalled]` — inactive long enough to be at risk of discard
- `[Discarded]` — dropped, with a one-line reason

### Per-topic entry

Mirror the git mailing list format:

```
* cc/contributing-expand (2026-04-23) 5 commits
 + CONTRIBUTING: clarify reroll expectations
 + CONTRIBUTING: document range-diff format
 - CONTRIBUTING: add maintainer notes
 - CONTRIBUTING: cross-reference howto
 - CONTRIBUTING: typofixes

 Expand CONTRIBUTING.md with reroll mechanics and maintainer-side
 expectations. The first two patches are well reviewed; the rest
 still need eyes.

 Expecting reroll.
 source: <20260423-contrib-v3-1@gut.local>
```

Conventions:

- `*` introduces the topic; format
  `<topic-ref> (<latest commit date>) N commits`
- `+` prefix on commits already in `next`
- `-` prefix on commits only in `seen`
- One-paragraph human description
- One status line, picked from:
  - `Will merge to 'next'.`
  - `Will merge to 'main'.`
  - `Needs review.`
  - `Expecting reroll.`
  - `Expecting (hopefully minor and final) reroll.`
  - `Stalled.`
  - `Discarded.`
- `source: <Message-Id>` of the patch (or cover letter for a series)
- Optional `cf. <Message-Id>` for a review or follow-up worth pointing at

### Sending it

Use the himalaya template pipeline from `gut-mailing-list`:

```bash
himalaya template write -a claude \
  -H "To: gut@mbp.localdomain" \
  -H "Subject: What's cooking in gut.git (Apr 2026, #01)" \
  "$(cat /tmp/whats-cooking.txt)" \
| himalaya template send -a claude
```

## Pitfalls

- **Never `cherry-pick`.** It produces a different commit object, which breaks
  `range-diff`, topic tracking, and (in git's setup) drops the amlog notes. Use
  `commit --amend` or `rebase` to make corrections.
- **Don't rewind `main` or `next` mid-cycle.** Anyone with topics building on
  top would break. `seen` is the only branch that rewinds freely.
- **Topics in `next` aren't replaced — they accumulate fix-ups.** Once it's in
  `next`, the only way forward is incremental.
- **"What's cooking" reflects state, not aspiration.** If you say "Will merge to
  'next'," your next integration round should actually do that. Otherwise the
  post is misleading.
- **A topic with no review activity for ~3 weeks is at risk of discard.** Mark
  it `[Stalled]` first, then `[Discarded]` next round if nobody revives it.
- **Don't squash a SQUASH??? into the topic yourself.** Leave it visible so the
  author can act on it in their reroll.

## Reference

- gut's `todo` branch — orphan, holds `Reintegrate`, `redo-{next,seen}.sh`,
  `whats-cooking.txt`. Mount with `git worktree add Meta todo`.
- Contributor side of the workflow: `gut-mailing-list` skill
- gut's own contributor docs: `CONTRIBUTING.md`
