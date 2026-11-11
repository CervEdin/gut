# Composing the message from the brief

Shared by `peff-commit` and `peff-commit-auto`. They differ only in how they
close the gaps in `.git/commit-brief`; everything after that is here.

`PEFF-STYLE.md`, alongside this file, carries the voice.

## 1. Budget

A message is built out of two different things, and only one of them decides how
long it gets.

**The ground** is `today` and `change`: what the code does now at the site, and
what the patch tells it to do instead. It is usually worth writing, and usually
worth writing first — it is what lets the message be read without the diff open
beside it, and it is where a misread change gets caught, since a reader who
knows the code can only tell you that you have it wrong if you wrote down how
you think it works.

It is not a section to fill, though. A typo fix wants no account of what the
line said before, and a mechanical rename wants none of what the old name meant.
The ground is worth writing where the change turns on how the code behaves, and
a triviality does not turn on anything — explaining one is noise, and where the
subject already says what changes, saying it again in the body adds nothing. Nor
is any of it a finding: you did not go and learn it, it was in front of you. So
it earns the body no room.

**The findings** are what you had to go and get: `incident`, `alternatives`,
`blame`, `issue`, a model's reason you `checked`, a claim `relayed` as the
user's, and anything the caller came back with as `asked`. These are what make a
message long, and they are what to count. `unsourced` entries are not findings
in either skill — a guess is not something you found out.

A `series` entry is not one either. It comes off the branch's own log, and
nearly every commit on a topic branch has one, so counting it would give nearly
every commit an extra paragraph. Write it where it helps, like the ground, and
fit it in the room the findings earned.

Counting and placement are two different decisions. `uncertain` entries and
caveats belong in Notes (§5), not the body — an entry you route there doesn't
count toward the body's budget just because its tag would otherwise qualify.
Count only the findings the body is actually going to say.

Count the findings:

| findings | body           | usual range |
| -------- | -------------- | ----------- |
| 0        | the ground     | ~25 words   |
| 1-2      | one paragraph  | ~60 words   |
| 3-4      | two paragraphs | ~140 words  |
| 5+       | three or more  | ~250 words  |

The paragraph count is the rule; the word ranges describe what that many
paragraphs usually come to. Coming in far under one is normal and good. Going
well over is a signal to check the prose, not a violation to trim — a single
subtle mechanism can genuinely want a hundred words, and cutting it to fit a
number loses something that was actually sourced.

A split by topic (see "Paragraph Structure" in `PEFF-STYLE.md`) can add a
paragraph or a list to that count. The findings still set the word range.

**No findings means the ground and nothing else** — however much of it the
change actually wants, which is often a sentence or two and sometimes nothing at
all. That is a finished, correct result and not a degraded one: 12% of peff's
real commit bodies are under 40 words. If the body feels thin, the repair is to
go and find something out, never to widen what you have.

## 2. Draft

Take the subject convention and the trailers from `git log --no-merges -10` —
whole messages, not `--oneline`, because one read answers both questions.

The subject follows whatever the log shows: Conventional Commits (`feat:`,
`fix(scope):`), a subsystem prefix (`http: ...`), or a bare imperative sentence.
The repo's convention always beats peff's default. Lowercase after the colon,
imperative mood, no trailing period, 50 characters soft and 72 hard.

Trailers likewise: sign off where the log signs off, carry a `Reviewed-by:` or
ticket trailer where the log carries one, add nothing where it carries nothing.
Separately from that, when you write a new message, add a `Generated-by:`
trailer naming the model, and nothing else — never `Co-authored-by:` and never a
human's `Signed-off-by:` on the model's behalf. See "Closing" in
`PEFF-STYLE.md`.

A `series` entry keeps the positional wording it was written with — "the
previous commit", "the next commit". A sha is worth writing only for a commit
that has reached the mainline. Anything else is one rebase away from a different
sha, including the commits of the branch you are on.

