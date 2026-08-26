---
name: peff-commit
description: >-
  Write a commit message in the style of Jeff King (peff) from the Git mailing
  list — narrative prose that says why the change was made, and git notes
  recording what was uncertain about it. Gathers the evidence first and
  interviews you about whatever it could not source, so the message reports
  your reasons rather than plausible ones. Use it whenever a commit message is
  about to be written or rewritten: committing staged work, amending or
  rewording an existing message, or fixing up a series before it is sent.
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
   `AskUserQuestion`, never a series. Always include `incident`: what prompted
   this change, and why now. Nothing in a repository records that, so it is the
   question worth spending.

   Offer your candidate readings as the options, so answering is a click rather
   than an essay; "Other" covers the case where all of them are wrong. Include
   an explicit escape — "go with your read" — and honour it by quarantining
   rather than by guessing into the body.

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
