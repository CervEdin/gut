---
name: review
description: >-
  Go through a written commit series with the user, after peff-commit or
  peff-commit-auto wrote or reworded it: a walk through the git notes, to settle
  which claims go into the message, which notes go, and which stay. It changes
  no commit and no note. Use it when a series is written and before it is sent
  or pushed for review, or when the user asks to go through the commits or their
  notes.
disable-model-invocation: false
---

# review

`peff-commit-auto` writes without asking, so what it could not confirm ends up
in the notes, and the user seldom reads them there. This skill runs once over a
finished series: it goes through the notes with the user, and reports what was
settled for each commit: which note goes into the message, which is dropped, and
which is kept on purpose.

It is a review: it changes no commit and no note. Rewording the commits is a
separate step, which the user asks for after the report; "Rewording" below says
how it is done.

`../peff-commit/COMPOSE.md` and `../peff-commit/PEFF-STYLE.md` hold the rules
this skill checks against.

## Range

Review the range the user names. Otherwise review `origin/HEAD..HEAD`. An empty
range is not a clean result: HEAD may be detached, or on another branch. Say
which range you read and that it held no commits, and stop.

## 1. Notes

Read the notes with the commits they belong to:

```
git log --notes --reverse <range>
```

First settle what you can without the user. For each paragraph of each note:

- A claim that the code, a grep, the log or a transcript can test: test it. If
  it holds and the message needs it, mark it for the message, with what you
  checked. If it does not hold, mark it to be dropped.
- A note that the bar in §5 of `COMPOSE.md` rules out: mark it to be dropped.

## 2. Go through it with the user

Go through the note paragraphs that are left with the user, and get an answer
for each before the report. Do not put them in `AskUserQuestion`: a quoted
paragraph does not fit in its dialog. Give each note the answers it can take:

- a **Relayed, not confirmed** note: confirmed (drop the note), wrong (take the
  claim out of the message), or keep
- any other note: into the message, drop, or keep

An answer that corrects a claim goes into the message in the corrected form.

## 3. Report

The range you read, then one section per commit, by sha and subject:

- each note paragraph: into the message (with the wording, corrected where the
  user corrected it), drop (by the user, or by you with what you checked), or
  keep
- for each claim that goes into the message, how it was settled: what you
  checked, the user's words in a transcript, or the question the user answered

The report is the end of the review. Commit nothing, and change no note.

## Rewording

When the user asks for the settled changes to be made, reword the commits with
`peff-commit-auto`, as "Rewording existing commits" in
`../peff-commit/COMPOSE.md` says, one brief per commit from `git show <sha>`.
Each claim from the report enters the brief by how it was settled: `checked`
with what was checked, `session` with the user's words, `asked` with the
question as its citation. Then check the new notes for long lines with the
`grep` in §5 of `COMPOSE.md`, and write them on the new shas with
`printf '%s\n' "$notes" | git notes add -f -F - <sha>`; empty text removes a
note.
