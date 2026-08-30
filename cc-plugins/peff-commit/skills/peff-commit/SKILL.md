---
name: peff-commit
description: >-
  Write a commit message in the style of Jeff King (peff) from the Git mailing
  list — narrative prose that says why the change was made, and git notes
  recording what was uncertain about it. Gathers the evidence first and
  interviews you about whatever it could not source, so the message reports your
  reasons rather than plausible ones. Use it whenever a commit message is about
  to be written or rewritten: committing staged work, amending or rewording an
  existing message, or fixing up a series before it is sent.
disable-model-invocation: true
---

# peff-commit

Channel Jeff King (peff) — prolific Git contributor — when writing commit
messages. The persona is the steering mechanism: peff's voice produces messages
that explain a mechanism, discuss alternatives, and stay honest about
uncertainty. The goal is not impersonation.

But the voice alone is not the discipline, and on its own it is actively
dangerous: style is the easiest thing in the world to reproduce, and a message
with peff's cadence and an invented reason is indistinguishable at a glance from
one with peff's cadence and a real reason. So the reasons come first, from
`commit-brief`, and from you where the repository cannot supply them.

You invoked this by hand, which means you are here and can be asked. That is the
whole reason this skill exists separately from `peff-commit-auto`: it spends a
question of your time to avoid guessing.

## Process

1. **Gather.** Invoke the `commit-brief` skill. It writes `.git/commit-brief`
   and reports which entries came back `unsourced`.

2. **Interview.** If any entry is `unsourced`, ask — one batched
   `AskUserQuestion`, never a series.

   `incident` gets asked every time it is `unsourced`. Every `AskUserQuestion`
   needs at least two options besides the automatic "Other," but for `incident`
   those options must be neutral escapes ("nothing," "not sure," "skip") rather
   than a guessed narrative — the real answer belongs in "Other," typed, not
   clicked. A guessed motive that "sounds right" and gets a click is a
   confabulation wearing a human's sign-off — worse than an honest gap, because
   it now looks sourced. Ask whichever of these bear on the change:

   - What happens if this never merges — what stays broken or unbuilt?
   - What happens if it ships later than planned — who or what is stuck waiting
     on it in the meantime?
   - Who asked for this, and why? ("nobody, I noticed it" is a real answer.)
   - Is there a business reason — an external stakeholder, deadline, or system
     that depends on this? A change that mirrors existing code, or is "more
     consistent," is a reason about the code, not about the business; it does
     not answer this question.

   `AskUserQuestion` allows at most four questions per call, and the four above
   can fill it on their own. When they do, `alternatives`, `deferred`, and
   `uncertain` stay `unsourced` this round rather than spilling into a second
   call — that is what "one batched call, never a series" means in practice.
   This matches `commit-brief`'s own rule that an absent
   `alternatives`/`deferred` is the ordinary case, not a gap to chase. Only
   spend a slot on one of those three if an incident question goes unused.

   Other unsourced fields (`alternatives`, `deferred`, `uncertain`), when a slot
   is available, can offer your candidate readings as clickable options plus
   "Other" and an explicit "go with your read" escape, so answering those is a
   click rather than an essay — unlike `incident`, a wrong guess here just gets
   corrected via "Other," not silently accepted as a motive.

   The trigger is the tag in the file, not your sense of whether the motivation
   feels recoverable. That judgment is what this skill used to make, and it made
   it wrong nearly every time: a transcript almost always contains something
   that pattern-matches a reason, so the bar was never met and the question was
   never asked.

   Record each answer in the brief as `asked`, with the question as its
   citation. Answers count as load-bearing facts, so asking widens the budget in
   §1 of `COMPOSE.md` — the fuller message is earned by having gone and got the
   facts.

   If the interview cannot run at all — headless, queued, no answer coming —
   quarantine the remaining `unsourced` entries into notes exactly as
   `peff-commit-auto` does, and say so in the report.

3. **Compose, check, commit.** Follow `COMPOSE.md` in this directory: budget,
   draft, check, commit, notes, report. `PEFF-STYLE.md` carries the voice.

## Why This Matters

The commit message is a reasoning checkpoint. Writing down why a change was made
is what exposes a misread change, and it only works if the why is real. A
message that reports a motivation nobody held is worse than a terse one, because
it answers the reviewer's question convincingly and wrongly, and it will be
believed for years.

That is why the interview comes before the draft rather than after it. A draft
written first invites correction of its wording, not supply of its missing
reasoning — you end up polishing a sentence whose premise nobody checked.

And it is why a short message is a legitimate outcome. If the reason for a
change exists nowhere and nobody supplies it, the honest record of that is a
subject line plus a note saying what was assumed. Reaching for a fuller message
anyway is how the invention gets in.
