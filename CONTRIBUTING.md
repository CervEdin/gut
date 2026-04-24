# Contributing to gut

The workflow follows the same mailing-list-based model used by the Git project
itself.

## Patch lifecycle

1. You find an itch. You code it up. No pre-authorization needed.

   Patches are reviewed on the mailing list. Reviews assess the general idea,
   the design of the solution, and the implementation.

2. Send the patch to the list. Your goal is not to convince anyone that what you
   are building is good. Your goal is to get help coming up with a solution that
   is better than what you can build alone.

3. You get comments and suggestions. Respond on the mailing list and take them
   into account when preparing an updated version.

4. Updated versions are full replacements, not incremental updates on top of
   what you posted. Rewrite history (e.g. with `git rebase -i`) to present a
   clean, logical progression. Nobody is interested in your earlier mistakes.

5. Polish and re-send. Go back to step 2.

## Choose a starting point

The repo has three integration branches:

- `main` — stable, released state
- `next` — topics that have reached consensus on the list and are queued to
  graduate to `main`
- `seen` — all topics that have been posted, whether accepted or not;
  experimental

Base your work on the **oldest integration branch your change applies to**:

- Bug fixes against the released behavior → `main`
- New features → `main`
- Fix-on-top-of-in-flight-work → the topic branch it depends on

Do **not** base work on `next` or `seen`. They are re-integrated and
force-pushed as topics come and go; anything built on top of them cannot be
merged cleanly. If you genuinely need to depend on a topic that is only in
`next`, say so in your cover letter so others can reproduce your base.

If your starting point is anything other than `main`, communicate it in the
cover letter.

## Make separate commits for logically separate changes

Do not send a patch generated between your working tree and HEAD. Always make a
proper commit with a complete message and generate patches from there.

Give an explanation detailed enough that people can judge whether the change is
a good idea without reading the diff.

If your description gets too long, that is a sign the commit should be split
into finer-grained pieces.

Obvious typo fixes and other trivially-independent improvements are welcome —
preferably submitted as **independent patches separate from other changes**, not
bundled in with unrelated work.

Make sure your changes do not introduce whitespace errors. Run
`git diff --check` before committing.

## Tests

- When fixing a bug, add a regression test that fails without the fix.
- When adding a feature, add tests that show the feature triggers when it should
  and does not trigger when it shouldn't.
- After any change, run the full test suite (`test/` + `git-sanity.sh`) and make
  sure everything passes.
- Try merging your topic into `next` and `seen` before sending — other in-flight
  topics may have unexpected interactions with yours.
- If your change alters observable behavior, update the relevant documentation
  and script `--help` text in the same patch.

## Describe your changes well

The commit message is as important as the change itself. The body should:

- explain the problem the change tries to solve — what is wrong with the current
  code without the change
- justify the way the change solves the problem — why the result is better
- note alternate solutions considered but discarded, if any

The problem statement is written in the present tense. Write "the script does X
when given Y", not "the script used to do X". You do not have to say "Currently"
— the status quo is assumed.

Describe changes in imperative mood: "make xyzzy do frotz" rather than "[This
patch] makes xyzzy do frotz". Make the explanation self-contained: summarize the
relevant points of a discussion instead of linking to a mailing-list archive.

The first line should be a short description (50 characters is the soft limit)
with no trailing full stop. Prefix with `area: ` where area is the script or
component being modified:

```
git-resolve: handle quoted filenames on macOS
delorean: add --since flag
```

The word after `area:` is not capitalized unless there is a reason (e.g. a
proper noun or acronym).

### Referencing other commits

When referring to a commit on `main`, `next`, or `seen`, use the format
`abbreviated hash (subject, date)`:

```
Commit a4c2c2c (delorean: don't rely on GNU xargs -d in the
deleted-files loop, 2026-04-23) started feeding ref names through
xargs...
```

Generate it with:

```bash
git show -s --pretty=reference <commit>
```

Reference another commit when you are fixing a bug it introduced, extending a
feature it added, or noting a conflict with it from a trial merge.

## Certify your work with `Signed-off-by`

Add a `Signed-off-by` trailer to certify that you wrote the patch or have the
right to submit it under the same license:

```
Signed-off-by: Random J Developer <random@example.org>
```

Use `git commit -s` to add it automatically.

### Other useful trailers

- `Reported-by:` — credits someone who found the bug the patch fixes
- `Acked-by:` — indicates someone familiar with the area liked the patch
- `Reviewed-by:` — can only be offered by the reviewer after detailed analysis
- `Tested-by:` — indicates someone applied and tested the patch
- `Suggested-by:` — credits someone who suggested the idea

Only capitalize the first letter: `Signed-off-by`, not `Signed-Off-By`.

## Use of AI tools

