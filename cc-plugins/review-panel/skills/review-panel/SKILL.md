---
name: review-panel
description: >-
  Run several persona reviews (peff, gitster, sunshine, avar, comment) and
  intent-review on the same commits as independent parallel agents, merge their
  findings, and have separate verifier agents confirm or refute each claimed
  defect against the code, and each intent finding against the transcripts.
  Opinions on naming, design and patch split are passed through without
  verification.
disable-model-invocation: true
---

# review-panel

The persona reviews each run alone. When several run one after another in the
same context, each one sees the conclusions of the ones before it, and the
reviews stop being independent. This skill runs each persona in its own agent,
at the same time, on the same range. Then it gives the defects they claim to
separate verifier agents, which may refute them.

Run it in the main session, not in an agent, so that the finders' full reports
stay available for questions about a finding.

## Arguments

`/review-panel [personas] [target]`

- **personas**: a comma-separated list of `peff`, `gitster`, `sunshine`, `avar`,
  `comment`, `intent`. Default: all six. `intent` is intent-review, which checks
  the diff against what the user said in the sessions that wrote it.
- **target**: a range, a branch, or a PR. Default: the rule in step 1.

Example: `/review-panel peff,sunshine main..topic`.

## Models

Each agent gets the model and effort of its role, unless the user names another
for the run, for a persona, or for the verifiers:

- Finders: `model: sonnet`, no `effort`.
- Verifiers: `model: sonnet`, `effort: high`. Each defect gets one verdict and
  no second reader, so the effort goes to the verifier.
- `intent` finder: `model: sonnet`, `effort: high`. It judges vague turns across
  long transcripts; effort adds output, while a larger model multiplies the cost
  of that input.
- `intent` verifier: `model: opus`, no `effort`. It decides whether a turn or a
  plan approval settled a decision, from the short output of `user_turns.py`.

A model or effort the user gives for a finder does not carry over to its
verifier. Before you start the finders, and again before the verifiers, say in
one line how many agents start and the model and effort of each.

## Process

1. **Scope.** Work out the target once, with the rule the persona skills use:
   - A range or branch argument: use it (a branch `B` means
     `$(git merge-base origin/HEAD B)..B`).
   - A PR: fetch it as the host requires and use its commit range.
   - No argument: `origin/HEAD..HEAD`. If that is empty and changes are staged,
     use the staged diff (`git diff --cached`). If `origin/HEAD` is not set or
     nothing is clear, ask what to review.

   The result is the **target**: a range, or the staged diff. Record the commit
   list (`git log --oneline <range>`) and the diff size
   (`git diff --shortstat <range>`, or `git diff --cached --shortstat`). Every
   finder and verifier gets the same target: where a prompt below says
   `<target>`, write the range, or "the staged diff (`git diff --cached`)".

   Check that the skill of each requested persona is available
   (`<persona>-review:<persona>-review`). Drop the ones that are not installed
   and say so in the report.

2. **Find.** Start one Agent per persona, all in a **single message**, with the
   model and effort from Models. Use this prompt, with `<persona>` and
   `<target>` filled in:

   > Invoke the `<persona>-review:<persona>-review` skill on `<target>`. Follow
   > its Process and Output Format, and keep its prose, its `something like:`
   > code and its sign-off.
   >
   > Under the heading of each finding (`**On <file>:<line>:**`, a finding on
   > the commit message, avar's `**Behavior change in ...:**` or
   > `**Test coverage gap:**`), add one line:
   >
   > - `Kind: defect — <input or state> → <wrong result>` for a claimed bug,
   >   edge case, regression, missing test for a changed path, or a commit
   >   message that contradicts its diff.
   > - `Kind: opinion` for taste, naming, design, wording, or patch split.
   >
   > Keep a defect you only half believe on the list, with its `Kind:` line. Do
   > not drop it: a separate verifier checks every defect, and a dropped
   > candidate is never checked. Do not edit files, commit, or post anything.

   For `intent`, use this prompt instead:

   > Invoke the `intent-review:intent-review` skill on `<target>`. Follow its
   > Process and Output Format, and start the report with the full paths of the
   > transcripts and of `user_turns.py`. Do not edit files, commit, or post
   > anything.

   intent-review writes its own
   `Kind: intent — <contradicted|misread|unasked|dropped>` lines. When it
   reports that it found no transcript, it is skipped; say so in the report.

