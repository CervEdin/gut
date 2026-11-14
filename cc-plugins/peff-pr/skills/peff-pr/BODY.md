# The PR body

The body is everything after the opening. Its reader has already decided to care
and has the commit list and the diff a click away. The body is a map for that
reviewer and a record of what was decided: which commit to read first, and what
was weighed and dropped, none of which the diff shows.

## Rules

The rules come from 160 cover letters Jeff King (peff) sent to the git mailing
list. The quotes are his; the before -> after examples are invented GitHub
bodies. The quotes show the move, not the wording: write in GitHub terms
(commit, not patch; request a review or @-mention, not cc). GitHub records each
push, so a PR body needs none of his range-diffs.

- **Length follows findings.** Write what you found out or decided, and stop.
  Short is normal: 55 % of his letters are under 10 lines. A one-commit PR whose
  opening says everything needs no body. A body padded toward a typical length
  without findings has to invent them.
- **Continue the thread.** When an issue or a discussion came first, link it
  with a clause saying what it is, and start where it ended. Do not repeat what
  it says; the reader would ask "didn't the issue already say that?" Say what
  changed since: what turned up when you tried, which suggestion you took.
  "Fixes #N" goes here.
  - "And here's the patch to fix it. There was a small cleanup needed, hence the
    2-patch series."
  - "As discussed in #212, exports time out on large projects. This PR adds
    streaming ..." -> "Fixes #212 (exports timing out on large projects).
    Streaming, as suggested there, was not enough: the CSV writer still held the
    whole file, so the second commit replaces it."
- **Say how it was found.** Name the tool, the report, or what you were doing
  when it turned up: a CI job, a leak checker, a user's report, an upgrade.
  Usually one sentence. How the code failed stays in the commit.
  - "After upgrading my Debian unstable box to libcurl 8.18.0~rc2-1, I noticed a
    few new test failures."
- **Give the map.** Say which commit is the fix and which are preparation or
  cleanup, which is risky or optional, which could be merged alone, and the
  order to read them in when it differs from the commit order. Name a commit by
  its position ("the third commit") or its subject. GitHub lists the commits;
  never reproduce the list. In a long PR, point at the few commits that need
  thought.
  - "The first one actually fixes a bug. The second is a cleanup, and the rest
    are just UNUSED annotations (but grouped into similar cases)."
  - "If you really want to put on your thinking cap, try patches 7, 14, and 21"
    (a 28-patch series)
  - "Changes: add a retry helper; use it in the uploader; remove the old retry
    loop; add tests" -> "The second commit is the fix. The first adds the helper
    it uses and the third deletes the loop it replaces. Read the tests in the
    last one first."
- **Point to the commit; do not restate it.** The commit message carries the
  mechanism and the measurements. The body says which commit has them, so the
  reviewer never asks "didn't the commit already say that?" Evidence the opening
  left out goes in the body only when no commit carries it. A commit outside the
  PR, when it is cited, is cited as `git show -s --format=reference` prints it,
  never as a bare date.
  - "A fix is in the final patch, along with a detailed explanation."
  - "The cache key was built from the path alone, so two tenants with the same
    path shared an entry. The fix adds the tenant id to the key ..." -> "The
    third commit explains why the tenant id has to be part of the cache key."
- **Argue an alternative only when a reviewer would ask "why not the obvious
  way?"** Say what it would cost and why you did not take it.
  - "The obvious alternative is to actually implement wrappers for other
    systems, and then use it everywhere. That doesn't buy us much for this
    problem ..."
- **Say what was left out, and why.** A reviewer who sees a neighbouring problem
  untouched will ask about it. Name it and say why it is not here.
  - "That may be something we want to put some configurable boundaries on, but I
    punted on it for this series. IMHO it is a lot less interesting since you'd
    usually have to authenticate to invoke receive-pack in the first place."
- **Hedge only where you are unsure, and flag the risky commit.** When you are
  not sure a commit is a good idea, name that commit, so it can be dropped
  without the rest.
  - "I'm actually not sure if the final patch is a good idea or not, but
    certainly all of the fixes leading up to it are worth doing."
- **State verification only when it goes beyond CI.** GitHub shows the checks.
  Say what else you ran, such as a sanitizer build or a run on production-sized
  data. Leave out "tests pass".
  - "It passes the regular test suite, as well as with LSan, ASan, and UBSan."
- **When you ask someone to look, say why.** Request a review from them on the
  PR, or mention the account with @, then give the reason in the body in one
  clause: they wrote the code, or they raised the issue.
  - "I'm cc-ing Stolee as the last person unfortunate enough to have touched
    this area."
  - "PTAL" -> "I requested Priya as a reviewer because she wrote the lease
    code."