AI tools are welcome as aids — for drafting, debugging, checking style, catching
obvious mistakes before sending. This is a pragmatic project; good patches are
good patches regardless of how they were produced.

However:

- You are responsible for every line you submit. If you cannot explain a change,
  do not send it.
- Patches that are clearly generated without understanding will be returned for
  revision.
- The `Signed-off-by` certifies that you know the origin and content of your
  contribution — including when you used AI assistance.

## Generate and review your patch

Use `git format-patch` / `git send-email` to produce and send patches. Use `-M`
when your patch involves renames; the receiving end handles them fine.

Before sending:

- Remove commented-out debugging code and any extra files that don't relate to
  the change.
- Re-read the generated patch — it's what reviewers will see, not your working
  tree.
- Confirm it applies cleanly on top of the starting point you chose.

## Sending patches

`git send-email` is already configured (see the repo `.gitconfig`) to deliver
via local sendmail to the gut mailing list at `gut@localhost`.

```bash
# single patch
git send-email -1

# everything between origin/main and HEAD
git send-email origin/main..HEAD
```

Subject prefixes:

- `[PATCH]` — a patch (added automatically by `git format-patch`).
- `[PATCH v2]`, `[PATCH v3]` — subsequent versions. Use `-v <n>`, which is short
  for `--subject-prefix="PATCH v<n>"`.
- `[RFC PATCH]` — request for comments before implementing. Use `--rfc`, short
  for `--subject-prefix="RFC PATCH"`.

Inter-version change notes can be kept in git-notes and inserted automatically
after the three-dash line via `git format-patch --notes`. Use this to summarize
what changed since v1 without cluttering the commit message itself.

Rerolls of v2 and later are also expected to carry a range-diff against the
previous version so reviewers can see what changed between iterations.

Do not attach patches as MIME attachments. Send them inline as plain text so
reviewers can quote and comment on specific lines. Do not cut-and-paste patches
between windows — tabs get mangled that way.

### Series vs standalone

A patch _series_ is a sequence of commits that belongs to **one topic**. The
`[PATCH n/N]` numbering and the cover letter exist to tell that single topic's
story — what it does, why it's split the way it is, what reviewers should focus
on.

Single-patch topics are sent with `[PATCH]` (or `[PATCH v2]`, etc.) **without
`n/N` numbering**. Use `n/N` only when there are genuinely multiple patches that
belong together.

Patches do **not** belong together just because you happen to send them in the
same batch. Patches that share a theme ("three ref-listing bugs", "three POSIX
portability fixes") but touch unrelated scripts, could be applied in any order,
and could be reviewed in isolation are not a series — they are independent
patches. Send each with its own `git send-email -1 <sha>` in its own thread.

Rule of thumb: if the cover letter you are about to write boils down to "here
are three unrelated fixes", the patches aren't a series. Send them individually.
Git's own guidance for obvious typo fixes says the same — "preferably submitted
as independent patches separate from other changes".

### Cover letter

For a genuine multi-patch series, include a cover letter:

```bash
git send-email --cover-letter --annotate origin/main..HEAD
```

The cover letter's title should succinctly cover the **purpose of the entire
topic** — imperative mood, like a commit subject. If you cannot write such a
title for your patches, they aren't a series.

The body explains the motivation and overall design of the series. Per-patch
details belong in the individual commit messages. The cover letter is not
recorded in the commit history, so anything useful to future readers should live
in the commits themselves.

Send the series as a thread: cover letter first (`[PATCH 0/N]`), then each patch
as a reply, either to the cover letter or to the preceding patch.
`git send-email` does this automatically.

For single-patch submissions, any additional context can go between the
three-dash line and the diffstat — it won't end up in the commit message.

## Handling conflicts and iterating patches

When revising a series, expect conflicts with other in-flight topics. The
iteration flow:

1. Format-patch your series from a clean base.

2. Find where the previous round was queued — often the tip of the relevant
   topic branch in `next` or `seen`.

3. Apply your new patches. Either:
   - They apply cleanly and tests pass — continue to step 4.
   - They apply but don't build, or conflicts appear. Identify what caused it
     (usually another topic that landed in your dependency area). Fresh-base on
     `main`, `merge --no-ff` in any topics you now depend on, rebuild the series
     on top, and format-patch from there. Note the dependency topics in your
     cover letter.

4. Trial-merge your topic into `next` and `seen` to see what conflicts others
   will hit:

   ```bash
   git checkout --detach origin/seen
   git revert -m 1 <merge-of-previous-iteration>   # if previous round is already in seen
   git merge <your-topic>
   ```

   You don't necessarily need to resolve the conflicts — noting them in the
   cover letter is enough. The conflicts may be the responsibility of whichever
   topic lands second.

Record in the cover letter anything non-obvious about the base, the
dependencies, or the conflicts you saw. The maintainer and other contributors
need to be able to reproduce your setup.
