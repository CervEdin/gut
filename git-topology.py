#!/usr/bin/env python3
"""git-topology: print a forest of branches nested by commit ancestry.

Each branch is shown under its nearest descendant branch -- the branch whose tip
is the closest commit reachable ahead of it. A branch that nothing else in the
set is built on becomes a root (flush left); these are the pure tips. Git does
not record which branch a branch was forked from, so the relationship is
inferred from commit ancestry.

The motivation is selective rebasing. 'git rebase --update-refs' already carries
along any intervening refs that point into the range being replayed, so you only
want to rebase a branch that nothing else sits on top of -- a root here. The
branches nested beneath it are the ones --update-refs moves for you; rebasing
them yourself just duplicates work and, unless you also reset committer dates
back to author dates, scrambles the very topology this tool shows. So the roots
are exactly the set you hand to rebase, and 'git topology | grep -v "^ "' lists
them.

Uses only stdlib subprocess: ref patterns are handed to 'git for-each-ref'
verbatim, preserving git's pattern/glob semantics, and reachability among the
branch tips is computed from a single 'git rev-list' walk.
"""

import subprocess
import sys

USAGE = """\
git topology [<pattern>...]

Print a forest of branches, nesting each branch under its nearest descendant
branch -- the branch whose tip is the closest commit reachable ahead of it. Git
does not record which branch a branch was forked from, so the relationship is
inferred from commit ancestry.

With no arguments all local branches (refs/heads/) are shown. Any arguments are
passed straight to 'git for-each-ref' as ref patterns, e.g.:

  git topology refs/heads/feature/             # only feature branches
  git topology refs/heads/ refs/remotes/origin # include remote-tracking refs

A branch that nothing else in the set is built on -- a pure tip -- is shown
flush left as a root; the branches it sits on top of nest beneath it. Branches
that point at the same commit are each shown as roots.

Note: a branch can be the base of several divergent branches, but a tree can
only nest it under one. It is shown under its nearest descendant (newest tip
wins ties); the others appear elsewhere as their own roots or subtrees.
"""


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def main(patterns: list[str]) -> None:
    # One git process: tip commit, committer date and name for every branch,
    # sorted by name so the rendered tree and tie-breaks are deterministic.
    records = run(
        "git",
        "for-each-ref",
        "--sort=refname",
        "--format=%(objectname)\t%(committerdate:unix)\t%(refname:short)",
        *patterns,
    )

    commit: dict[str, str] = {}      # branch -> tip OID
    cdate: dict[str, int] = {}       # branch -> committer date (unix)
    order: list[str] = []            # branches in refname order
    oid_names: dict[str, list[str]] = {}  # tip OID -> branches pointing at it

    for line in records.splitlines():
        commit_oid, committer_date, name = line.split("\t", 2)
        if not name:
            continue
        commit[name] = commit_oid
        cdate[name] = int(committer_date)
        order.append(name)
        oid_names.setdefault(commit_oid, []).append(name)

    # Reachability among branch tips in ONE git process instead of one
    # 'git for-each-ref --merged <tip>' per branch. Walk every commit reachable
    # from the tips with its parents, then propagate, to each commit, the set of
    # tip OIDs that are ancestors-or-self of it -- a bit per tip OID. rev-list
    # is newest-first, so reversing it visits parents before their children.
    isanc: set[tuple[str, str]] = set()  # (ancestor, descendant) reachability
    desc: dict[str, list[str]] = {name: [] for name in order}  # descends-from-it
    tips = list(oid_names)
    bit = {oid: 1 << i for i, oid in enumerate(tips)}
    if tips:
        graph = run("git", "rev-list", "--topo-order", "--parents", *tips)
        reach: dict[str, int] = {}
        for cline in reversed(graph.splitlines()):
            ids = cline.split()
            mask = bit.get(ids[0], 0)
            for parent in ids[1:]:
                mask |= reach.get(parent, 0)
            reach[ids[0]] = mask
        for name in order:
            mask = reach.get(commit[name], 0)
            for oid in tips:
                if mask & bit[oid]:
                    # Every branch at this ancestor tip is an ancestor of name;
                    # equivalently, name descends from it.
                    for ancestor in oid_names[oid]:
                        isanc.add((ancestor, name))
                        desc[ancestor].append(name)

    def parent_of(b: str) -> str:
        """Nearest descendant branch of b, or "" if it has none.

        Among branches that descend from b, drop b itself and any co-located
        branch, then keep the candidate that no other candidate sits above
        (the closest one ahead). Ties (divergent branches built on the same
        base) go to the newest tip, then the lexically smaller name.
        """
        candidates = [
            x for x in desc.get(b, [])
            if x != b and commit[x] != commit[b]
        ]
        best = ""
        bestd = -1
        for i, x in enumerate(candidates):
            # Drop x if another candidate sits strictly between b and x, i.e.
            # is a strict ancestor of x; the survivors are the closest reachable
            # branches ahead. Compare by index, and ignore co-located candidates
            # (same tip OID), so neither duplicate short-names nor branches that
            # merely share a tip drop each other.
            if any((candidates[j], x) in isanc
                   and commit[candidates[j]] != commit[x]
                   for j in range(len(candidates)) if j != i):
                continue
            if best == "" or cdate[x] > bestd or (cdate[x] == bestd and x < best):
                best = x
                bestd = cdate[x]
        return best

    children: dict[str, list[str]] = {}
    roots: list[str] = []
    for b in order:
        p = parent_of(b)
        if p == "":
            roots.append(b)
        else:
            children.setdefault(p, []).append(b)

    lines: list[str] = []

    def render(node: str, prefix: str) -> None:
        for c in children.get(node, []):
            lines.append(prefix + c)
            render(c, prefix + "    ")

    for r in roots:
        lines.append(r)
        render(r, "    ")

    for line in lines:
        print(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)
    # Default to local branches.
    if not args:
        args = ["refs/heads/"]
    main(args)