3. **Merge.** Collect the findings from the returned reviews. Two findings at
   the same location that describe the same mechanism become one finding that
   names every persona that raised it. Two different claims about the same line
   stay separate. A finding with no `Kind:` line counts as a defect if it claims
   that something breaks, and as an opinion otherwise. When the personas gave a
   merged finding different kinds, it is a defect if any of them called it one.
   An intent finding is never merged with a persona's: one is about what the
   user asked for, the other about the code.

4. **Verify.** For each persona with defect findings, and for `intent` when it
   has findings, start one verifier Agent, all in a single message, with the
   model and effort from Models. A merged defect goes to the verifier of the
   first persona, in the order of the arguments, that called it a defect. Give
   each verifier the target and its numbered list of findings (location, claim,
   and the `Kind:` line), and this prompt:

   > Check each finding against the code in `<target>`. Read the diff and the
   > surrounding code; run read-only commands if that settles it. Do not edit
   > files. Give one verdict per finding:
   >
   > - `CONFIRMED`: quote the line and state the input or state that triggers
   >   the wrong result.
   > - `PLAUSIBLE`: the mechanism is real but the trigger is uncertain. Say what
   >   would confirm it.
   > - `REFUTED`: only when the code proves the claim wrong. Quote the guard,
   >   type, or invariant that does so.
   >
   > A realistic runtime state (a rare error path, a cold cache, a falsy zero,
   > an empty input, a race) is not "speculative". A finding that depends on one
   > stays `PLAUSIBLE`; do not refute it for that reason. Refute only what the
   > code rules out.

   The verifier for intent findings gets the transcript paths and the
   `user_turns.py` path from the start of intent-review's report, instead of the
   code prompt above:

   > Check each finding against the user's turns in these transcripts. Print
   > them with `python3 <user_turns.py> <transcript>...`; only `user`,
   > `answered`, `rejected plan` and `command` turns are the user's words. An
   > approved plan means "go ahead", not agreement with what it says: a decision
   > in the plan, with no turn of the user's on it, stays unasked. Say that the
   > plan states it. Do not edit files. Give one verdict per finding:
   >
   > - `CONFIRMED`: for contradicted or misread, quote the turn and say how the
   >   code departs from it. For unasked, say what you searched for and that no
   >   turn covers the decision. For dropped, quote the request and say where
   >   the diff lacks it.
   > - `PLAUSIBLE`: a turn bears on it, but whether it settles the decision is
   >   unclear. Quote it.
   > - `REFUTED`: only when a turn of the user's backs the decision, or the user
   >   took it when the agent offered it. Quote that turn and its line.

   Opinions are not verified.

5. **Report.** Per commit, in diff order, one entry per finding:

   ```
   <file>:<line> — <claim in one line> [peff, sunshine] CONFIRMED
   ```

   A finding with no line, such as one on the commit message, a test coverage
   gap, a proposed split or a dropped request, uses its own heading in place of
   `<file>:<line>`.

   The tag is `CONFIRMED`, `PLAUSIBLE` (with what would confirm it), or
   `opinion`; an intent finding adds `intent` and its kind
   (`[intent] unasked CONFIRMED`). Under each entry, give the persona's own
   wording and any `something like:` code; for a defect, add the verifier's
   quote and trigger. Commit-message findings go first in their commit.

   After the commits, list the refuted findings, one line each, with the line of
   code or the user's turn that refuted each one. End with counts: findings per
   persona; defects confirmed, plausible and refuted; opinions; and, apart from
   the defects, intent findings confirmed, plausible and refuted. Then the
   confirmed and plausible intent findings, as questions for the user:
   contradicted first, then dropped, then the decisions that are hardest to
   undo.

   Keep the finders' full reports in this context. When asked about a finding,
   answer from the report of the persona that raised it.

   When the target is a range and the user has gone through the findings, run
   `peff-commit:review` on it in this context. It reads the commit messages as a
   stranger would and goes through their notes with the user.

## Important

- **One target for all.** Each finder and verifier gets the same target from
  step 1. Do not let a finder pick its own target.
- **The verifier decides, not the finder.** Finders keep weak defects; verifiers
  refute only with a quote from the code.
- **Read-only.** No agent edits files, commits, pushes, or posts to a PR.
