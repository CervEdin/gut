# Composing the message from the brief

Shared by `peff-commit` and `peff-commit-auto`. They differ only in how they
close the gaps in `.git/commit-brief`; everything after that is here.

`PEFF-STYLE.md`, alongside this file, carries the voice.

## 1. Budget

Count the **load-bearing facts** in the brief: sourced entries a reader could
not get by reading the diff.

- `incident` and `alternatives` entries always count.
- `today` counts when it says something the hunk alone does not show.
- `blame` and `issue` entries count.
- `change` never counts. The diff is right there.
- `unsourced` entries never count, in either skill.

The count sets the body:

| load-bearing facts | body           | cap       |
| ------------------ | -------------- | --------- |
| 0                  | subject only   | no body   |
| 1-2                | one paragraph  | 60 words  |
| 3-4                | two paragraphs | 140 words |
| 5+                 | three or more  | 250 words |

These are ceilings, not targets. Coming in far under one is normal and good.

**Zero facts means a subject line and nothing else.** That is a finished,
correct result, not a degraded one — 12% of peff's real commit bodies are under
40 words, and a change whose reason is not recorded anywhere is exactly the case
that should produce a short message. If the body feels thin, the repair is to go
find another fact, never to widen the ones you have.

## 2. Draft

Take the subject convention and the trailers from `git log --no-merges -10` —
whole messages, not `--oneline`, because one read answers both questions.

The subject follows whatever the log shows: Conventional Commits (`feat:`,
`fix(scope):`), a subsystem prefix (`http: ...`), or a bare imperative sentence.
The repo's convention always beats peff's default. Lowercase after the colon,
imperative mood, no trailing period, 50 characters soft and 72 hard.

Trailers likewise: sign off where the log signs off, carry a `Reviewed-by:` or
ticket trailer where the log carries one, add nothing where it carries nothing.
Separately from that, always add a `Generated-by:` trailer naming the model —
never `Co-authored-by:` and never a human's `Signed-off-by:` on the model's
behalf. See "Closing" in `PEFF-STYLE.md`.

Write the body from the load-bearing facts, in peff's voice, and from nothing
else. Write it to `.git/peff-commit-draft`.

## 3. Check

Run all of these before committing. The first two are the ones that catch
invention; the rest catch presentation.

1. **Provenance.** Take each sentence of the body and name the brief entry it
   came from. A sentence that maps to no entry, or to an `unsourced` one, comes
   out. Do not rescue it by hedging — "I suspect this improves performance" is
   the same fabrication wearing a disclaimer, and it reads as calibration rather
   than as the guess it is.
2. **Diff coverage.** Every claim in the message corresponds to something in the
   diff, and every non-trivial hunk is either accounted for or deliberately
   passed over. This catches the message that describes a different change than
   the one staged.
3. **Budget.** Body word count is inside the cap for the fact count.
4. **Line length.** 72 characters soft, 120 hard, body and notes alike.
5. **Slop score.**

   ```
   python3 <dir holding this file>/scripts/slop_score.py .git/peff-commit-draft
   ```

   Paths in this document are relative to `COMPOSE.md` itself, not to the skill
   reading it — `peff-commit-auto` reads this from a sibling directory.

   It needs `textstat` and says so in one line if it is missing. That is not
   worth installing anything over mid-commit: skip it and say in the report that
   the draft went unscored.

   Read the output in this order. **The stock-phrase penalty first, if there is
   one** — a hit costs a flat +8 however mild, so one stray "utilize" carries an
   otherwise clean draft into the bands below; delete the word and rescore.
   **Then the total**, once no phrase penalty is in it: below ~5 is fine, 5-8
   means the prose is denser than nearly all the corpus, above ~10 is LLM-slop
   register and wants a rewrite rather than a touch-up. **Then the strongest
   prose signal, which the scorer names** — the total sums signed z-scores, so a
   metric sitting low hides another's spike.

   Understand what this step does and does not do. The scorer reads the message
   and never sees the diff, so a wholly invented rationale written in clean peff
   register scores near zero. It measures register, not truth. Passing it is
   necessary and not remotely sufficient; checks 1 and 2 are the ones doing the
   real work.

## 4. Commit

`git commit -F .git/peff-commit-draft`.

A `commit-msg` hook may reject a long line. Rewrap and retry, or pass
`--no-verify` for a line that genuinely cannot wrap — a code snippet, pasted
output, a long identifier — and is still inside the 120-character hard limit.

## 5. Notes

Notes carry what the message cannot: alternatives not taken, caveats, scope
decisions, uncertainties — and, in `peff-commit-auto`, every `unsourced` entry
from the brief, marked plainly as an assumption.

Format them exactly like commit body prose, because `git notes` stores them
verbatim and they are read in a terminal: 72 characters per line soft, 120 hard,
no markdown, no bullet lists, paragraphs separated by a blank line.

No hook fires on `git notes add`, so nothing else catches a long line. Check
first:

```
printf '%s\n' "$notes" | grep -n '.\{121\}'
```

Rewrap anything it reports, then attach with
`printf '%s\n' "$notes" | git notes add -F -`.

## 6. Report

```
Committed as `1f3fd68`:

    (the commit message)

Notes:

    (the notes, as attached)
```

When the brief holds `unsourced` entries, lead with them under **Assumed, not
sourced** before the sha, one line each. That section is the point of the whole
exercise — it is where a misread change becomes visible while `--amend` is still
cheap. Close with `git commit --amend` to fix the message, `git notes edit` for
the notes.
