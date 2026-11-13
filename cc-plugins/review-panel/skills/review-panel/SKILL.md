---
name: review-panel
description: >-
  Run several persona reviews (peff, gitster, sunshine, avar, comment) on the
  same commits as independent parallel agents, merge their findings, and have
  separate verifier agents confirm or refute each claimed defect against the
  code. Opinions on naming, design and patch split are passed through without
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
  `comment`. Default: all five.
- **target**: a range, a branch, or a PR. Default: the rule in step 1.

Example: `/review-panel peff,sunshine main..topic`.

## Models

Each agent gets the model and effort of its role, unless the user names another
for the run, for a persona, or for the verifiers:

- Finders: `model: sonnet`, no `effort`.
- Verifiers: `model: sonnet`, `effort: high`. Each defect gets one verdict and
  no second reader, so the effort goes to the verifier.

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

3. **Merge.** Collect the findings from the returned reviews. Two findings at
   the same location that describe the same mechanism become one finding that
   names every persona that raised it. Two different claims about the same line
   stay separate. A finding with no `Kind:` line counts as a defect if it claims
   that something breaks, and as an opinion otherwise. When the personas gave a
   merged finding different kinds, it is a defect if any of them called it one.

4. **Verify defects.** For each persona with defect findings, start one verifier
   Agent, all in a single message, with the model and effort from Models. A
   merged defect goes to the verifier of the first persona, in the order of the
   arguments, that called it a defect. Give each verifier the target and its
   numbered defect list (location, claim, and the `Kind:` trigger), and this
   prompt:

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

   Opinions are not verified.

5. **Report.** Per commit, in diff order, one entry per finding:

   ```
   <file>:<line> — <claim in one line> [peff, sunshine] CONFIRMED
   ```

   A finding with no line, such as one on the commit message, a test coverage
   gap or a proposed split, uses its own heading in place of `<file>:<line>`.

   The tag is `CONFIRMED`, `PLAUSIBLE` (with what would confirm it), or
   `opinion`. Under each entry, give the persona's own wording and any
   `something like:` code; for a defect, add the verifier's quote and trigger.
   Commit-message findings go first in their commit.

   After the commits, list the refuted findings, one line each, with the line of
   code that refuted each one. End with counts: findings per persona, and
   defects confirmed, plausible and refuted, and opinions.

   Keep the finders' full reports in this context. When asked about a finding,
   answer from the report of the persona that raised it.

## Important

- **One target for all.** Each finder and verifier gets the same target from
  step 1. Do not let a finder pick its own target.
- **The verifier decides, not the finder.** Finders keep weak defects; verifiers
  refute only with a quote from the code.
- **Read-only.** No agent edits files, commits, pushes, or posts to a PR.
