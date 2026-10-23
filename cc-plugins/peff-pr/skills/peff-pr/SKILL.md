---
name: peff-pr
description: >-
  Write or judge the title of a GitHub pull request, so that a reader who has
  not seen the diff knows why to care. Also covers the opening paragraph. Use it
  every time a PR title or description is written or renamed, and whenever the
  wording of one is being judged rather than the code: before `gh pr create`,
  before any `gh pr edit --title` or `--body`, when a commit subject is about to
  become a PR title, and when asked "is this a good title", "write the PR" or
  "rename the PR".
---

# peff-pr: PR titles that say why

## Purpose

A PR title is read in a list, a notification or an email by someone who has not
read the diff. In one line it must tell them what was wrong or what gets better,
so they can decide whether to care. The description's opening paragraph is an
_opening_, not a summary: it answers "if I read more, what will this be about?"
so the reader can categorise the PR and rank it against the other open PRs.
Everything after that is detail.

## Process

1. **Collect the facts.** Read the commit messages and the linked issue first:
   they say what problem the PR solves. Then the body and the diff: the diff
   only says what the PR touches. If the `commit-brief` skill is available, use
   its brief; otherwise note each fact and its source. Establish for each
   candidate claim:
   - was the fault _observed_ (a crash, a wrong number, a lost result) or is it
     only _possible_?
   - any number: a count, a size, a speed-up, how many records or users
   - the component or area the change lives in
   - whether the code is in use yet, or nothing calls it

   Read the project's CLAUDE.md and memory for its own naming conventions (how
   it names components, documents, sections) and follow them.

2. **Title.** Draft two or three candidates and run each through the title
   checklist. Discard any that fail; rewrite and check again. Keep one, plus at
   most one alternative when the trade-off is real.

3. **Opening.** Write the opening paragraph and run the opening checklist.

4. **Present.** Show the title and the opening together in one fenced block,
   hard-wrapped at 79 columns, so they can be judged as the reader will see
   them. When judging, run the same checklists; give the verdict first (passes,
   or fails on: ...), then the rewrite. Give word counts when length is the
   question.

5. **Apply only when asked.** If the request already includes creating or
   editing the PR, apply the chosen title and text without waiting. Use
   `gh pr edit <n> -R <owner/repo> --title '...'`, and `--body-file <file>` for
   the description; for a new PR, `gh pr create` with the same title and body
   file. Write the body file with one line per paragraph and no hard wraps,
   because GitHub renders a single newline inside a paragraph as a line break.

## Rules for a good title

The examples are invented.

- **Why, not what.** Name the harm fixed, the gain, or the risk prevented. The
  harm is what the reader loses: a result, a correct number, a run, time. The
  faulty mechanism (an expired lease, an overflowed counter) is the cause. When
  it is named, it must make sense on its own.
  - "SnapshotStore: measure staleness from the last write" -> "Fix a nightly
    import losing its rows when another import starts".
- **Fix visible, harm first.** A fix title reads harm, then cause.
  - "Fix the sync retry counter overflowing, which stops all uploads" -> "Stop
    sync losing every upload once its retry counter overflows".
  - "Keep the date filter on when a saved report is rerun" -> "Stop a rerun of a
    saved report silently dropping its date filter".
- **Vary the verb and match it to reality.** Fix, Stop, Correct, Repair when the
  fault occurs. Prevent when it is a guard against something not seen. Cut,
  Tighten, Let for gains. Add ... for a feature, saying the gain. Delete X,
  saying why it is safe and why anyone cares.
  - "SQLite job store as a Redis stand-in" -> "Add a SQLite job store so the
    service runs locally without Redis".
  - "Delete the old importer, whose parser has drifted from the new one" ->
    "Delete the old importer, unused since 2.0 and with bugs of its own".
- **Short.** About 65 characters, never more than 72. A title carries one thing:
  the core problem the PR solves. If no single problem can carry the title, the
  PR is probably several PRs. Say so and propose the split instead of writing a
  title that lists.
