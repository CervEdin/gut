---
name: intent-review
description: >-
  Review a diff against what the user said in the Claude Code sessions that
  wrote it: decisions the agent made without asking, vague answers it read one
  way, requests it dropped, and changes that contradict the user. Use after an
  agent finishes a change and before it is committed, pushed or sent, or when
  asked whether a change does what the user asked. Skips when no transcript of
  the change can be found.
disable-model-invocation: false
---

# intent-review

An agent turns a vague answer into one reading, or makes a choice on its own,
and the code it writes looks the same as code the user asked for. A diff review
cannot see the difference. This review reads the user's own turns in the
sessions that wrote the change, and checks each decision in the diff against
them.

The agent that wrote the change is the worst reviewer of it: its own inferences
read as settled in its context. If this context wrote the change, start an Agent
(`model: sonnet`, `effort: high`) that invokes this skill on the same range, and
pass its report on unchanged.

## Process

1. **Get the change.** Use the rule the persona reviews use:
   - "Review this branch" or "my changes": `git log -p origin/HEAD..HEAD`. If
     `origin/HEAD` is not set, ask for the base.
   - A PR: fetch it as the host requires, then read its commit range.
   - Only staged changes: `git diff --cached`.
   - Nothing obvious: ask what to review.

2. **Find the transcripts.** Run the second script next to this file, from the
   repository, on the range from step 1:

   ```
   python3 <dir holding this file>/scripts/find_sessions.py <range>
   python3 <dir holding this file>/scripts/find_sessions.py --staged
   ```

   The script reads every transcript under `~/.claude/projects`, since a session
   often works on this repository from another checkout, or from one that has
   since been removed. It matches a session that edited or wrote a file whose
   path ends in a path the change touches, unless that file's directory still
   exists and belongs to another repository, or that holds the subject of a
   commit in the range. The plan hand-offs and summaries of a matched session
   bring in the sessions they came from.

   A common name such as `README.md`, or a session that only printed the log,
   can match a session about something else. Each line of evidence gives the
   transcript lines it was found on. Read the user's turns around those lines,
   and drop the session if none of them is about the change. Name the sessions
   you kept, and why, in the report.

   **If no transcript is found, stop.** Report that the review was skipped, and
   which searches found nothing. Do not infer intent from the commit messages or
   the code.

3. **Read the user's turns.** Run the script next to this file on each
   transcript, oldest first:

   ```
   python3 <dir holding this file>/scripts/user_turns.py <transcript>...
   ```

   It prints each turn with its line number in the file, labelled `user`,
   `answered`, `rejected plan`, `command`, `ran`, `pasted`, `interrupt`, or
   `model-written`. Then read the plans, notes and files those turns name.

   Who wrote a sentence decides what it proves:
   - `user`, `answered`, `rejected plan` with a reason, and `command` arguments
     are the user's words. A note the user passes on from an agent ("here is a
     note from a side agent") is not, unless they say they agree with it.
   - `model-written` text is not the user's, even when it arrives as a user
     turn.
   - An `approved plan` turn, or a plan hand-off (which only follows an
     approval), means "go ahead", not that the user read the plan or agrees with
     what it says. A decision in the plan, its approach included, is the user's
     only where a turn of theirs covers it; otherwise it is `unasked`. Quote the
     plan's line, so that the user can see where the decision came from.
   - A choice the agent offered with its reason, which the user then took, is
     the user's decision. Silence is not: a choice the agent reported and the
     user never answered is still the agent's.
   - A later turn overrides an earlier one.

4. **List the decisions in the diff.** Per commit, list each choice a user would
   want a say in:
   - behaviour: what the code does in a case the request did not name;
   - scope: work added beyond the request, or left out of it;
   - interfaces: public names, commands, flags, config keys, file layout;
   - cost: new dependencies, agents or calls per run, time, money;
   - a departure from a plan the user approved;
   - an action outside the repository: a push, a post, a mail.

   Leave out local names, formatting, and internal structure that follows from
   the request. When unsure, ask: would the user have wanted to be asked?

5. **Check each decision against the turns.** It is one of:
   - **backed**: a turn of the user's says it, or the user took it when offered.
     No finding.
   - **contradicted**: a turn of the user's says otherwise.
   - **misread**: a turn covers it but allows more than one reading, and the
     code follows one of them.
   - **unasked**: no turn covers it.
   - **dropped**: the user asked for something the diff does not do. Check later
     commits on the branch before reporting it.

   Search the turns for the topic before calling a decision `unasked`. A user
   often answers in few words ("sure", "2 then"); read the question they
   answered.

## Output Format

Per commit, in diff order, laid out like the persona reviews so the outputs can
be read side by side. Start with the transcripts read, so that a verifier can
read them again: the full path of each, the evidence `find_sessions.py` gave for
it, and the number of user turns. Then give the full path of `user_turns.py`.

> ### [PATCH N/M] `<subject line>`
>
> **On `<file>:<line>`:**
>
> ```
> (quoted code or diff hunk)
> ```
>
> `Kind: intent — <contradicted|misread|unasked|dropped>`
>
> `Said:` the user's words, quoted, with `<transcript file>:L<n>`. For
> `unasked`, what the search covered: "nothing in 2 transcripts (68 user
> turns)". For `misread`, the turn and the other reading.
>
> What the code does, and the question to put to the user: "The skill skips a
> persona whose plugin is missing. Should it stop instead?"

A `dropped` finding has no code line; write it as **On the request,
`<transcript file>:L<n>`:**.

End with the questions to ask the user, most important first: `contradicted`,
then `dropped`, then the decisions that are hardest to undo.

## Important

- **Quote, do not paraphrase.** Every `Said:` is the user's exact words and its
  line. A finding without a quote, or without the search it ran, is not a
  finding.
- **Decisions, not code quality.** Bugs, style and comment placement belong to
  the persona reviews and comment-review. Whether the commit message states the
  user's reasons faithfully belongs to peff-commit.
- **Do not judge the decision.** An unasked choice can be a good one. The
  finding says that the user did not make it, not that it is wrong.
- **Read-only.** Do not edit files, commit, or reply in the transcripts' place.
