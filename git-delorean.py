#!/usr/bin/env python3
"""git-delorean: automatically create fixup commits targeting the right ancestor.

For each modified file, finds which lines changed, blames those lines against
the parent, then identifies the earliest ancestor commit that touched those
lines — i.e. the commit your changes should be a fixup of.

Modes:
  git-delorean [revspec]   Analyze changes in a commit or range (default: HEAD).
  git-delorean --staged    Analyze staged changes and create fixup commits.
"""

import argparse
import re
import subprocess
import sys
from collections.abc import Iterator

_RAW_STATUS_RE = re.compile(r":\d{6} \d{6} [a-f0-9]+ [a-f0-9]+ (M|R\d+)")
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-delorean",
        description="Automatically create fixup commits targeting the right ancestor.",
    )
    parser.add_argument(
        "revspec",
        nargs="?",
        default=None,
        help="commit or range to analyze (default: HEAD)",
    )
    parser.add_argument(
        "--staged",
        "--cached",
        action="store_true",
        dest="staged",
        help="analyze staged changes instead of a commit",
    )
    parser.add_argument(
        "--fixup",
        action="store_true",
        help="analyze staged changes and create fixup commits",
    )
    parser.add_argument(
        "-z",
        action="store_true",
        dest="null",
        help="separate output fields with NUL bytes instead of tabs",
    )
    args = parser.parse_args()
    if args.fixup and args.revspec is not None:
        parser.error("--fixup cannot be combined with a revspec")
    if args.revspec is None:
        args.revspec = "HEAD"
    if args.fixup:
        args.staged = True
    return args


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def resolve_revspec(revspec: str) -> tuple[str, str, str]:
    """Resolve a revspec into (blame_target, diff_base, diff_head).

    The blame_target is the left side of the range — the tree state
    before the changes. diff_base and diff_head are explicit SHAs
    passed to plumbing diff commands.
    """
    parsed = run("git", "rev-parse", revspec).splitlines()
    excluded = [line[1:] for line in parsed if line.startswith("^")]
    if len(excluded) > 1:
        raise ValueError(
            f"revspec '{revspec}' resolves to multiple excluded refs (unsupported)"
        )
    if excluded:
        included = [line for line in parsed if not line.startswith("^")]
        return excluded[0], excluded[0], included[0]
    else:
        sha = parsed[0]
        return f"{sha}^", f"{sha}^", sha


def _parse_raw_header(raw: str) -> list[tuple[str, str]]:
    """Parse the raw section of ``--patch-with-raw -z`` output into file pairs."""
    it = iter(raw.split("\0"))
    result: list[tuple[str, str]] = []
    for token in it:
        m = _RAW_STATUS_RE.match(token)
        if not m:
            continue
        match m.group(1):
            case "M":
                path = next(it)
                result.append((path, path))
            case s if s.startswith("R"):
                old, new = next(it), next(it)
                result.append((new, old))
            case other:
                raise ValueError(f"unexpected diff status: {other!r}")
    return result


