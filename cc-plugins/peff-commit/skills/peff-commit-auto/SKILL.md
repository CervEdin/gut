---
name: peff-commit-auto
description: >-
  Write or rewrite a commit message in the style of Jeff King (peff) without
  interrupting the user — gathers the evidence behind the change, writes only
  what it can actually source, and records everything it had to assume as git
  notes rather than asserting it in the message. Use it for committing your own
  work mid-task, and whenever you reword, split, review or revise an existing
  commit message, yours or another session's, including each round of edits on
  the user's review of a message. /peff-commit is the user's own entry point,
  which interviews them about the gaps; a model cannot invoke it.
disable-model-invocation: false
---

# peff-commit-auto

Channel Jeff King (peff) — prolific Git contributor — when writing commit
messages, without stopping to ask anyone anything.

Use this when you reached for the skill yourself, mid-task: you have just
finished some work and want it committed. The user may be away, and stopping an
unattended run to ask why the change is being made is exactly the friction that
makes a commit step not worth having.

Revising a message is writing one. When the user reviews commit messages and
asks for changes, each round is a reword: it runs this process, with the brief,
not a prose edit of the old text.

The user is probably not watching. When you reach for this mid-task they may be
away from the keyboard, or working in another session entirely, so a question
does not come back quickly — it parks the work until they return. That is the
whole reason this skill does not ask.

**Never ask the user a question from this skill.** If a gap needs their input,
the gap goes in the notes and the commit proceeds. `git commit --amend` is
cheap, and a note saying "assumed X" is a thing they can correct in ten seconds.
A body asserting X is a thing they have to notice first.

## Process

1. **Gather.** Invoke the `commit-brief` skill. It writes `.git/commit-brief`
   and reports which entries came back `unsourced`.

2. **Quarantine.** Every `unsourced` entry stays out of the commit body, without
   exception, and goes into the notes marked as an assumption:

   ```
   Assumed, not sourced: this drops the retry because the caller already
   retries. Nothing in the diff, the log, or the session says so.
   ```

   A reason from a plan or another agent that `commit-brief` could not check is
   one of these. Name where it came from, so that the user can confirm it before
   it goes into the body:

   ```
   Assumed, not sourced: the review agent says the next commit puts this rule
   in front of every load. Not checked against the next commit.
   ```

   Do not launder an assumption into the body by hedging it. "I suspect this
   improves performance" is the same invention wearing a disclaimer, and it
   reads as calibration — the reviewer takes it as a real if tentative finding,
   which is precisely the failure.

   Do not go looking for a different reason to say instead. If `incident` is
   unsourced, the message simply does not state why the change was made. That is
   an accurate message.

3. **Compose, check, commit.** Follow `../peff-commit/COMPOSE.md`: budget, draft
   from the brief, check (brief lint, the provenance file with its coverage
   section, budget and paragraphs, commit references, line length, slop score),
   commit, notes, report. `../peff-commit/PEFF-STYLE.md` carries the voice, and
   the scorer is at `../peff-commit/scripts/slop_score.py` — all three live in
   the `peff-commit` skill directory alongside this one.

   To rewrite the messages of existing commits, follow "Rewording existing
   commits" in `../peff-commit/COMPOSE.md`. This skill is the one to use when
   you reword your own commits; `peff-commit` cannot be invoked by a model.

   With `incident` quarantined the finding count is usually low, so the budget
   is usually one paragraph or none. Let it be short. Saying what the code does
   today and what changes, and stopping there, is the correct output for a
   change whose reason is not recorded anywhere; 12% of peff's real commit
   bodies are under 40 words.

4. **Report**, leading with the **Assumed, not sourced** section. That section
   is why this skill is allowed to run without asking: it moves the interview
   after the commit instead of deleting it. It lists reasons to verify, not
   things to do; those go under **To decide** (see §6 of `COMPOSE.md`).
