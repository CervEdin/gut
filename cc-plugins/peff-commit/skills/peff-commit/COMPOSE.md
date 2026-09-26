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
`blame`, `issue`, and anything the caller came back with as `asked`. These are
what make a message long, and they are what to count. `unsourced` entries are
not findings in either skill — a guess is not something you found out.

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
Separately from that, always add a `Generated-by:` trailer naming the model —
never `Co-authored-by:` and never a human's `Signed-off-by:` on the model's
behalf. See "Closing" in `PEFF-STYLE.md`.

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
   indented lines the ID and text of each brief entry it came from:

   ```
   mbsync.service: run the backup after every sync
     change-1: ExecStartPost -> ExecStopPost for the backup.

   The backup is queued by the last ExecStartPost=, so a failed sync
   skips it.
     today-1: Backup queued via ExecStartPost=, after the scorer and
       notmuch new.
     incident-1: User noticed backups stall when syncs fail.
   ```

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

4. **Budget.** Append a `budget:` line to the provenance file: the findings
   the body says, the range for that count, and the body's word count, subject
   and trailers excluded.

   ```
   budget: 2 findings, ~60 words, body 71 words
   ```

   Well over the range? Re-read the paragraph that pushed it over and check its
   sentences against their provenance records (check 2). If each one still names
   its entry, the length can stay. Past twice the range, it can still stay, but
   the line has to say why: what the extra words explain that a shorter body
   could not. The range is a guideline, and the line is how an overrun reaches
   the report instead of being waved through in your head.

5. **Line length.** 72 characters soft, 120 hard, body and notes alike.
6. **Slop score.**

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

Provenance:

    (the provenance file, including its coverage: and budget: lines)
```

The provenance file goes in the report whole. If a check was skipped, its
section is missing, and the user can see that.

When the brief holds `unsourced` entries, lead with them under **Assumed, not
sourced** before the sha, one line each. That section is the point of the whole
exercise — it is where a misread change becomes visible while `--amend` is still
cheap. Close with `git commit --amend` to fix the message, `git notes edit` for
the notes.

## Rewording existing commits

The process above assumes staged work. To rewrite the message of commits that
already exist, run it once per commit, with these changes.

Which skill runs it: `peff-commit` has `disable-model-invocation: true`, so an
agent cannot invoke it. An agent rewording its own commits uses
`peff-commit-auto`. When the user wants the reword, they run `/peff-commit`.

**One brief per commit.** `commit-brief` gathers from `git show <sha>` in place
of the staged diff. Do not combine several commits into one brief: the IDs, the
provenance file and the coverage check all belong to one commit.

**Newest first.** Rewording a commit rewrites all of its descendants, and they
get new shas. Its ancestors do not change. If you start with the newest commit,
the shas of the older commits you have not reworded yet stay valid.

**Save the old shas before the first reword.** Rewording loses notes (see
below), and the old shas are how you get them back:

```
base=$(git rev-parse <oldest sha>^)
git rev-list --reverse $base..HEAD >"$(git rev-parse --git-path peff-reword-old)"
```

**Reword in place of §4.** For each commit, after the checks pass:

```
GIT_EDITOR="cp $(git rev-parse --git-path peff-commit-draft)" git history reword <sha>
```

Where `git history` is missing, use an interactive rebase that starts at the
commit, so the commit is the first line of the todo list:

```
GIT_SEQUENCE_EDITOR="sed -i '1s/^[a-z]*/reword/'" \
GIT_EDITOR="cp $(git rev-parse --git-path peff-commit-draft)" git rebase -i <sha>^
```

The sed replaces any command word, not only `pick`: with
`rebase.abbreviateCommands` set, the todo list says `p`.

**Carry the notes over.** `git history reword` drops the notes of the reworded
commit and of every descendant, whatever `notes.rewriteRef` says. `git rebase`
keeps them only when `notes.rewriteRef` is set. After the last reword, pair the
old shas with the new ones by position and copy each note that did not come
across:

```
git rev-list --reverse $base..HEAD |
paste -d' ' "$(git rev-parse --git-path peff-reword-old)" - |
while read old new; do
	git notes list $old >/dev/null 2>&1 &&
	! git notes list $new >/dev/null 2>&1 &&
	git notes copy $old $new
done
```

Pairing by position works because a reword never adds or drops a commit, but
only on a linear range. This copies the default notes ref. Repeat with
`git notes --ref=<ref>` for each other ref that `git for-each-ref refs/notes`
shows. Then use `git notes add -f` to update the notes of the reworded commits
(§5).

The report (§6) covers each reworded commit, with its new sha.
