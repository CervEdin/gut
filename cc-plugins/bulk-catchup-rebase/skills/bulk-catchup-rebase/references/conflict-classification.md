# Classifying a Step 1 / Step 2 conflict stop

When the merge (or rebase) in Step 1 / Step 2 stops with `MERGE_HEAD` (or
`REBASE_HEAD`) set, it's a real conflict, and it splits three ways. This covers
why the checks run in this order and why two of them print output instead of
staying quiet.

## The three categories

- **Structural (add/delete)** — `git status --porcelain` shows a `DU`/`UD`/`AU`/
  `UA`/`DD`/`AA` code. One side deleted a file the other touched, so there's no
  three-way text to merge and no conflict markers are ever written.
- **Manual** — markers are present (`git diff --check` fails): a genuine
  three-way text conflict rerere had no cached answer for.
- **Rerere-resolved** — no markers, and it's not a structural case: rerere
  replayed a cached resolution and the tree came out clean.

## Why the structural check runs first

`git diff --check` only detects leftover conflict markers. A `modify/delete`
conflict never has markers — there's no three-way text to diff, so nothing is
ever written — which means checking markers before checking for the structural
case would read every add/delete stop as a clean rerere replay that never
happened. Checking `git status --porcelain` for the structural codes first
avoids that misread.

## Why the guard commands aren't silenced

Both `grep` and `git diff --check` are left to print their own output instead of
being redirected to `/dev/null`:

- `grep -E '^(DU|UD|AU|UA|DD|AA) '` matched lines are the list of
  structurally-conflicted paths — worth having at the stop rather than
  re-deriving with a second `git status` afterward. The `^` anchor matters: an
  unanchored match risks a false positive against a path that happens to contain
  one of those two-letter codes as a substring (e.g. a file literally named
  `UD file.txt` shows up quoted later on an unrelated status line).
- `git diff --check`'s output is the file:line of each leftover marker, not just
  a pass/fail signal.

Both still gate their `elif` on exit code (grep: `0` matched, `1` no match, `>1`
error); printing their output is a side effect, not a change in behavior.

## Structural and manual are not "hard"

rerere skips add/delete conflicts unconditionally, no matter how many times the
same shape recurs, so a structural stop says nothing about how much thought the
resolution needs. And early in Step 1 the rerere cache starts empty, so nearly
every stop is manual by construction — that's the normal shape of a first pass,
not a run of hard calls. Neither label is a difficulty signal; see the main
skill's Step 2 pacing decision for what actually is.
