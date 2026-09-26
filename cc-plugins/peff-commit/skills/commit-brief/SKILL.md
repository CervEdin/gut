---
name: commit-brief
description: >-
  Gather the evidence behind a change and record it as a sourced brief before
  any commit message is written — what the code does today, what prompted the
  change, what it does differently, what alternatives were weighed, what was
  deliberately left out. Every claim is tagged with where it came from, so
  anything the model merely inferred is visible as an inference. Use it before
  writing a commit message, a PR description, or a patch series cover letter.
disable-model-invocation: false
---

# commit-brief

Collect what is actually known about a change, and record where each piece came
from. This runs before any prose exists. It writes evidence, not sentences.

The point is the source tags. A commit message that invents a motivation reads
exactly like one that reports a real motivation, so the invention is invisible
once it is prose. Tagging each claim at the moment it is collected — while it is
still obvious whether it was read or assumed — is what keeps the distinction
alive long enough for the message to respect it.

This skill never asks the user anything. It gathers what is there and marks what
is missing. Whoever calls it decides what to do about the gaps.

## Gather

Work from cheapest to most expensive and stop when a field is answered:

1. `git diff --cached` (or `git diff` if nothing is staged). This always answers
   `change`, and usually `today`. When rewording an existing commit, use
   `git show <sha>`, one brief per commit; see "Rewording existing commits" in
   `../peff-commit/COMPOSE.md`.
2. The source around each hunk — enough to say what the code does now, not just
   what the patch touches.
3. `git log -10 --no-merges` on the repo, and `git blame`/`git log -L` on the
   touched lines. Commits that introduced the code being changed often carry the
   reason it looked that way.
4. The rest of this branch: `git log --oneline @{upstream}..HEAD`, or
   `main..HEAD` where there is no upstream. These are the commits a `series`
   entry can point back to; anything older is ordinary history.
5. The conversation so far. What did the user actually say about this change?
   This is also the only place a _following_ commit can come from — the repo
   cannot know what has not been written yet.
6. Any issue, PR, or mail thread already in context. Do not go fetch one that
   is not.

## Tags

Every entry carries exactly one tag, and **every tag except `unsourced` must
carry a citation**:

| tag         | citation required               |
| ----------- | ------------------------------- |
| `diff`      | `path` or `path:line`           |
| `code`      | `path:line`                     |
| `blame`     | abbreviated sha                 |
| `session`   | a direct quote of what was said |
| `issue`     | identifier or URL               |
| `asked`     | the question that was answered  |
| `unsourced` | none — this is the inference    |

If you cannot produce the citation, the tag is wrong and the entry is
`unsourced`. This is the whole mechanism: a tag you cannot back is a guess
wearing a label. `session` in particular is not "the conversation was broadly
about this" — it is a sentence the user wrote, not one you wrote yourself.

A long session accumulates your own plans, running commentary, and mid-task
calls ("let's rename this because X") in the same context window as anything the
user actually said, and by the time you write the brief they read just as
settled either way — nothing marks "I decided this three turns ago" apart from
"this was already true." Quoting your own earlier turn back to yourself is not a
citation; it's the same inference wearing a timestamp. If the sentence you are
about to cite came from an assistant turn rather than the user, the entry is
`unsourced`.

`asked` never appears in a brief this skill writes; it exists for callers that
interview and re-tag afterwards.

## Fields

- `today` — what the code does now at the change site
- `incident` — what prompted this change, and why now. Narrower legal tags than
  the table above: `asked`, `session`, `issue`, or `unsourced` only — never
  `diff`, `code`, or `blame`. Those three can tell you what the code does and
  when it started; they cannot tell you why anyone wanted it to. "This mirrors
  how an existing field already works" is a `code` fact about the change, not a
  fact about the motive — tagging it `code` and calling `incident` answered is
  exactly the mistake this rule exists to close. If the only thing you have is a
  diff or the commit that introduced the touched code, the entry is `unsourced`.
- `change` — what the diff tells the code to do differently, imperative
- `alternatives` — approaches weighed and rejected, with the reason
- `series` — what a neighbouring commit on this branch does, by position
- `deferred` — what follows naturally from this but is deliberately not done
- `uncertain` — what you do not know

Only `change` is guaranteed answerable; it comes off the diff. `today` usually
follows from the code. `incident` is the field that is most often `unsourced`,
because the reason for a change frequently exists nowhere in the repository.
That is a fact about the change, not a failure of the search — record it and
move on.

**Omit a field entirely rather than filling it.** An absent `alternatives` means
none were weighed, which is the ordinary case; an `alternatives` entry invented
to look thorough is worse than nothing, because it will be repeated downstream
as though someone had actually considered it. The same goes for `deferred`.

`series` is for work that spans commits: a preparation whose payoff lands in the
next one, a fix that only reads as a fix because the previous one moved the
code. Write it by position — "the previous commit", "the next commit" — and
never by sha. A topic gets rebased before anyone else sees it, so every sha in
it is provisional while the position holds.

The citation is a separate question from the text. A commit already on the
branch is evidence you can go and read, so cite it however you found it; a sha
in the citation is fine, because the citation never reaches the message — only
a sha on the mainline is fit to be written into one. A commit that does not
exist yet is not in the repository at all, so it is `session` with the sentence
that promised it, or it is `unsourced`.

## Output

Write the brief to the commit-brief file. `.git` is a plain directory in an
ordinary checkout, but a _file_ pointing elsewhere inside a worktree, so
`.git/commit-brief` only works by accident there; resolve the real path with
`git rev-parse --git-path commit-brief` and write to that instead. It is
untracked by construction, the same way the `peff-commit-draft` file
(`git rev-parse --git-path peff-commit-draft`) is.

One entry per line, `field-N: [tag] (citation) text`, continuation lines
indented two spaces. The ID is the field name and a number that counts up per
field — `today-1`, `today-2`, `incident-1` — and it is how `COMPOSE.md` traces
each sentence of the message back to the entry it came from. Lines starting with
`#` are comments.

```
today-1: [code] (odb/loose.c:412) We mmap the object file and keep the result
  in `map`, unmapping it at the `out` label.
incident-1: [session] ("this segfaults on a truncated pack") Reported against
  a pack truncated mid-write.
change-1: [diff] (odb/loose.c) Clear `map` after unmapping so the error path
  cannot unmap it a second time.
series-1: [session] ("then do the same for the v2 reader") The next commit
  applies the same fix to the v2 reader.
uncertain-1: [unsourced] Whether the v2 reader has the same pattern; not
  checked.
```

A gap goes under the field it belongs to, tagged `[unsourced]`. There is no
`unsourced` field. This form is wrong, because it loses which question the gap
leaves open:

```
unsourced: Why Drafts was orphaned comes from my IMAP checks.
```

Write it as `incident-2: [unsourced] Why Drafts was orphaned ...` instead.

Then lint the file:

```
python3 <dir holding this file>/scripts/lint_brief.py "$(git rev-parse --git-path commit-brief)"
```

It prints `line N: reason` for each malformed entry and exits non-zero. Fix the
file and run it again until it passes; do not report a brief it rejects. On a
pass it prints the entry count by tag.

Then report to the caller, in two lines: the count of entries by tag, and the
`unsourced` entries in full. The caller needs to see the gaps without opening
the file.
