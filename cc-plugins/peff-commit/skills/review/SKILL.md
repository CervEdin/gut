---
name: review
description: >-
  Go through a written commit series with the user, after peff-commit or
  peff-commit-auto wrote or reworded it: a cold read of each message against its
  own diff by a reader with no context, and a walk through the git notes, to
  settle which claims go into the message, which notes go, and which stay. It
  changes no commit and no note. Use it when a series is written and before it
  is sent or pushed for review, or when the user asks to go through the commits
  or their notes.
disable-model-invocation: false
---

# review

`peff-commit-auto` writes without asking, so what it could not confirm ends up
in the notes, and the user seldom reads them there. This skill runs once over a
finished series: it reads the messages as a stranger would, goes through the
notes with the user, and reports what was settled for each commit: which note
goes into the message, which is dropped, and which is kept on purpose.

It is a review: it changes no commit and no note. Rewording the commits is a
separate step, which the user asks for after the report; "Rewording" below says
how it is done.

`../peff-commit/COMPOSE.md` and `../peff-commit/PEFF-STYLE.md` hold the rules
this skill checks against.

## Range

Review the range the user names. Otherwise review `origin/HEAD..HEAD`. An empty
range is not a clean result: HEAD may be detached, or on another branch. Say
which range you read and that it held no commits, and stop.

## 1. Cold read

You know the session, so you cannot read the messages as someone who does not.
Hand them to a subagent that knows only what a reader of the log will:
`git log -p --no-notes <range>`. No brief, notes, transcript or conclusions of
yours. Ask it:

```
You are reading these commits in `git log -p` a year from now. For each
commit, list each sentence of the message that:

- you do not understand
- refers to something you cannot see, or whose "it" or "this" you
  cannot resolve
- states a behaviour without saying why it matters
- gives a reason without saying what it buys
- the diff does not bear out

And each paragraph that:

- is a list written as sentences: steps in order, or parallel items
  strung together

Quote the sentence, or the first sentence of the paragraph, and say
what is missing. Report only what you found; an empty list is a good
result.
```

A smaller model is fine for this, and it makes the reader colder. Check each
finding against the code before you act on it or pass it on: the reader has no
context, so some findings are wrong. Reject findings like these, which the user
has overruled before:

- that nobody can reproduce a failure the message describes, when the message
  only needs to say that it happened
- that a choice goes unexplained where the user said it needs no reason
- that a number was measured on an earlier version of the code, when this series
  could not change it much

A thin reason, such as "saves ~730 tokens per session", often has a fuller one
behind it that the session that made the change knew. Where you can find it in
the change's transcript or work it out from the code, write it as a sentence for
the message and show it to the user with the finding.

## 2. Notes

Read the notes with the commits they belong to:

```
git log --notes --reverse <range>
```

First settle what you can without the user. For each paragraph of each note:

- A claim that the code, a grep, the log or a transcript can test: test it. If
  it holds and the message needs it, mark it for the message, with what you
  checked. If it does not hold, mark it to be dropped.
- A note that the bar in §5 of `COMPOSE.md` rules out: mark it to be dropped.

## 3. Go through it with the user

Go through the cold-read findings that held and the note paragraphs that are
left with the user, and get an answer for each before the report. Do not put
them in `AskUserQuestion`: a quoted paragraph does not fit in its dialog. Give
each note the answers it can take:

- a **Relayed, not confirmed** note: confirmed (drop the note), wrong (take the
  claim out of the message), or keep
- a note about a cost the message takes no stance on: say what the change gives
  up and what you found for and against it, and ask the user for the stance. The
  answer becomes the message's "I think ... because ..." sentence
- any other note: into the message, drop, or keep

An answer that corrects a claim goes into the message in the corrected form.

## 4. Report

The range you read, then one section per commit, by sha and subject:

- each cold-read finding, with `accepted:` and the new sentence, or `rejected:`
  and the evidence
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
question as its citation.

Before the rebase folds the new messages in, give them a second cold read: each
`--fixup=reword` commit's message next to `git show --no-notes --format= <sha>`
of the commit it replaces, without the old message, since a reader of the log
will not have it either. Then check the new notes for long lines with the `grep`
in §5 of `COMPOSE.md`, and write them on the new shas with
`printf '%s\n' "$notes" | git notes add -f -F - <sha>`; empty text removes a
note.
