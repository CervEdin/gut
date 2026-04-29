# Rerolling a patch series

CONTRIBUTING.md expects v2+ rerolls to carry a range-diff against the previous
version. That requires the previous tip to stay reachable, so tag every version
at send time — not after. Without a tag the old tip lives only in reflog (90-day
TTL), and the range-diff becomes irreproducible once it expires or the branch is
force-pushed.

Tag convention: `<topic>/v<N>`, e.g. `arch-points-at/v1`, `arch-points-at/v2`.
Lightweight tags are fine; they're immutable and survive any later rebase.

The `--range-diff` argument takes **two different forms** depending on context:

- **Single-patch reroll**: `--range-diff=<prev-tag>` — a bare tag, not a range.
  `git format-patch` compares `<prev-tag>..<prev-tag>` against
  `origin/main..HEAD` automatically. Passing `A..B` here silently produces an
  _empty_ range-diff because both sides resolve to the same one-commit range.
- **Series with a cover letter**: `--range-diff=<prev-v-tag>..<this-v-tag>` —
  the range form. The cover letter needs both endpoints so it can render a
  series-wide range-diff in its own body.

Single-patch v2+ invocation:

```
git tag arch-points-at/v2 HEAD

git send-email \
  --from 'Claude <claude@gut.local>' \
  -v2 \
  --range-diff=arch-points-at/v1 \
  --notes \
  origin/main..arch-points-at/v2
```

Series with cover letter:

```
git tag arch-points-at/v2 HEAD

git send-email \
  --from 'Claude <claude@gut.local>' \
  -v2 \
  --cover-letter \
  --range-diff=arch-points-at/v1..arch-points-at/v2 \
  --notes \
  origin/main..arch-points-at/v2
```

The range-diff lands at the **end** of each patch message, below the diff and
just above the `-- \n<git-version>` sign-off. (The format-patch man page says
"between the commit message and the diff", but observed behavior for
single-patch rerolls puts it at the bottom. `git notes` / `--notes` is what goes
between the commit message and the diff.) Skim to the bottom when checking a
received reroll.

Per-version prose — "Changes since v1: addressed Erik's POSIX comment" — goes
into `git notes` on the tip commit and is picked up by `--notes`:

```
git notes add -m "Changes since v1:
- tighten the ref-resolution case Erik pointed out on-list
- POSIX-ify the awk call" <tip-sha>
```

**Retrofit**: if v1 wasn't tagged (true for pre-existing series — arch, etc.),
apply the v1 patches onto a scratch branch off `origin/main` and tag that commit
`<topic>/v1`. From there the normal flow works.
