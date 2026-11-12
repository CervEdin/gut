---
name: comment-review
description: >-
  Review the comments, API docs, directives and touched docs in a diff or patch
  series: which text to delete, which to move to the commit message, the use
  site, the definition or code, and which must stay. Use after writing code and
  before committing or sending, especially code an agent wrote, or when asked
  whether a comment belongs, is too much, or is in the wrong place. Also use
  when tidying a branch for review and its diff adds comments, even if the user
  does not mention them.
disable-model-invocation: false
---

# comment-review

Agents leave notes in source while they work: what they changed, why, what it
replaced. That is reasoning leaking out of the context into the result. Each
such comment costs every future reader of the line, and the noise hides the few
comments that matter.

Each piece of explanation has a place, and each place has its own readers:

    code (names, types, assertions)   every reader, with no prose to read
    comment on the line               every reader of the line, every time
    API doc, first sentence           everyone who looks up the symbol
    API doc, body and examples        whoever is about to call it
    standalone docs                   whoever opens them
    commit message                    only whoever runs log, blame or log -L
    below the --- line                the reviewers of this round, then gone

Put text in the place that reaches the readers who need it and spares the rest.
For a comment, ask: does every reader of this line need it at first glance, and
can no other place give it to the readers who ask? Staleness and upkeep add to a
comment's cost, but who reads it decides where it goes.

The commit message is the only place for _why now_: why this change was made,
what it replaced, what was tried. It is not the default place for everything. A
lasting reason why the code is the way it is can stay a comment. The Git project
is a fair calibration: its source has comments, and the why of each change is in
its log.

When a finding needs backing, quote `COMMENT-SOURCES.md`. It has the sources
behind most checks and lists the ones that have none.

## Process

1. **Get the commits.**
   - "Review this branch" or "my changes": `git log -p origin/HEAD..HEAD`. If
     `origin/HEAD` is not set, ask for the base.
   - A PR: fetch it as the host requires, then read its commit range the same
     way.
   - Only staged changes: `git diff --cached`.
   - Nothing obvious: ask what to review.

2. **Ask whether each commit should be one.** Ask when the commit is big on both
   counts: its diff changes more than about 200 lines of code (added plus
   removed, not counting tests, docs, translations or generated files) and its
   message body is longer than about 1,000 characters (not counting the subject
   or trailers). At any size, also ask when its message describes more than one
   change. Size is a reason to ask, not a limit.
   - One count alone is not a reason. A big diff with a short message is usually
     mechanical: a rename, a reindent, generated code. A long message on a small
     diff is usually a subtle fix that needs the words.
   - The test: does the commit hold logically separate changes, each with its
     own why, that can go in as a series where each part builds and passes the
     tests (where the project has them) with the parts before it applied? One
     change made to many files stays one commit.
   - If no such series exists, the commit stays one. Say nothing.
   - If one does, the output opens that commit with a **Split:** block (see
     Output Format). The split matters more than the comment findings on the
     commit, so it comes first. Still review the comments, and tag each finding
     with the part that will hold its line.
   - Only staged changes: there is no message. Ask when the code diff is over
     about 200 lines, or when it holds more than one change.

3. **Collect the text, per commit.** Read each file as it is at that commit
   (`git show <commit>:<path>`, or `git show :<path>` when only staged), not
   from the working tree.
   - Comments and doc comments on added lines.
   - Comments in the whole enclosing function, struct or class, not only the
     diff's context lines: check these only for staleness caused by this patch.
   - Comments anywhere that name an identifier the patch renames or removes
     (grep for it).
   - Comments the patch removes: check that nothing a reader needs went with
     them.
   - Doc files the patch touches.
   - The paragraphs of the commit message, for step 9 only.
   - Do not audit the rest of the file.

4. **Classify each piece.**
   - **Directive**: comment syntax that a tool reads. `// SAFETY:`,
     `//go:build`, `# type: ignore`, `# noqa`, `//nolint`,
     `// eslint-disable-next-line`, `// @ts-expect-error`, `# pragma: no cover`,
     `/* fallthrough */`, `SPDX-License-Identifier:`, comments a project linter
     requires (checkpatch wants one on each memory barrier). Extend the list
     from the project's lint config and the tools it runs. Go to step 7.
   - **API doc**: Javadoc, docstring, header doc, `--help` text. Go to step 6.
   - **Commented-out or debug code**: `delete`.
   - **Working note** ("change needed", "related to XYZ", "added this because"):
     its why-now part is `move-to-log`. Strip the narration and the why-now
     part, and run what is left through step 5. If nothing is left and there was
     no why-now part either, the note is `delete`. Text meant only for this
     round's reviewers ("as suggested in v2") goes below the `---` line:
     `move-to-log`, naming that place. If the work is real, a labelled
     `TODO`/`NEEDSWORK` with a ticket may replace the note.
   - **Prose comment**: step 5.