Read the brief's `# review:` lines before the first sentence. They hold what the
user said about earlier messages on this branch, found by `commit-brief` in the
sessions that wrote them, and they are rules for this draft too: a lesson taught
on one commit of a series applies to every commit after it. Then draft in the
order that "Body: Narrative Prose" in `PEFF-STYLE.md` gives, and write each
sentence to the rules under "Sentences" there.

Build the body by rewriting brief entries, in peff's voice, and from nothing
else. Write it to the peff-commit-draft file —
`git rev-parse --git-path peff-commit-draft` if you're in a worktree, where
`.git/peff-commit-draft` doesn't resolve.

The session is in your context, and it is not a source at this step. Everything
from it that belongs in the message is already a brief entry, with a tag that
says how well it is sourced. Drafting from the session skips that tag. It also
changes the prose. In a long session you hold the facts as a story of events:
what you tried, what broke, what you changed. A body drafted from that story is
a retelling in the past tense ("the backup was queued", "the trap removed the
file"). It describes code the reader still has in front of them as though it
were gone. Draft with the brief open, one entry at a time. If you want a
sentence that no entry supports, go back to `commit-brief` and add the entry
with an honest tag, or leave the sentence out.

An entry can carry the session's shape too. If it answers a question that came
up during the work ("why not keep the old name?"), it goes in the body only when
a reader of the diff would ask the same question. Otherwise it answers the
session, not the change: put it in the notes, or leave it out.

Shape the paragraphs as you draft, not after the checks. A paragraph of more
than 5 sentences or more than about 80 words on more than one topic is split
where its topics part, and a sentence or more of someone else's words inside a
sentence goes into a `> ` block of its own; the user's words become the author's
own, with the quote in the notes. See "Paragraph Structure" and "Emphasis and
References" in `PEFF-STYLE.md`. Then reread the message as a reader would. Each
paragraph of one sentence that a split left gets the questions in "Paragraph
Structure": drop it, write the idea it serves, or put it back.

## 3. Check

Run all of these before committing. Checks 2 and 3 are the ones that catch
invention; the rest catch format and presentation.

Each check leaves output behind: a tool's output, or a section of the provenance
file below. A check that is only done in your head is easy to skip without
noticing, and the checks that were skipped in practice were the ones that
printed nothing. Paths in this document are relative to `COMPOSE.md` itself, not
to the skill reading it — `peff-commit-auto` reads this from a sibling
directory.

1. **Brief lint.**

   ```
   python3 <dir holding this file>/../commit-brief/scripts/lint_brief.py "$(git rev-parse --git-path commit-brief)"
   ```

   `commit-brief` already ran it, but the interview in `peff-commit` adds
   `asked` entries afterwards, so run it again. Fix the brief until it passes.

2. **Provenance.** Write the provenance file,
   `$(git rev-parse --git-path peff-commit-provenance)`. Start with the subject
   line, then each sentence of the body in order. Write the sentence, then on
   indented lines the ID and text of each brief entry it came from, and a
   `gives:` line with what the sentence tells the reader that the diff does not:

   ```
   mbsync.service: run the backup after every sync
     change-1: ExecStartPost -> ExecStopPost for the backup.

   The backup is queued by the last ExecStartPost=, so a failed sync
   skips it.
     today-1: Backup queued via ExecStartPost=, after the scorer and
       notmuch new.
     incident-1: User noticed backups stall when syncs fail.
     gives: a failed sync skips the backup
   ```

   The subject needs no `gives:` line. If the only `gives:` you can write is the
   sentence again, or a list of names from the diff, the sentence narrates the
   diff: attach its reason or consequence, or cut it. Then check each sentence
   against the rest of "Sentences" in `PEFF-STYLE.md`, and write `fixed:` under
   any sentence you changed, saying what was wrong ("fixed: 'it' could mean the
   checkpoint").

   A sentence with no entry, or only an `unsourced` one, gets `NONE` and comes
   out of the draft. Leave the `NONE` record in the file, so the report shows
   what was cut. Do not rescue the sentence by hedging — "I suspect this
   improves performance" is the same fabrication wearing a disclaimer, and it
   reads as calibration rather than as the guess it is.

   Then read each sentence against its entries for drift. The usual kinds are: a
   `today` entry in the present tense that became past tense in the sentence
   (see "Tense" in `PEFF-STYLE.md`), a verb or a number that changed, and a
   claim wider than its entry. Correct the sentence to match the entry, never
   the other way.

   A paragraph whose sentences all cite `change` entries has no point of its
   own: see "Paragraph Structure" in `PEFF-STYLE.md`.

3. **Diff coverage.** List the changed files with `git diff --cached --stat`, or
   `git show --stat <sha>` when rewording. Append a `coverage:` section to the
   provenance file with one line per file: the ID of an entry cited above that
   accounts for it, or `passed over:` and the reason.

   ```
   coverage:
     systemd/mbsync.service: change-1
     CLAUDE.md: passed over: documents the new ExecStopPost= order
   ```

   This catches a message that describes a different change from the one staged.
   It also shows when the files span unrelated concerns — a config import, a bug
   fix, and a new document in one commit. Then recommend a split. `peff-commit`
   asks the user whether to split before it commits. `peff-commit-auto` commits
   anyway and puts the recommendation in the notes as a scope note.

4. **Budget.** Append a `budget:` line to the provenance file: the findings the
   body says, the range for that count, and the body's word count, subject and
   trailers excluded.

   ```
   budget: 2 findings, ~60 words, body 71 words
   ```

   Well over the range? Re-read the paragraph that pushed it over and check its
   sentences against their provenance records (check 2). If each one still names
   its entry, the length can stay. Past twice the range, it can still stay, but
   the line has to say why: what the extra words explain that a shorter body
   could not. The range is a guideline, and the line is how an overrun reaches
   the report instead of being waved through in your head.

   Then append a `paragraphs:` line with the sentences, words and topics of each
   paragraph of the body and notes:

   ```
   paragraphs: 1: 3 sentences, 52 words, 1 topic; 2: 7 sentences, 104 words, 2 topics
   ```

   A paragraph over the limits with more than one topic goes back to §2 to be
   split. So does each paragraph of one sentence that a split left, for the
   questions in "Paragraph Structure". Checks 2 and 4 run again on the result.

5. **Commit references.** Every sha in the draft is on the mainline.
   `git rev-list origin/HEAD..HEAD` lists the ones that are not: those get
   rewritten, so a sha naming one of them is a name for nothing.

   ```
   grep -oE '\b[0-9a-f]{7,40}\b' "$(git rev-parse --git-path peff-commit-draft)" |
     while read -r sha; do
       git merge-base --is-ancestor "$sha" origin/HEAD 2>/dev/null ||
         echo "not on the mainline, rewrite positionally: $sha"
     done
   ```

   Use whatever the mainline is called here — `origin/HEAD`, `origin/main`,
   `main`. Rewrite anything it reports as "the previous commit", or however else
   the commit sits relative to this one.

6. **Line length.** 72 characters soft, 120 hard, body and notes alike.
7. **Slop score.**

   ```
   python3 <dir holding this file>/scripts/slop_score.py "$(git rev-parse --git-path peff-commit-draft)"
   ```

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
   necessary and not remotely sufficient; checks 2 and 3 are the ones doing the
   real work.

## 4. Commit

`git commit -F "$(git rev-parse --git-path peff-commit-draft)"`.

A `commit-msg` hook may reject a long line. Rewrap and retry, or pass
`--no-verify` for a line that genuinely cannot wrap — a code snippet, pasted
output, a long identifier — and is still inside the 120-character hard limit.

## 5. Notes

Notes carry what the message cannot, and what it says without confirmation:
alternatives not taken, caveats, scope decisions, uncertainties, a cost the
message takes no stance on — and, in `peff-commit-auto`, every `unsourced` entry
from the brief, marked plainly as an assumption. Every `relayed` entry the
message uses gets a note too, marked as not confirmed.

Keep three kinds apart, each in paragraphs of its own. An assumption or an
uncertainty is a claim, which the reader verifies. A relayed claim is already in
the message; the reader confirms that it is theirs. A scope decision or a piece
of work left over (fix X, drop Y) is not a claim; the reader decides it.

Write a note only when a reviewer can act on it: check a claim, decide a scope,
weigh an alternative. Leave out filler: why a formatter reflowed a line, or that
a lint, the tests or the build pass. Once a commit is on the mainline, its
checks can be assumed to have passed when it merged, and after an amend or a
rebase the claim may no longer hold.

Format notes exactly like commit body prose, because `git notes` stores them
verbatim and they are read in a terminal: 72 characters per line soft, 120 hard,
no markdown, paragraphs separated by a blank line. A dense paragraph is split
into paragraphs, or into a list where its items are one (see "Tone" in
`PEFF-STYLE.md`). A person's words, the user's included, go in a mail-style `> `
quote: see "Emphasis and References" in `PEFF-STYLE.md`.

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

Provenance:

    (the provenance file, including its coverage:, budget: and paragraphs: lines)
```

The provenance file goes in the report whole. If a check was skipped, its
section is missing, and the user can see that.

When the brief holds `unsourced` entries, lead with them under **Assumed, not
sourced** before the sha, one line each. That section is the point of the whole
exercise — it is where a misread change becomes visible while `--amend` is still
cheap. It holds claims only. Work to do or to drop goes after it, under **To
decide**, so that the user is not asked to verify a to-do. Close with
`git commit --amend` to fix the message, `git notes edit` for the notes.

## Review, before sending

This is not a check on every commit. Before a series is sent or pushed for
review, or when the user asks, run `peff-commit:review` over it, with the user
present: a cold read of the messages by a reader with no context, and a walk
through the notes.

## Rewording existing commits

The process above assumes staged work. To rewrite the message of commits that
already exist, run it once per commit, with these changes.

Which skill runs it: `peff-commit` has `disable-model-invocation: true`, so an
agent cannot invoke it. An agent rewording its own commits uses
`peff-commit-auto`. When the user wants the reword, they run `/peff-commit`.

**Keep the trailers.** The commit keeps the trailers it has. Add `Generated-by:`
only if it is missing and the new text is a model's. Add no session link or
other trailer the harness asks for, even where it asks for every commit: it
would name the session that reworded the message, not the one that wrote the
code.

**Each round of review is a reword.** When the user reviews the messages and
asks for changes, run the process again for each commit they comment on, and
check the commits they did not comment on against the same remarks: a remark on
one message usually applies to its siblings. Where a suggestion of theirs states
something the code does not do, say so in one line with the evidence, then
follow their decision. Do not argue again for wording they have settled.

**Hold each round to the budget.** When the fix for a remark would push the body
past the word range in §1, check first whether all of the addition is needed,
whether it can be said more directly, and what the message already says that can
go, other than wording the user settled. Only then add. Moving the extra words
into the notes is not a fix: the length is still there, in another place.

**One brief per commit.** `commit-brief` gathers from `git show <sha>` in place
of the staged diff. Do not combine several commits into one brief: the IDs, the
provenance file and the coverage check all belong to one commit.

**Fold the new messages in with one rebase, in place of §4.** Each rewrite of
history gives every later commit a new sha, so do not rewrite once per commit.
Commit each new message as a `--fixup=reword` commit, which names its target,
then fold them all in with one autosquash rebase, which copies the notes when
`notes.rewriteRef` is set. The `git-rebase-i` skill's Reword recipe does this
with `git reword` and checks the notes afterwards. Follow it.

Without that plugin, start each draft with the line `amend! <sha of the target>`
and a blank line. Autosquash folds `amend! <subject>` into the first commit with
that subject, and two commits in a range can share one. Then run:

```
GIT_EDITOR="cp $(git rev-parse --git-path peff-commit-draft)" git commit --fixup=reword:<sha>
GIT_SEQUENCE_EDITOR=: git -c notes.rewriteRef='refs/notes/*' rebase -i --autosquash <oldest sha>^
```

The fixup commits change no existing commit, so the shas of the targets stay
valid until the rebase. `git log` shows each new message before it runs. Then
use `git notes add -f` to update the notes of the reworded commits (§5).

The report (§6) covers each reworded commit, with its new sha.