- **No code identifiers.** No method, field, class, variable or file names,
  unless the identifier _is_ the public thing: an API offered upstream, a script
  the reader runs by that name. Name the concept instead: "the config parser",
  "the rate limiter", "a Postgres rollback". A name the project uses in speech
  for a model, tool or component ("the Scheduler", "the Indexer", "sync") is a
  concept, not an identifier.
  - "Fix build_docs.py crashing on nav.yml, where a page has no title" -> "Fix
    build_docs.py crashing on the navigation menu".
- **Ordinary technical words are fine.** Concurrent, intermediate, idempotent,
  abort, rollback, timeout. Paraphrasing around them is circumlocution, not
  plainness.
  - "Stop exports that start together merging their files" -> "Stop concurrent
    exports merging their files".
- **Say where.** The component, model, command or area, and for a document the
  part of it, so the reader knows the blast radius.
  - "Fix the crash opening a note with an image" -> "Stop the Android app
    crashing on a synced note with an image".
- **Say how much.** No "most", "some", "several", "a few" when there is a
  number. Write it as a numeral: 13,690 rows, 6 commands, 14-fold.
  - "Correct outdated commands in the install guide" -> "Correct 6 outdated
    commands in the install guide".
- **Say the scope honestly.** Not oddly specific when the fault is general; not
  undersold when the gain is general; say when nothing uses the code yet.
  - "Let the API and the workers run 8 threads on fewer than 8 cores" -> "Stop
    the core count capping the API and worker thread pools".
  - "Fix the dedup step running out of heap near 5 million rows" -> "Cut the
    dedup step's memory 14-fold and its run time 37-fold".
  - "Fix the new parser giving most dates the wrong time zone" -> "Fix wrong
    time zones in the replacement parser before anything uses it".
- **Only what the evidence supports.** No "never", "always", "silently", "no
  user hit it" unless established from the data or the code. "Silently" means
  nothing tells the user: no error, no log line, no visible difference. Name the
  observed effect, not a guessed mechanism.
  - "Stop the scheduler silently losing jobs to a race on restart" -> "Fix the
    scheduler dropping queued jobs when it restarts".
- **No dangling or ambiguous words.** No trailing "instead", "again", "too", "as
  well": each leaves the reader asking "as opposed to what?" A "which ..."
  clause pins the fault to the subject.
  - "Fix the API reference link resolving to the home page" -> "Fix the API
    reference link, which points at the home page".
  - "Stop retry logs colliding with the first attempt's number" -> "Stop job
    retries reusing the first attempt's sequence number".
- **One negative at most.** A negative verb inside a negative verb makes the
  reader invert twice: "Stop ... refusing valid files" means "accept valid
  files"; "Stop ... losing uploads" has one negative and is fine.
  - "Stop a wrong size check making the uploader refuse valid files" -> "Fix the
    uploader's size check, which rules out valid files".
- **No bare references.** An issue or PR number says nothing on its own.
  - "Fix the typos of #57 in 5 tutorial pages" -> "Fix the typos codespell found
    in 5 tutorial pages".

## Title checklist

Run on every candidate. Every line must be yes.

- [ ] Harm fixed, gain, or risk prevented is stated, not the change
- [ ] A fix is visibly a fix, and the harm comes before its cause
- [ ] The verb matches reality: observed fault, guard, gain, feature, removal
- [ ] At most about 65 characters, never over 72
- [ ] Carries one thing: the core problem from the commits and the issue, not
      the most visible change in the diff; if none fits, propose a split
- [ ] No code identifier, unless it is the public name of the thing
- [ ] No circumlocution around an ordinary technical word
- [ ] Says where: component, command, model, part of the document
- [ ] Says how much, as a numeral, whenever there is a number
- [ ] Scope is honest: not oddly specific, not undersold, says if unused yet
- [ ] Every word is backed by the diff, the data or the issue
- [ ] No dangling word, no clause that can be read two ways
- [ ] At most one negative
- [ ] No bare issue, PR or commit reference

## Opening paragraph

The opening paragraph, under the title: short beats complete.

