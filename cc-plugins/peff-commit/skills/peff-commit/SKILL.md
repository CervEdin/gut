---
name: peff-commit
description:
  Write a commit message in the style of Jeff King (peff) from the Git mailing
  list. Use when about to commit, or when the user wants to craft a thoughtful
  commit message.
disable-model-invocation: false
---

# peff-commit

Channel Jeff King (peff) — prolific Git contributor — when writing commit
messages. The persona is the steering mechanism: peff's voice naturally produces
commit messages that articulate reasoning, discuss alternatives, and stay honest
about uncertainty. The goal is not impersonation; it's that this style forces
you to actually think through and verbalize the reasoning behind a change.

See `PEFF-STYLE.md` for the full style reference.

The default is to commit and then report. Interview the user first only when the
change's motivation can't be recovered — see step 3.

## Process

1. Understand the change — read `git diff --cached` (staged) and/or `git diff`
   (unstaged). If nothing is staged or changed, ask the user what change they'd
   like a message for.
2. Read `git log --oneline --no-merges -10` to detect the repo's subject line
   convention. Look for patterns like:
   - **Conventional Commits**: `feat:`, `fix:`, `chore:`, `feat(scope):`, etc.
   - **Subsystem prefix**: `http: ...`, `odb: ...`
   - **No prefix**: bare imperative sentences

   Follow whatever the log shows and keep peff's narrative body underneath it.
   With Conventional Commits that means type, optional scope, and description on
   the subject line. The repo's convention always takes priority over peff's raw
   prefix style.

3. Decide whether you can state _why_ the change was made. The motivation is
   missing when:
   - nothing in the diff, the conversation, or the recent log explains why the
     change was made;
   - two plausible motivations would produce materially different messages; or
   - the change reads as a workaround or a tradeoff whose rationale lives
     outside the code.

   If any of those hold, interview the user before drafting — ask focused
   questions (AskUserQuestion) about motivation, alternatives weighed, and
   scope. Don't draft a speculative message first; a draft invites correction of
   wording instead of supplying the reasoning that's missing. Otherwise go
   straight on to step 4.

4. Draft a commit message following peff's style (see `PEFF-STYLE.md`), adapting
   the subject line format to match what you found in step 2. Then reread the
   draft and delete every clause that carries no fact, causal link, or decision
   — asides survive only if they report effort, confidence, or scope.
5. Score the draft with the bundled slop scorer (needs the `textstat` package),
   passing the draft as a file or on stdin:

   ```
   python3 <skill base dir>/scripts/slop_score.py draft.txt
   ```

   The combined z-score measures the draft's prose against a baseline fit from
   300 of peff's real commit messages, so 0 means "median peff" — that is the
   target, not a minimum. Read the output in this order:

   - **The stock-phrase penalty, if there is one.** A hit costs a flat +8
     however mild it is, so one stray "utilize" carries an otherwise clean draft
     into the bands below and the density advice there won't fix it. Delete the
     word and rescore. The exception is quoting slop vocabulary on purpose —
     writing about slop — where the hit is correct and stays.
   - **Then the total, once no phrase penalty is in it.** Below ~5 is fine. 5–8
     means the prose is denser than nearly all of the corpus: break
     clause-chained sentences into shorter ones, trade abstract nouns for verbs,
     and rescore. Above ~10 is LLM-slop register; rewrite rather than touch up.
   - **Then the strongest prose signal, which the scorer names.** The total sums
     signed z-scores, so a metric sitting low hides another one's spike. Real
     messages rarely push a single metric past +3; past that, read what that
     metric measures even when the total looks fine.

   Under 40 words of prose the metrics are summarising three or four sentences
   and the score reports noise. The scorer says so when it happens; judge a
   message that short by eye.

6. Write notes — caveats, alternatives you considered, things you're uncertain
   about. See the Notes section in `PEFF-STYLE.md`. Aim for 72 chars per line
   (soft limit), hard limit 120 — same as the commit body.
7. Commit with the drafted message, then report — see Output Format. A
   `commit-msg` hook may reject it for long lines. Rewrap and retry, or pass
   `--no-verify` for a line that genuinely can't wrap — a code snippet, pasted
   output, a long identifier — and is still inside the 120-char hard limit.
8. Check the notes before attaching them. No hooks fire on `git notes add`, so
   nothing else catches a long line, and checking first saves a rewrite:
   ```
   printf '%s\n' "$notes" | grep -n '.\{121\}'
   ```
   Rewrap any lines it reports, then attach with
   `printf '%s\n' "$notes" | git notes add -F -`.

## Output Format

Report the commit like this — the sha, the message as it landed, and the notes
that went with it:

> Committed as `1f3fd68`:
>
> ```
> (the commit message)
> ```
>
> **Notes** (plain text, no markdown, no bullet lists — aim 72 chars/line, hard
> limit 120):
>
> ```
> Prose paragraphs here, every line hard-wrapped at 72 characters, just
> like the commit body. Blank line between paragraphs. Caveats,
> alternatives considered, uncertainties — whatever helps the user
> verify your reasoning.
> ```
>
> `git commit --amend` to fix the message, `git notes edit` for the notes.

## Why This Matters

The commit message is a reasoning checkpoint. The narrative style forces you to
articulate _why_ a change was made, not just _what_ changed. The notes surface
the gaps — alternatives you weighed, things you're unsure about, scope
decisions. If your understanding doesn't match the user's, this is where it
becomes visible. A bad commit message that gets corrected is more valuable than
a generic one that goes unquestioned.

That is why the message records the motivation you _believed_ you were acting
on, and why it gets written even when you commit without asking. If you can't
state the motivation, that is itself the signal — you may have misread the point
of the change. And if the change later turns out to be wrong, the recorded why
usually shows how you got there. Reviewing it after the commit exists costs
nothing, since amending is cheap; stopping to ask when nothing needs deciding
leaves the work parked.
