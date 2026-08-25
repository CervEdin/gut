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
   `change`, and usually `today`.
2. The source around each hunk — enough to say what the code does now, not just
   what the patch touches.
3. `git log -10 --no-merges` on the repo, and `git blame`/`git log -L` on the
   touched lines. Commits that introduced the code being changed often carry the
   reason it looked that way.
4. The conversation so far. What did the user actually say about this change?
5. Any issue, PR, or mail thread already in context. Do not go fetch one that
   is not.

## Tags

Every entry carries exactly one tag, and **every tag except `unsourced`
must carry a citation**:

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
about this" — it is a sentence the user wrote.

`asked` never appears in a brief this skill writes; it exists for callers that
interview and re-tag afterwards.

## Fields

- `today` — what the code does now at the change site
- `incident` — what prompted this change, and why now
- `change` — what the diff tells the code to do differently, imperative
- `alternatives` — approaches weighed and rejected, with the reason
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

## Output

Write `.git/commit-brief`. It is untracked by construction, the same way
`.git/peff-commit-draft` is.

One entry per line, `field: [tag] (citation) text`, continuation lines indented
two spaces:

```
today: [code] (odb/loose.c:412) We mmap the object file and keep the result
  in `map`, unmapping it at the `out` label.
incident: [session] ("this segfaults on a truncated pack") Reported against
  a pack truncated mid-write.
change: [diff] (odb/loose.c) Clear `map` after unmapping so the error path
  cannot unmap it a second time.
uncertain: [diff] (odb/loose.c) Whether the v2 reader has the same pattern;
  not checked.
```

Then report to the caller, in two lines: the count of entries by tag, and the
`unsourced` entries in full. The caller needs to see the gaps without opening
the file.
