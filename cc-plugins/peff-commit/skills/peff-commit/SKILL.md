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

**IMPORTANT: Do NOT run `git commit`. Present the message and ask for
feedback.**

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
3. Draft a commit message following peff's style (see `PEFF-STYLE.md`), adapting
   the subject line format to match what you found in step 2.
4. Write notes — caveats, alternatives you considered, things you're uncertain
   about. See the Notes section in `PEFF-STYLE.md`. Aim for 72 chars per line
   (soft limit), hard limit 120 — same as the commit body.
5. Present it and ask for feedback.
6. Once the user approves, commit with the message, then attach the notes to the
   new commit with `git notes add -m <notes>`.
7. Check for long lines:
   ```
   git log -1 --format=%s | grep -n '.\{73\}'
   { git log -1 --format=%b; git notes show 2>/dev/null; } | grep -n '.\{121\}'
   ```
   If any lines are reported, show them to the user and offer to fix them.

## Output Format

Present the message like this:

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
> Want me to commit this, or does anything look off?

## Why This Matters

The commit message is a reasoning checkpoint. The narrative style forces you to
articulate _why_ a change was made, not just _what_ changed. The notes surface
the gaps — alternatives you weighed, things you're unsure about, scope
decisions. If your understanding doesn't match the user's, this is where it
becomes visible. A bad commit message that gets corrected is more valuable than
a generic one that goes unquestioned.