- **Say the base and the urgency when they matter.** If the PR is stacked on
  another branch or must land after another PR, name it and say whether this one
  could go in alone. If it is urgent, or can wait, say so and why.
  - "I built it on top of what you have queued in
    jc/ci-upload-artifact-and-linux32, but it could be applied separately"
  - "Not urgent, as they are quite old, but they are newly triggered in the test
    suite by Harald's hn/status-compare-with-push topic."
- **Propose; do not ask the reviewer to choose.** A choice goes on the issue.
  Flagging a commit that can be dropped is not such a choice: the change stands
  either way. The one exception is a draft PR whose point is the question
  whether the direction is right at all: "And of course the most important
  question is: do we like this direction overall."
- **After review, comment; do not rewrite the body.** When you push changes for
  review, add a comment saying what changed and what you chose not to change,
  with the reason. Credit the reviewer in a clause. Do not restate the
  motivation: the reviewer has read it. When a force-push makes the compare view
  hard to follow, say which commit to read again. Edit the body only when its
  map no longer matches the commits.
  - "fixed typos noticed by Patrick"
  - "The only thing I punted on was refactoring the GIT_COLOR_* defines, as I
    think it extends well beyond the code I'm touching here"

**Voice.** The body keeps the opening's direct style and adds first person for
what you found and decided ("I noticed", "I left out"). Past tense for what
happened, present tense for what the code does. Plain paragraphs, with a
numbered list only for distinct alternatives.

**What stays out.**

- Headings: Summary, Overview, Changes, Testing, Motivation. None of the 133
  first-version letters has one.
- A section of benefits or expected outcomes. A benefit the opening has not
  stated is a clause in a sentence.
- "This PR" and "This change". The reader knows which PR they are reading.
- Anything the opening already said, beyond the clause that names the issue.

## Checklist

Every line must be yes, or not apply.

- [ ] Has only what was found out or decided, with no padding
- [ ] If it continues an issue or discussion, links it and does not repeat it
- [ ] If the problem was found and not planned, says how it was found
- [ ] Says which commit is the fix and which are preparation or cleanup
- [ ] Names commits by position or subject, and has no list of them
- [ ] Points to the commit for mechanism and numbers, does not restate them
- [ ] Each alternative argued is one a reviewer would raise, with its cost
- [ ] If something was left out, says what and why
- [ ] If unsure of a commit, names it; hedges nowhere else
- [ ] Mentions verification only when it goes beyond CI
- [ ] When a review is requested or an account mentioned, says why
- [ ] If the base branch, stacking or urgency matter, states them
- [ ] Proposes one change; asks a question only in a draft about direction
- [ ] No headings, no benefit section, no "this PR"

## Example

A 4-commit PR, with its title and opening shown. The body is 141 words.

```
Stop slow workers sending the same invoice email twice

The queue leases an invoice job to a worker for 30 seconds, then hands it to
a second worker even if the first is still sending. Support has had about 40
reports since March.

Fixes #318 (duplicate invoice emails). I confirmed the cause by holding a
worker in a debugger past its lease; the email went out twice.

The second commit is the fix. The first adds the setting it reads, and the
last removes the workaround it replaces. The third is a guard that can be
dropped: it needs a migration, and the fix stands without it.

Raising the timeout would only move the line, because a large enough invoice
outlasts any limit. It would also delay the retry when a worker dies. The
second commit explains why the lease is renewed at a third of its length.

The report export has the same race, but an export that runs twice does no
harm, so I left it for a later PR.

I requested Priya as a reviewer because she wrote the lease code.
```

What is not there: how the fix and the guard work, which their commits explain,
and the second worker the opening already describes.

## Provenance

**Length.** Peff's own prose in words, over the 133 letters he posted as first
versions. Quoted reply text, his "[i/N]: subject" patch list, the diffstat and
the signature are excluded.

**Do not copy these numbers.** His words record things he found out or decided,
and the count includes what here is the opening paragraph. Length tracks the
number of commits only weakly, with a correlation of about 0.3. Some of his
series of 20 patches or more get 4 to 8 lines, and his seven longest letters,
about 300 to 550 words, span 2 to 20 patches.

| commits | n   | p25 | median | p75 |
| ------- | --- | --- | ------ | --- |
| 1-2     | 32  | 43  | 77     | 101 |
| 3-5     | 57  | 53  | 87     | 115 |
| 6-10    | 26  | 72  | 88     | 204 |
| 11+     | 18  | 84  | 169    | 236 |