5. **Prose comments.** Run the keep check first, then the rest in order. The
   first check that fires gives the verdict.
   - **Keep check.** First say what `git blame` on the line shows: the commit
     that added it, and whether its message gives the reason. Then read the code
     without the comment. Does it tempt a competent editor into a change that
     breaks it, because it looks redundant, like a no-op, like a hack or like an
     arbitrary order, and nothing in the code says otherwise? Name that change.
     Invariants, lock and ordering rules, lifetimes, why a race is harmless,
     hardware or spec quirks and constraints from systems outside this repo
     often hide such a trap. Code that states its purpose does not: a check that
     fails with an error message, an assertion, a usage line. Nobody removes an
     explicit refusal without asking why, and blame answers them, so the reason
     for it is `delete` when the commit message gives it and `move-to-log` when
     it does not. That holds only while the refusal looks needed. When something
     else seems to do its job already, such as a call that looks like it fails
     the same way or a caller that looks like it checks first, removing the
     refusal is the tempting change. Do not assume that working code gets tidied
     away at random: if you cannot name the tempting change, the check does not
     fire.
     - **A test first.** If the check fires, ask whether a test can guard the
       code in place of the comment: one that fails when someone makes that
       change, on the machines that run the tests. A comment warns only whoever
       reads it; a test stops the change.
       - A test already fails on that change: `delete`, naming the test.
       - A test could be written: `replace`, put to the author as "Can we guard
         this with a test instead of a comment?", with the test, named for the
         rule it holds. The comment goes once the test exists, with its reason
         in the commit message.
       - None of these rules a test out: the other side of a contract is outside
         the repo (test this side's half, such as that a file is renamed into
         place only after it is complete); the code drives hardware or another
         system (a fake clock or device stands in); the code has no seam, such
         as a hardcoded path (propose the seam with the test); the repo has no
         tests yet (propose the first).
       - A test that passes either way does not count, such as one for a Windows
         quirk that only runs on Linux.
     - **Keep** only when nothing this repo's code does shows the trap to a
       test, and say what a test would have to see. Then skip the other checks
       except for these findings: `rewrite` if the comment is wrong,
       `move-to-log` for a sentence in it that only makes sense next to the
       diff, a form `Nit:` from the survivor check, and step 9. Do not move the
       lasting part to the log: the change it guards against looks safe, so
       whoever makes it has no reason to run `blame` first.
   - **Wrong or stale**: it does not match the code after the patch. `rewrite`
     or `delete`, to fix before sending. A reader trusts a comment over the
     code, so this is not a `Nit:`, however small the wording change.
   - **Why now**: it only makes sense to someone who saw the diff or the old
     code. It compares with an earlier version ("no longer", "changed to", "now"
     meaning "since this patch"), or it gives the motive for the change, not for
     the code as it stands. "Now" meaning "at this point in the function" does
     not count. `move-to-log`. If the commit message already says it, the
     verdict is `delete` instead; report and count it only as `delete`.
   - **Cites what the reader cannot see**: a reason that points at something the
     reader cannot open — a discussion, a plan, an issue, a request, a design
     that never reached the history ("as discussed", "per issue 3f2a158", "the
     old rule compared sizes") — is no reason. Write the reason itself
     (checkpoints share the database's disk, so they do not survive it failing).
     If it still holds for the code as it stands, `rewrite` the comment to state
     it. If it only explains the change, `move-to-log`, with the reason written
     out. The pointer does not go in the comment or in the commit-message prose;
     an issue id can go in a trailer where the log carries them. If you do not
     know the reason, ask the author for it, and write nothing in its place, in
     the comment or the commit message.
   - **No consequence**: it states a behaviour, and "an empty path counts as
     unset" leaves the reader asking why it matters. Ask what goes wrong for a
     reader who does not know it, and `rewrite` with that ("an empty path counts
     as unset: SQLite would open a temporary database that vanishes on close"),
     then run the keep check on the result. If nothing goes wrong, `delete`.
   - **Restates**: it repeats the name, the signature, the path, or what the
     language does, or it takes longer to read than the code it describes.
     `delete`.
   - **grep answers it**: callers, users, who shares a file. `delete`.
   - **Wrong place in the code**: ask who must obey it and who changes when it
     changes. A rule that binds every caller goes on the definition. A reason
     that one call site has goes at that call site. `move`.
   - **Code could say it**: a precondition becomes an assertion; a "what"
     comment becomes a name; a comment that explains the same check at more than
     one site becomes a helper whose name says it. A new name does not replace a
     comment that states an assumption or limitation. An assertion replaces a
     comment only if it checks at least what the comment says; Python's
     `threading.Lock` has no owner, so "caller must hold the lock" stays a
     comment there. `replace`, with the code.
   - **Repeated**: prose that cannot become code, at three or more places,
     counting copies the patch adds and copies a grep finds. Keep it at the
     definition, or at one site if the definition is outside this repo; at most
     a one-line pointer elsewhere; `delete` the rest.
   - **Survivor**: `keep`. Check its form against the file's own convention: the
     constraint in the first line, the point first and a caveat or the rejected
     alternative after it, no narration ("we then loop"), no "I", "we" only
     where the file already uses it, no clause that restates the sentence, no
     volatile section numbers. Form findings are `rewrite` with `Nit:`.

6. **API docs.**
   - The first sentence gives the gist to a reader who stops there.
   - The body gives the contract: calling context (threads, locks, blocking),
     failure modes, then an example if the signature does not show the use.
   - No rationale and no history; those go to the log.
   - Mood, person and doc marker follow the file.
   - Class and module docs follow these rules too. A list of who uses the class
     is a "grep answers it" `delete`.
   - A doc on an obvious member or class: `delete`, unless the file documents
     every one; then `keep`.
   - `missing`: an externally called symbol with a contract the signature does
     not show and no doc. Private symbols only when the file documents them.

7. **Directives.** The questions above do not apply.
   - Still needed? A stale suppression hides a real warning: `delete`. Judge by
     reading the code; do not run the tool. If only running it would settle the
     question, say so in the finding.
   - Scoped as tightly as the tool allows (next line over whole file, one rule
     over all)? If not, `rewrite`.
   - Free text after the tag (the reason after `SAFETY:`, the pairing note on a
     barrier): check that it is true and names what it relies on. `rewrite`
     only: the tag or its linter requires the text, and a bare tag tells the
     next reader nothing.

8. **Touched docs.** Common case first; an example where one helps; text for
   removed behaviour removed; active voice, short sentences. Text that is wrong
   after the patch gets `rewrite` or `delete`; the rest are `rewrite` with
   `Nit:`.

9. **Dense paragraphs and inline quotes.** Run this on each paragraph that the
   patch adds or changes, including those the keep check kept, and on each
   paragraph of the commit message. A paragraph is a run of lines with no blank
   line between them. A line that holds only the comment marker (` *`, `//`,
   `#`) counts as blank, and a list item ends the paragraph.
   - **Dense**: in the commit message, the paragraph covers more than one topic,
     however short it is, and more than 5 sentences or about 80 words is a
     reason to look for a second topic. In a comment, only a paragraph past
     those counts that covers more than one topic is dense. A topic is a part
     that a reader can look for on its own: what the code does, what the change
     does, how it does it or at what cost, what happens during an operation,
     what happens after it, what a person must do, what it cannot do or fix, or
     what was tried. One argument where each sentence builds on the last, or
     sentences that each show how the change meets one constraint, stays one
     paragraph.
   - **Inline quote of a person**: a sentence or more of someone else's words (a
     reviewer, a bug report) inside a sentence of the text. It goes on its own
     lines as a `> ` block quote, after a line that names who said it. A quoted
     term, message or command ("database is locked"), a few words, and text from
     a spec or standard stay inline.
   - **Quote of the author**: the commit is authored as the user, so their words
     in its message, quoted or not, read as the author quoting themselves.
     `rewrite`: say it as the author's own reasoning, in the message's voice,
     and move the quote to the notes if it is worth keeping.
   - Verdict: `rewrite`, without `Nit:`: a reader who needs one fact should not
     have to read another topic to find it.
   - Replacement: the paragraph split where one topic ends and the next begins,
     so that each part says one thing and keeps its reason. Use a bold lead-in
     where the file uses them. A list is only for items that are a list on their
     own, such as cases or commands that each carry their own reason. Short
     paragraphs in the same form do not become a list: a list of what changed is
     a changelog.
   - Then reread the replacement as a whole, as a reader would. A paragraph of
     one sentence that the split left is a question, not a shape to fix:
     - It says what the diff says and gives no reason. It is changelog: drop it.
       In a commit message, the one sentence that states the fix stays.
     - It is one consequence of an idea that the text never states, such as an
       invariant that several writers must keep. Find the idea in the code, its
       comments or the commit message, and write it as the topic sentence of a
       paragraph that holds its consequences. If nothing states it, say so and
       ask; do not invent it.
     - It is on the same topic as the paragraph it was cut from: undo that part
       of the split. A one-sentence paragraph on a topic of its own stays.
   - End each step 9 finding with this line for whoever applies it: "Rewrite the
     paragraph, then reread the whole comment (or message) as a reader before
     committing." The replacement shows one shape. Whoever applies it rewrites
     the paragraph so it reads well, rather than pasting the split.
   - When another check also fires on the paragraph (a sentence goes to the log,
     a clause is wrong), give one replacement under that check's verdict, and
     say that step 9 also applies.

## Output Format

Per commit, in diff order, laid out like the persona reviews so the outputs can
be read side by side:

> ### [PATCH N/M] `<subject line>`
>
> **Split:** only when step 2 finds a series. What made you ask (the size, or
> the changes the message lists), then the parts, in order. For each part: a
> subject line, what it holds, which paragraphs of the current message go with
> it (none when only staged), and its tests. Say which parts depend on which.
>
> A step 9 finding in the commit message goes before the file findings, as **On
> the commit message, paragraph N:**
>
> **On `<file>:<line>`:** after a **Split:** block, add the part:
>
> **On `<file>:<line>` (part 2):**
>
> ```
> (quoted comment and the code around it)
> ```
>
> `<verdict>:` which check fired, then where the text still reaches its readers:
> "the commit message gives this to whoever runs blame; no reader of the line
> needs it unasked". Then the replacement: the new comment, the code, or the
> commit-message paragraph. A plain `delete` needs no replacement.
>
> **For the commit message:** the `move-to-log` paragraphs for this commit, or
> for each part after a **Split:** block, ready to paste into a reword, and any
> text for below the `---` line, marked as such. In staged-only mode, one block
> at the end. When a step 9 finding is on the commit message, end the block with
> "Rewrite the paragraphs, then reread the whole message as a reader before
> committing.", even if that line is all the block holds. Otherwise leave the
> block out when there is nothing to add.
>
> ---
>
> **Summary:** first `Split: N parts` for each commit with a **Split:** block.
> Then the count per verdict, with `Nit:` findings counted apart. `keep` is not
> a finding and is not counted.
>
> **Outside this review:** one line per code issue you noticed that is not about
> a comment, such as a missing lock. These are not findings.

For example, a working note that hides a lasting reason:

> **On `parse.c:88`:**
>
> ```c
> /* Added this because the parser points into buf until parse_end(). */
> parse_end(p);
> free(buf);
> ```
>
> `rewrite:` working note. "Added this because" is narration and goes. The rest
> passes the keep check: blame gives the reason, but freeing `buf` first looks
> like a harmless reorder, and nothing in the code says otherwise. Replacement:
> `/* The parser points into buf until parse_end(). */`

The review follows step 9 itself: when it quotes a person (the user, a
reviewer), the quote goes in a `> ` block quote on its own lines, not inside a
sentence.

Verdicts: `delete`, `move-to-log`, `move`, `replace`, `rewrite`, `missing`.
Form-only findings carry `Nit:`, except those of step 9; no other findings do.
Mention `keep` only where another reviewer might be tempted to remove the
comment, or where you were unsure; then say what you were unsure of.

## Important

- **Name the place.** Every `delete` and `move-to-log` names where the
  information still reaches the readers who need it: code, grep, the log, the
  definition. A wrong comment or dead code names the code that contradicts or
  replaces it. If you cannot name one, the verdict is `keep`.
- **Words that suggest keep.** Lock, ordering, race, pairs with, erratum,
  workaround, upstream and spec often mark a comment that passes the keep check.
  When one appears, run the keep check against the code, not the word: "in order
  to" and "pathspec" do not count, and a sentence that only makes sense next to
  the diff still goes to the log. When unsure, name the change the comment
  guards against and say what blame shows; `keep` when that change looks safe
  without the comment and no test can catch it.
- **Do not invent the why.** A commit-message paragraph carries only what the
  comment or the diff already says. If the reason is unknown, say so and ask. A
  sentence that condenses the code, a comment or a docstring keeps the condition
  ("fails when the checkpoint has no -shm", not "fails without a -shm"). Read
  the claim against the code, not your memory of it.
- **Name the check, not the author.** Do not say a comment "sounds like AI".
- **Review the commit message only for step 9.** Otherwise read it only to
  choose between `delete` and `move-to-log`, and for the split check in step 2.
  Its narrative and wording belong to peff-commit, sunshine-review and
  gitster-review.
- **Respect patch scope.** Comments the patch does not touch are out of scope,
  unless the patch makes them wrong.
