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

## Process

1. **Get the commits.**
   - "Review this branch" or "my changes": `git log -p origin/HEAD..HEAD`. If
     `origin/HEAD` is not set, ask for the base.
   - A PR: fetch it as the host requires, then read its commit range the same
     way.
   - Only staged changes: `git diff --cached`.
   - Nothing obvious: ask what to review.

2. **Collect the text, per commit.** Read each file as it is at that commit
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
   - Do not audit the rest of the file.

3. **Classify each piece.**
   - **Directive**: comment syntax that a tool reads. `// SAFETY:`,
     `//go:build`, `# type: ignore`, `# noqa`, `//nolint`,
     `// eslint-disable-next-line`, `// @ts-expect-error`, `# pragma: no cover`,
     `/* fallthrough */`, `SPDX-License-Identifier:`, comments a project linter
     requires (checkpatch wants one on each memory barrier). Extend the list
     from the project's lint config and the tools it runs. Go to step 6.
   - **API doc**: Javadoc, docstring, header doc, `--help` text. Go to step 5.
   - **Commented-out or debug code**: `delete`.
   - **Working note** ("change needed", "related to XYZ", "added this because"):
     its why-now part is `move-to-log`. Strip the narration and the why-now
     part, and run what is left through step 4. If nothing is left and there was
     no why-now part either, the note is `delete`. Text meant only for this
     round's reviewers ("as suggested in v2") goes below the `---` line:
     `move-to-log`, naming that place. If the work is real, a labelled
     `TODO`/`NEEDSWORK` with a ticket may replace the note.
   - **Prose comment**: step 4.

4. **Prose comments.** Run the keep check first, then the rest in order. The
   first check that fires gives the verdict.
   - **Keep check.** Would a competent editor of the current code break
     something without this comment, and not think to look it up? Invariants,
     lock and ordering rules, lifetimes, why a race is harmless, hardware or
     spec quirks, constraints from systems outside this repo, traps that a
     reasonable cleanup would fall into. If yes: `keep`, and skip the other
     checks except for three findings: `rewrite` if the comment is wrong,
     `move-to-log` for a sentence in it that only makes sense next to the diff,
     and a form `Nit:` from the survivor check. Do not move the lasting part to
     the log: whoever tidies the code will not run `blame` first.
   - **Wrong or stale**: it does not match the code after the patch. `rewrite`
     or `delete`, to fix before sending. A reader trusts a comment over the
     code, so this is not a `Nit:`, however small the wording change.
   - **Why now**: it only makes sense to someone who saw the diff or the old
     code. It compares with an earlier version ("no longer", "changed to", "now"
     meaning "since this patch"), or it gives the motive for the change, not for
     the code as it stands. "Now" meaning "at this point in the function" does
     not count. `move-to-log`. If the commit message already says it, the
     verdict is `delete` instead; report and count it only as `delete`.
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
     constraint in the first line, no narration ("we then loop"), no "I", "we"
     only where the file already uses it, no clause that restates the sentence,
     no volatile section numbers. Form findings are `rewrite` with `Nit:`.

5. **API docs.**
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

6. **Directives.** The questions above do not apply.
   - Still needed? A stale suppression hides a real warning: `delete`. Judge by
     reading the code; do not run the tool. If only running it would settle the
     question, say so in the finding.
   - Scoped as tightly as the tool allows (next line over whole file, one rule
     over all)? If not, `rewrite`.
   - Free text after the tag (the reason after `SAFETY:`, the pairing note on a
     barrier): check that it is true and names what it relies on. `rewrite`
     only: the tag or its linter requires the text, and a bare tag tells the
     next reader nothing.

7. **Touched docs.** Common case first; an example where one helps; text for
   removed behaviour removed; active voice, short sentences. Text that is wrong
   after the patch gets `rewrite` or `delete`; the rest are `rewrite` with
   `Nit:`.

## Output Format

Per commit, in diff order, laid out like the persona reviews so the outputs can
be read side by side:

> ### [PATCH N/M] `<subject line>`
>
> **On `<file>:<line>`:**
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
> **For the commit message:** the `move-to-log` paragraphs for this commit,
> ready to paste into a reword, and any text for below the `---` line, marked as
> such. In staged-only mode, one block at the end. Leave the block out when
> there is nothing to add.
>
> ---
>
> **Summary:** count per verdict, with `Nit:` findings counted apart. `keep` is
> not a finding and is not counted.
>
> **Outside this review:** one line per code issue you noticed that is not about
> a comment, such as a missing lock. These are not findings.

For example, a working note that hides a lasting reason:

> **On `parse.c:88`:**
>
> ```c
> /* Added this because the parser returns NULL on empty input. */
> if (!node)
> 	return 0;
> ```
>
> `rewrite:` working note. "Added this because" is narration and goes; the rest
> passes the keep check, since a cleanup would drop the NULL check without it.
> Replacement: `/* The parser returns NULL on empty input. */`

Verdicts: `delete`, `move-to-log`, `move`, `replace`, `rewrite`, `missing`.
Form-only findings carry `Nit:`, and no others do. Mention `keep` only where
another reviewer might be tempted to remove the comment, or where you were
unsure; then say what you were unsure of.

## Important

- **Name the place.** Every `delete` and `move-to-log` names where the
  information still reaches the readers who need it: code, grep, the log, the
  definition. A wrong comment or dead code names the code that contradicts or
  replaces it. If you cannot name one, the verdict is `keep`.
- **Words that suggest keep.** Lock, ordering, race, pairs with, erratum,
  workaround, upstream and spec often mark a comment that passes the keep check.
  When one appears, run the keep check against the code, not the word: "in order
  to" and "pathspec" do not count, and a sentence that only makes sense next to
  the diff still goes to the log. A wrong deletion costs more than a kept
  comment; when unsure, `keep`.
- **Do not invent the why.** A commit-message paragraph carries only what the
  comment or the diff already says. If the reason is unknown, say so and ask.
- **Name the check, not the author.** Do not say a comment "sounds like AI".
- **Do not review the commit message itself.** Read it to choose between
  `delete` and `move-to-log`. Its narrative and wording belong to peff-commit,
  sunshine-review and gitster-review.
- **Respect patch scope.** Comments the patch does not touch are out of scope,
  unless the patch makes them wrong.