**Length.** About 40 words, 2 to 4 sentences; up to about 55 for a PR with
several faults. Aim for sentences of 13 to 16 words. One can run longer at
times; 30 words or more is a chain.

**Content, in this order.**

1. What goes wrong, for whom, in plain words. Give a rough figure ("about 5 % of
   the uploads", "about 90 % of the active accounts") rather than exact counts
   and ids.
2. Whether it happened or is latent (found in review, never seen in a run). Code
   that nothing uses yet is said in the first sentence ("the replacement parser,
   which nothing uses yet").
3. Why it matters: what it blocks, what reads wrong, how much the result changes
   ("changes the outcome on under 1 %, so the gain is small").
4. The delivery kind, when it matters: draft, proof of concept, stop-gap, quick
   fix to ship as soon as possible, already applied to the data. This is a note
   on how to treat the PR, not a description of the fix.

**What stays out.**

- The fix, if it pushes the paragraph past 40 words. Once the problem is stated,
  the fix fixes it; how it does so rarely changes how the PR is treated. When it
  is kept, it is one sentence that starts "The fix ...", never "This ...", which
  has no referent.
- Evidence: dates, user and record ids, query results, counts to the unit. Those
  belong in the body unless they are what makes the reader care.
- The mechanism beyond one sentence.
- A restatement of the title. The opening may share the title's words, but it
  starts from what the title leaves open.

**Phrasing.**

- Use ", so" and semicolons sparingly. When every paragraph has one, the text
  reads as machine-made. One short cause and effect joined by ", so" is fine. A
  long chain ("X does A, so B, and C") is recast with the harm first and the
  cause after "because"; that reads well. Chopping the chain into bare full-stop
  sentences does not.
- Plain, direct statements in present tense and active voice, in words the
  reader has been given. A term the opening has not explained is said in plain
  words or left to the body.
- Keep a project's own word for a state, and do not swap in a near synonym that
  means something else. If a project calls a job that has used up its retries
  "parked", do not write "failed" (a failure is one attempt) or "timed out" (the
  limit is on retries, not time).
- A status sentence must connect to its neighbours. "Not observed; found in
  review" dropped between the harm and the fix reads as a non sequitur. Join it
  to the reason it matters: "The fault is latent, but it is why imports are kept
  to one worker at a time."

Never open with a base-branch note, "Fixes #N", a file path, a bare "Problem:
`identifier` does X", or a lead-in such as "Three problems:".

After the opening, in detail sections: identifiers, the base branch and
stacking, "Fixes #N", checks run, decisions taken without the reviewer,
alternatives considered. A PR proposes one change. It never asks the reviewer to
choose between options; a choice goes on the issue.

No hedges that hide whether it happened ("so far", "which can"), and no
narration ("When a worker threw ...").

**Example.** The same opening at 98 words and at 39, under the title "Fix the
uploader's size check, which rules out valid files":

```
The uploader can refuse a file that the server would accept, because the size
it checks is not the size the server limits. It applies the 100 MB limit after
base64 encoding, which adds a third to every file. The server applies it
before encoding: a 90 MB file passes there but fails here. In last month's
logs, 1,412 refusals from 96 accounts were for files between 75 and 100 MB;
none of them was found to be over the server's limit. The fix checks the size
before encoding, as the server does, which holds for every file.
```

```
The uploader can refuse a file the server would accept. It checks the 100 MB
limit after base64 encoding, which adds a third. In last month's logs, about
30 % of its refusals were for files the server takes.
```

What went: the 90 MB example, the exact counts, the hedge about files over the
server's limit, and the fix.

## Opening checklist

Every line must be yes.

- [ ] About 40 words, 2 to 4 sentences; up to about 55 for several faults
- [ ] Says what goes wrong and for whom, in plain words
- [ ] Says whether it happened or is latent, and if nothing uses the code yet
- [ ] Says why it matters
- [ ] Adds to the title instead of restating it
- [ ] No "This ..." and no "Fixes #N" anywhere in the opening
