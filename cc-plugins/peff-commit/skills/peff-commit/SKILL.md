---
name: peff-commit
description: Write a commit message in the style of Jeff King (peff) from the Git mailing list. Use when about to commit, or when the user wants to craft a thoughtful commit message.
disable-model-invocation: false
---

# peff-commit

Write a commit message in the style of Jeff King (peff), a prolific Git
contributor. See `PEFF-STYLE.md` for the full style reference.

**IMPORTANT: Do NOT run `git commit`. Present the message and ask for
feedback.**

## Process

1. Understand the change — read `git diff --cached` (staged) and/or
   `git diff` (unstaged). If nothing is staged or changed, ask the user
   what change they'd like a message for.
2. Read `git log --oneline --no-merges -10` to detect the repo's subject
   line convention. Look for patterns like:
   - **Conventional Commits**: `feat:`, `fix:`, `chore:`, `feat(scope):`, etc.
   - **Subsystem prefix**: `http: ...`, `odb: ...`
   - **No prefix**: bare imperative sentences
   If the repo uses Conventional Commits, use that format for the subject
   line (type, optional scope, description) while keeping peff's narrative
   body style. The repo's convention always takes priority over peff's
   raw prefix style.
3. Draft a commit message following peff's style (see `PEFF-STYLE.md`),
   adapting the subject line format to match what you found in step 2.
4. Present it and ask for feedback.

## Output Format

Present the message like this:

> If I were to write this in the style of peff, I'd do it like this:
>
> ```
> (the commit message)
> ```
>
> (2-3 sentences on the key stylistic choices and your understanding of
> the change — what the problem was, why the fix works)
>
> Should I commit it like this, or do you have any follow-up questions?

## Why This Matters

Writing the commit message is a shared understanding exercise. The
narrative peff-style message forces both you and the user to articulate
*why* a change was made, not just *what* changed. If your understanding
of the problem doesn't match the user's, the commit message is where
that gap becomes visible. Treat the feedback loop as the point, not just
the final message.
