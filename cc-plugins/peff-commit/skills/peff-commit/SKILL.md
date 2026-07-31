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
   - **No prefix**: bare imperative sentences If the repo uses Conventional
     Commits, use that format for the subject line (type, optional scope,
     description) while keeping peff's narrative body style. The repo's
     convention always takes priority over peff's raw prefix style.
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
5. Write notes — caveats, alternatives you considered, things you're uncertain
   about. See the Notes section in `PEFF-STYLE.md`. Aim for 72 chars per line
   (soft limit), hard limit 120 — same as the commit body.
6. Commit with the drafted message, then report — see Output Format. A
   `commit-msg` hook may reject it for long lines. Rewrap and retry, or pass
   `--no-verify` for a line that genuinely can't wrap — a code snippet, pasted
   output, a long identifier — and is still inside the 120-char hard limit.
7. Check the notes before attaching them. No hooks fire on `git notes add`, so
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
