# rerere cheatsheet

The rerere porcelain — use it to confirm what rerere recorded or replayed for a
specific conflict, and to locate the cache directory when you need it.

## Inspecting a resolution

Ask rerere directly with its porcelain commands:

- `git rerere status` — while stopped at a conflict, prints the paths whose
  resolution rerere will record.
- `git rerere remaining` — prints the paths still conflicted that rerere did
  _not_ autoresolve, including kinds it cannot track (conflicting submodules,
  `CONFLICT (modify/delete)`). Empty output plus a clean tree means rerere
  replayed a cached resolution — the direct answer to "did rerere resolve this,
  or must I still do it by hand?"
- `git rerere diff` — shows the resolution rerere recorded or replayed for the
  conflicted paths (conflicted state → resolved state). Read this to confirm
  _what_ rerere applied; it is the evidence the Step 1 / Step 2 audit needs, so
  a replayed resolution earns its trust the same way a hand-resolved one does.
- `git rerere forget <pathspec>` — drop the cached resolution for matching paths
  while still in the conflicted state (used in the corrupted-stage pitfall).

`git rerere` also has `gc` and `clear` for pruning the cache; don't run them
mid-rebase. (Note that a periodic `git gc` prunes recorded resolutions on its
own — see the cache-expiry pitfall in SKILL.md.)

## Where the cache lives

On the rare occasion you need the cache directory itself, resolve its path with:

```sh
git rev-parse --git-path rr-cache
```

This is correct in a plain clone, the main checkout, and a **linked worktree**
alike. It matters because this skill may run in a worktree, where `.git` is a
_file_ pointing at the common git dir and the rerere cache is shared from there
— so `git rev-parse --git-path` resolves it wherever it actually is, which an
assumed `.git/rr-cache` would not.