def _parse_hunk_ranges(diff_chunk: str) -> list[tuple[int, int]]:
    """Extract ``(start, end)`` line ranges from ``@@`` headers in a diff chunk."""
    ranges: list[tuple[int, int]] = []
    for line in diff_chunk.splitlines():
        m = _HUNK_RE.match(line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        if count == 0:
            ranges.append((start, start))
        else:
            ranges.append((start, start + count - 1))
    return ranges


def diff_line_ranges(
    diff_base: str, diff_head: str, *, staged: bool = False
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """Run a single diff and return changed line ranges keyed by file pair.

    Uses ``--patch-with-raw -z`` so the raw section gives us unambiguous
    NUL-separated paths while the patch section provides ``@@`` hunk headers.

    Returns a dict keyed by ``(new_path, old_path)`` with ``(start, end)``
    tuples suitable for ``git blame -L``.
    """
    args = [
        "git",
        "diff-index" if staged else "diff-tree",
        "-r",
        "--patch-with-raw",
        "-z",
        "--relative",
        "-M",
        "--diff-filter=MR",
        "-U0",
    ]
    if staged:
        output = run(*args, "--cached", diff_head)
    else:
        output = run(*args, diff_base, diff_head)
    if not output:
        return {}

    parts = output.split("\0\0", 1)
    if len(parts) != 2:
        return {}
    header, patch = parts

    file_pairs = _parse_raw_header(header)
    file_diffs = patch.split("diff --git ")[1:]

    return {
        pair: _parse_hunk_ranges(chunk)
        for pair, chunk in zip(file_pairs, file_diffs)
    }


def blame_commits(
    file: str, ranges: list[tuple[int, int]], blame_target: str
) -> set[str]:
    """Run `git blame --incremental` with all ranges and collect unique commit SHAs."""
    cmd = ["git", "blame", "--incremental"]
    for start, end in ranges:
        cmd += ["-L", f"{start},{end}"]
    cmd += [blame_target, "--", file]
    output = run(*cmd, check=False)
    commits: set[str] = set()
    for line in output.splitlines():
        m = re.match(r"^([a-f0-9]{40}) ", line)
        if m:
            commits.add(m.group(1))
    return commits


def find_earliest_ancestor(commits: set[str], topo_target: str) -> str:
    """Walk the topo-ordered rev-list and return the first (earliest) matching commit."""
    with subprocess.Popen(
        ["git", "rev-list", "--topo-order", topo_target],
        stdout=subprocess.PIPE,
        text=True,
    ) as proc:
        assert proc.stdout is not None
        for sha in proc.stdout:
            sha = sha.strip()
            if sha in commits:
                proc.kill()
                return sha
    raise ValueError(f"none of the given commits are ancestors of {topo_target}")


def resolve_blame_targets(
    revspec: str, *, staged: bool = False
) -> Iterator[tuple[str, str, str]]:
    """Yield (new_path, old_path, target_sha) for each file with a fixup target."""
    if staged:
        blame_target = revspec
        diff_base = revspec
        diff_head = revspec
    else:
        blame_target, diff_base, diff_head = resolve_revspec(revspec)

    all_ranges = diff_line_ranges(diff_base, diff_head, staged=staged)
    if not all_ranges:
        if staged:
            print("No fixup targets found in staged changes.", file=sys.stderr)
        else:
            print(f"No file changes found in {revspec}.", file=sys.stderr)
        return

    for (new_path, old_path), ranges in all_ranges.items():
        if not ranges:
            # TODO: pure renames should target the commit that last added/renamed
            # the file (e.g. git rev-list <target> -- <path> | tail -n 1)
            continue
        commits = blame_commits(old_path, ranges, blame_target)
        if not commits:
            continue

        target = find_earliest_ancestor(commits, blame_target)
        display = f"{old_path} => {new_path}" if old_path != new_path else new_path
        if not target:
            print(
                f"Warning: no ancestor commit found for {display}, skipping.",
                file=sys.stderr,
            )
            continue

        yield new_path, old_path, target


def analyze(revspec: str, *, staged: bool = False, null: bool = False) -> None:
    """Print fixup targets to stdout."""
    for new_path, old_path, target in resolve_blame_targets(revspec, staged=staged):
        display = f"{old_path} => {new_path}" if old_path != new_path else new_path
        fmt = "%h%x00%s" if null else "%h%x09%s"
        info = run(
            "git",
            "rev-list",
            "--max-count=1",
            "--no-commit-header",
            f"--format={fmt}",
            target,
        )
        sep = "\0" if null else "\t"
        end = "\0" if null else "\n"
        sys.stdout.write(f"{display}{sep}{info}{end}")


def create_fixups(revspec: str) -> None:
    """Create fixup commits for staged changes."""
    working_tree_sha = run("git", "stash", "create")
    run("git", "stash", "--keep-index")
    try:
        for new_path, _old_path, target in resolve_blame_targets(revspec, staged=True):
            run("git", "commit", "--fixup", target, "--", new_path)
    finally:
        if working_tree_sha:
            run("git", "stash", "apply", working_tree_sha, "--index", check=False)


def main(
    revspec: str, *, staged: bool = False, fixup: bool = False, null: bool = False
) -> None:
    if fixup:
        create_fixups(revspec)
    else:
        analyze(revspec, staged=staged, null=null)


if __name__ == "__main__":
    args = parse_args()
    main(args.revspec, staged=args.staged, fixup=args.fixup, null=args.null)
