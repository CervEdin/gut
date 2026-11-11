# Jeff King (peff) Commit Message Style

Reference for writing commit messages that channel Jeff King's voice and
approach. Distilled from his patches to git@vger.kernel.org.

The point is not impersonation — it's that peff's style forces you to articulate
the reasoning behind a change. Channeling his voice is the steering mechanism;
the goal is reasoning quality.

## Subject Line

The default peff format is:

```
area: lowercase imperative description
```

However, **the repo's existing convention always wins**. If the recent commit
log uses Conventional Commits (`feat:`, `fix:`, `chore:`, `feat(scope):`, etc.),
use that format instead:

```
fix(auth): handle nil pointer in batch resolver
feat: add retry logic for transient failures
```

General rules regardless of format:

- **50 char soft limit**, 72 hard limit for subject lines
- Lowercase after the colon
- Imperative mood: "fix", "use", "avoid", not "fixed", "uses", "avoided"
- A verb phrase that says what the commit does: "take btrfs checkpoints of the
  database", not "named databases and checkpoints". A noun phrase names a topic,
  and the reader still has to guess what changed in it. A subject that starts
  with a verb, such as "revert to a checkpoint", is already one
- No period at the end
- If the repo does NOT use Conventional Commits, area prefix matches the file,
  subsystem, or logical component (peff's default)
- For tightly scoped changes, a function name works as the area prefix:
  `check_connected(): delay opening new_pack`,
  `find_last_dir_sep(): convert inline function to macro`

## Body: Narrative Prose

The body reads like a debugging story or design explanation. It is NOT a
changelog entry. Its parts come in this order, and each part leads with its
point:

1. **The motive** — what the code does and why that is a problem, in the present
   tense ("We mmap() a loose object file, storing the result in..."; see Tense
   below). Trace the causal chain ("But if we hit an error, we jump to a label
   which does X, and X is wrong because..."). Do not open with "Today" or
   "Currently": the present tense says that already
2. **The fix, in one sentence** — "Fix this by ...", "Use Y instead", "Teach
   db_store to copy the main database to a remote location". It can be a
   paragraph of its own. For a small fix, stop here
3. **Each choice the fix makes, what and then why** — a paragraph for each
   choice a reader would question: what the code does, then the reason
4. **The alternative, after the choice that beat it** — as a conditional: "Had
   we copied the live database instead, the copy might never finish: SQLite's
   backup starts over each time another session commits." The point comes first,
   and a caveat or the rejected alternative follows it in the same paragraph
5. **Work left undone, only where this change leaves itself incomplete** — a
   `TODO:` paragraph that says what waits and why ("to keep the conflicts with
   the next topic small"). Follow-on work the change does not need, such as
   scheduling a job or choosing a host, goes to the tracker, not the message

Leading with the alternative or the caveat is the usual way to get this wrong.
The reader holds a clause before they know what it qualifies, and its pronouns
attach to the wrong noun:

```
wrong: The copy comes from a new checkpoint, not from SQLite's backup of
       the live database: that backup starts over each time another
       connection commits, and may never finish.
right: Copy from a new checkpoint. Had we used SQLite's backup of the
       live database, the copy might never finish: the backup starts
       over each time another connection commits.
```

A reader of the wrong version took the checkpoint to be what never finishes.

### Tense

The message is read against the parent commit. The behaviour the patch changes
is still the behaviour of the code the reader has in front of them, so describe
it in the present tense: "the trap removes the scratch file but never exits."
The past tense is only for history — an incident that happened, an earlier
commit that introduced the code. What the commit does takes the imperative:
"Export DB in the Makefile so that the scripts see the same value", not "The
Makefile exports DB so ...", which reads as the code before the patch.

```
wrong: The backup was queued by the last ExecStartPost=, so a failed sync
       skipped it.
right: The backup is queued by the last ExecStartPost=, so a failed sync
       skips it.
```

The wrong version reads like a story of what you did during the session. That is
the usual cause: the prose was written from memory of the work rather than from
the brief, whose `today` entries are already in the present tense.

### Tone

- **Conversational but precise** — uses "we", "our", as if talking to a peer on
  a mailing list
- **Plain language** — avoids jargon when a simpler word works
- **Tentative only when actually unsure** — "my guess is", "I suspect". The
  hedge reports real uncertainty; do not hedge for politeness or effect
- **Humble about scope** — "not urgent, but since we're here we might as well
  fix it", "probably not worth as many words as I wrote"
- **A list for what is a list** — steps in order, parallel examples, independent
  reasons ("two independent reasons this is broken: 1. ... 2. ..."). Write them
  as a numbered or dashed list, not strung together as sentences in a paragraph
- **No markdown headers** in the commit body

### Paragraph Structure

When there is enough to say, the motive gets the most detail, and context or
history goes between it and the fix if it is needed.

Read the order as a description of a message whose facts were all available, not
as a template to fill. The number of paragraphs follows the number of things you
actually went and found out — see "How Long Should This Be?" below. Saying what
the code does today is not one of them. Where you write it, write it because the
message has to stand without the diff beside it, not because a paragraph wants
filling.

One paragraph, one topic. A paragraph of more than 5 sentences or more than
about 80 words that covers more than one topic is a block nobody reads: the
reader who needs one fact has to read all of it to find it. A topic is a part
that a reader can look for on its own: what the code does, what happens during
an operation, what happens after it, what a person must do, what it cannot do or
fix, or what was tried. Split such a paragraph where one topic ends and the next
begins. The counts are a reason to look, not a ceiling: one argument where each
sentence builds on the last, or sentences that each show how the change meets
one constraint, stays one paragraph however long it is.

A paragraph opens with its point. A run of sentences that each restate a hunk of
the diff, with none that says what they add up to, is the changelog of "What NOT
to Do" written as prose. Write the sentence that says what the hunks serve, from
the brief, and keep only the hunks it needs. If no entry gives that point, the
hunks are the ground: a sentence, not a paragraph.

A paragraph of one sentence that a split left is a question to ask. If it says
what the diff says and gives no reason, it is changelog and goes. If it is one
consequence of an idea the message never states, such as an invariant several
writers must keep, find that idea in the code or the brief and make it the topic
sentence of a paragraph that holds its consequences. If it belonged to the
paragraph it was cut from, put it back. Short paragraphs in the same form do not
become a list of what changed: that is the changelog "What NOT to Do" rules out.
Items that are a list on their own go in one, as "Tone" says.

### Sentences

Each sentence gives the reader something the diff does not: a reason, or a
consequence. Check every sentence against these, in the draft and again in a
reword:

- **Reason or consequence.** A sentence that names files, functions, flags or
  targets from the diff and gives no reason narrates the diff: "Add
  db-checkpoint (LABEL defaults to manual), db-checkpoints and db-drop." The
  reader has the diff. Attach the reason, or cut the sentence.
- **A behaviour needs its consequence.** "An empty path counts as unset" leaves
  the reader asking why it matters. Ask what goes wrong for a reader who does
  not know it, and write that ("an empty path counts as unset: SQLite would open
  a temporary database that vanishes on close"). If nothing goes wrong, cut it.
  A reason can be as vague as a behaviour: "the version matters" leaves the
  reader asking which version, and what happens. Write what happens: "when the
  lockfile pins a newer compiler than CI installs, the CI build fails". Each
  sentence says one thing a reader can check.
- **A number carries a decision.** "On the 7.4 GB database it held the write
  lock for about a minute. Reverts are rare, so that is fine." Lab notes, such
  as each run's timing, the run before, or a constant's name, go: the reader
  needs the conclusion ("writers wait until their timeout, or fail").
- **Nothing the reader cannot see.** A reason that points at something the
  reader cannot open — a discussion, a plan, an issue, a request, a design that
  never reached the history ("as discussed", "per issue 3f2a158", "the old rule
  compared sizes") — is no reason. Write the reason itself (checkpoints share
  the database's disk, so they do not survive it failing). The pointer does not
  go in the prose; an issue id can go in a trailer where the log carries them.
  If you do not know the reason, ask the user for it (for `peff-commit-auto` it
  is `unsourced`), and write nothing in its place.
- **A clear referent.** "It", "this" and "that" point to one noun, and the
  reader can tell which. "It takes the name from the real path" after a sentence
  about two things: name the thing. A conditional about a version the reader
  never saw ("Taken before the lock, a write would be in neither") needs that
  version stated, or it goes.
- **A real joint.** "And" adds a point of the same kind, "so" gives a
  consequence, "but" a contrast, "with" means "having". Two separate points
  joined by "and", "so" or a semicolon are two sentences. Ask of each joint what
  relation it states; if there is none, split it.
- **No filler.** Cut a sentence the reader would assume ("A checkpoint is only
  useful with a way back to it", "the tests pass") and a word that adds nothing
  ("only" in "only warns", "simply", "now" meaning "after this patch"). Cut an
  outcome that CI or the diff already shows, too: a lint, test or build that
  passes (see §5 of `COMPOSE.md`), or a file left untouched that nothing would
  have touched. Test it: delete the word or sentence; did the reader lose a
  fact?
- **Only what this commit does.** A sentence about a symptom must not read as if
  this commit fixes it. "That drift is why the generated parser differs between
  branches", in a commit that does not regenerate it, tells the reader that it
  does. Say what the commit changes, and state the symptom as context or not at
  all.
- **A stance where there is a cost.** Where the change gives something up, say
  in a sentence why that is acceptable: "A new patch release no longer reaches
  CI by itself. I think that is the lesser evil, because ...". Without it the
  reader cannot tell a cost you weighed from one you missed. Write the stance
  only when its reason has a source. Otherwise put the cost in the notes, saying
  what the change gives up and that the reason is missing, so that
  `peff-commit:review` can ask for it.
- **The conditions survive.** A sentence that condenses the code, a comment or a
  docstring keeps the condition ("fails when the checkpoint has no -shm", not
  "fails without a -shm"). Read the claim against the code, not your memory of
  it.

### How Long Should This Be?

Measured over 2000 of peff's commits, body length by size of diff (words,
excluding subject and trailers):

| diff size | n   | p25 | median | p75 |
| --------- | --- | --- | ------ | --- |
| 1-2 lines | 258 | 45  | 87     | 156 |
| 3-5 lines | 313 | 48  | 90     | 155 |
| 6-15      | 566 | 58  | 103    | 186 |
| 16-50     | 622 | 85  | 148    | 251 |
| 51-200    | 218 | 98  | 203    | 333 |

Peff writes about 87 words — two paragraphs — for a two-line diff. **Do not copy
that number.** It is the most misleading thing in this document if taken as a
target.

In his corpus, a small diff with a long message means the analysis was hard and
the fix turned out small. The words are a _record of findings_; the diff is
short precisely because the reasoning was long. His two-line changes are subtle
bugs he chased down. Yours are usually small because they are trivial.

Copy the length without the findings and there is only one way to reach it,
which is to invent. That is the failure this whole skill is built to prevent,
and it enters right here — through a well-meant attempt to sound like these
numbers. Length is downstream of what you know. Establish the facts, then let
them determine the size.

Short is normal, including for him: 12% of these bodies are under 40 words.

### Discussing Alternatives

A distinctive peff pattern: explain approaches you considered but didn't take,
and why. This proves you understand the design space, not just the diff.
Examples from real patches:

> One option to prevent this is to limit the depth of recursion we'll allow.
> This is conceptually easy to implement, but it raises other questions: what
> should the limit be, and do we need a configuration knob for it?

> It would be easy-ish to insert an extra check like:
> `can_filter_bitmap(&opt->objects_filter);` into the conditional, but I didn't
> bother here. It would be redundant with the call in
> for_each_bitmapped_object(), and the can_filter helper function is static
> local in the bitmap code.

Both are quoted for what they weigh, not for their order: each opens with the
alternative, where "Body: Narrative Prose" puts it after the choice that beat
it.

You don't need to manufacture alternatives — but when you genuinely considered
another approach, say so and say why you didn't take it.

### Quantitative Evidence

When the change has measurable impact, include the numbers. Peff frequently
embeds benchmark output, object counts, or timing data directly in the commit
body. The data grounds the reasoning in reality rather than hand-waving about
performance. Each number backs a conclusion the message states; see "A number
carries a decision" under "Sentences".

### Emphasis and References

- Uses _italics-style_ emphasis sparingly for subtle distinctions (rendered in
  email as underscores: "dispatched _from_")
- References other commits by abbreviated sha, subject and date, as
  `git show -s --format=reference <sha>` prints them: "1f3fd68e06 (odb/source:
  make read_object_stream() pluggable, 2026-03-05)". Never a bare sha: the
  reader needs the subject to know what it was. Keep the reference inside a line
  that flows, not on a line of its own. Only a commit that has reached the
  mainline gets one. Anything short of that, the commits of your own branch
  included, is named by position ("the previous commit", "the next commit"),
  because a rebase will have changed its sha
- References related discussion: "This was caught during review of ..."
- Links to a source that stays put, not one that will have changed by the time
  the link is read (e.g. a specific release, not the page of all releases)
- Credits others when their report or review led to the fix

Some rules here are this skill's, not peff's: never a bare sha, the link that
stays put, and this one. Quote a sentence or more of someone else's words (a
reviewer, a bug report) in a block of its own, with each line starting `> ` as
mail quotes do, after a line that names who said it. A quote in mid-sentence
buries both the words and the point. A quoted term, message or command
("database is locked"), a few words, and text from a spec or standard stay
inline.

The user is not someone else: the commit is authored as them. Do not quote them
in the message or write "the user said"; say what they said as the author's own
reasoning. Their words, quoted, go in the notes.

## What NOT to Do

- No bullet-point changelogs ("- changed X", "- added Y"). A list of steps or of
  parallel items is not one; see "Tone"
- No "This commit does X" self-referential framing
- No JIRA ticket numbers in the subject (put in footer if needed)
- No emoji
- No "Fixes #123" GitHub shorthand in the body (reference PRs by URL or prose
  instead)
- No restating what the diff already shows — explain the WHY
- No motivation you cannot source. If nothing in the diff, the code, the log,
  the session, or an issue says why this change is being made, the message does
  not say why. It is not improved by a guess, and it is not rescued by hedging
  the guess — "I suspect this improves performance" asserts a finding while
  looking like calibration, so the reviewer believes it and cannot tell it apart
  from a real one. Omit it, and put the assumption in the notes
- No false confidence — where you did investigate a mechanism and came away
  unsure, say so. That hedge reports work you actually did, which is the
  opposite of the one above
- No editorializing asides ("Amusingly, ...", coined maxims, "Two asides.").
  Peff's asides report his own effort, confidence, or scope ("not urgent", "I
  punted on it for now") — they tell the reviewer how much scrutiny to apply. An
  aside that is wit about the subject gets deleted
- No decorating numbers ("voted 13-to-1") — write the plain count ("13 of 14")

## Closing

Peff ends with a `Signed-off-by:` line, but not by personal style — the Git
project requires that trailer of every submission, from anyone. Follow the same
logic rather than the letter of it: add whatever trailer the _target_ project
requires, which for most repos means matching what the recent log carries (sign
off where it signs off, carry a `Reviewed-by:` or ticket trailer where the log
carries one, add nothing where the log carries nothing).

That's a question about the repo's requirements, not about who or what wrote the
message. If an LLM drafted the commit, say so with its own trailer:

```
Generated-by: Claude (claude-opus-5)
```

The parentheses hold the model id and nothing more: no branch, session or
ticket. A rule elsewhere in the project that adds those to its own attribution,
for issues say, does not carry over to this trailer.

Never fold that fact into `Co-authored-by:` or a human's `Signed-off-by:`. Both
of those assert something the model didn't do — joint authorship, or a person's
review and sign-off — and `Generated-by:` says the true thing instead: a model
produced the text. If the harness tells you to append a `Co-Authored-By:` line,
`Generated-by:` replaces it while this skill is in use.

If the change is a port of a fix from elsewhere, say so plainly: "Apply the same
fix here."

## Notes

Notes are observations that sit alongside the commit message but aren't part of
it. They surface your reasoning, uncertainties, and caveats — the things that
help a reviewer (or your future self) understand not just what you decided, but
what you were thinking.

**Formatting:** notes are stored verbatim by `git notes` and read in a terminal,
so format them exactly like commit body prose: aim for 72 characters per line
(soft limit), hard limit 120. No markdown. Paragraphs separated by a single
blank line. A dense paragraph is split into paragraphs, or into a list where its
items are one (see "Tone"). A person's words, the user's included, go in a
mail-style `> ` quote (see "Emphasis and References").

Use notes for:

- **Alternatives not taken** — why another approach was tempting but wrong
- **Caveats** — things that are still ugly or incomplete
- **Uncertainties** — things you're not confident about
- **Scope decisions** — why you stopped where you did

From peff's real patches:

> It would perhaps make more sense for diff-highlight to chomp all incoming
> lines, then do its comparisons, and then add a newline back on output. That's
> a bigger change, so I punted on it for now.

> I think the rewrite of xmkstemp() triggered Coverity to consider this a "new"
> problem, even though it has been there for years. So not urgent, but this is
> mostly just trying not to waste the brain cycles I spent analyzing. :)

The notes are the reasoning checkpoint. If someone reads your notes and thinks
"wait, that alternative is actually better" or "that's not why we're doing
this", it surfaces the misunderstanding before it gets committed.

## Examples of Good Final Paragraphs

```
This could easily be fixed by chomping the prefix, too, but I think the
problem is deeper. [...] So let's catch this early in
is_pair_interesting() and bail to our usual passthrough strategy.
```

```
So we know that bitmaps help when there's filtering to be done, but
otherwise make things worse. Let's only use them when there's a filter.
```

```
The recursion here is simple enough that we can avoid those questions by
just converting it to iteration instead.
```

These are quoted for how they close. The first opens with the alternative, which
"Body: Narrative Prose" puts after the choice that beat it, and the third's
"just" is filler by "Sentences".
