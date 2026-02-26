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
import dataclasses
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator


@dataclasses.dataclass
class BlameTarget:
    new_path: str
    old_path: str
    target: str
    ranges: list[tuple[int, int]]


_RAW_STATUS_RE = re.compile(r":\d{6} \d{6} [a-f0-9]+ [a-f0-9]+ (M|R\d+)")
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")
_HUNK_NEW_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


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
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--fixup",
        action="store_true",
        help="analyze staged changes and create fixup commits",
    )
    action_group.add_argument(
        "--squash",
        action="store_true",
        help="analyze staged changes and create squash commits",
    )
    parser.add_argument(
        "-c",
        "--reedit-message",
        dest="reedit_message",
        metavar="commit",
        help="reuse and edit message from commit (requires --squash)",
    )
    parser.add_argument(
        "-C",
        "--reuse-message",
        dest="reuse_message",
        metavar="commit",
        help="reuse message from commit (requires --squash)",
    )
    parser.add_argument(
        "--group",
        action="store_true",
        help="treat all changes as one unit targeting the first ancestor found",
    )
    parser.add_argument(
        "-z",
        action="store_true",
        dest="null",
        help="separate output fields with NUL bytes instead of tabs",
    )
    args = parser.parse_args()
    if (args.fixup or args.squash) and args.revspec is not None:
        parser.error("--fixup/--squash cannot be combined with a revspec")
    if (args.reedit_message or args.reuse_message) and not args.squash:
        parser.error("-c/-C requires --squash")
    if args.revspec is None:
        args.revspec = "HEAD"
    if args.fixup or args.squash:
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


def _parse_new_hunk_ranges(diff_chunk: str) -> list[tuple[int, int]]:
    """Extract new-side ``(start, end)`` line ranges from ``@@`` headers."""
    ranges: list[tuple[int, int]] = []
    for line in diff_chunk.splitlines():
        m = _HUNK_NEW_RE.match(line)
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
        pair: _parse_hunk_ranges(chunk) for pair, chunk in zip(file_pairs, file_diffs)
    }


def blame_ranges(
    file: str, ranges: list[tuple[int, int]], blame_target: str
) -> Iterator[tuple[str, tuple[int, int]]]:
    """Stream ``(commit_sha, (start, end))`` from ``git blame --incremental``.

    Yields one pair per blame block, in line order (top of file first).
    """
    cmd = ["git", "blame", "--incremental"]
    for start, end in ranges:
        cmd += ["-L", f"{start},{end}"]
    cmd += [blame_target, "--", file]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            m = re.match(r"^([a-f0-9]{40}) \d+ (\d+) (\d+)$", line)
            if m:
                final_start = int(m.group(2))
                num_lines = int(m.group(3))
                block_end = final_start + num_lines - 1 if num_lines > 0 else final_start
                yield m.group(1), (final_start, block_end)


def find_first_reachable(commits: set[str], walk_start: str) -> str:
    """Walk topo-order from *walk_start* and return the first commit in *commits*."""
    if walk_start in commits:
        return walk_start
    with subprocess.Popen(
        ["git", "rev-list", "--topo-order", walk_start],
        stdout=subprocess.PIPE,
        text=True,
    ) as proc:
        assert proc.stdout is not None
        for sha in proc.stdout:
            sha = sha.strip()
            if sha in commits:
                proc.kill()
                return sha
    raise ValueError(f"none of the given commits are reachable from {walk_start}")


def find_grouped_target(targets: set[str], walk_start: str) -> str:
    """Return the first commit from *targets* reachable from *walk_start*."""
    if len(targets) == 1:
        return next(iter(targets))
    return find_first_reachable(targets, walk_start)


def _ranges_overlap(
    a: list[tuple[int, int]], b: list[tuple[int, int]], margin: int = 3
) -> bool:
    """Return True if any range from *a* is within *margin* lines of any range from *b*."""
    for a_start, a_end in a:
        for b_start, b_end in b:
            if a_start - margin <= b_end and b_start - margin <= a_end:
                return True
    return False


def check_commutability(
    file: str,
    fixup_ranges: list[tuple[int, int]],
    target: str,
    walk_start: str,
) -> list[tuple[str, str]]:
    """Return (short_hash, subject) for intermediate commits that overlap fixup ranges."""
    intermediates = run(
        "git", "rev-list", f"{target}..{walk_start}", "--", file, check=False
    )
    if not intermediates:
        return []
    conflicts: list[tuple[str, str]] = []
    for sha in intermediates.splitlines():
        diff_output = run(
            "git", "diff-tree", "-r", "-U0", f"{sha}^", sha, "--", file, check=False
        )
        if not diff_output:
            continue
        intermediate_ranges = _parse_new_hunk_ranges(diff_output)
        if not intermediate_ranges:
            continue
        if _ranges_overlap(fixup_ranges, intermediate_ranges):
            info = run(
                "git",
                "rev-list",
                "--max-count=1",
                "--no-commit-header",
                "--format=%h%x00%s",
                sha,
            )
            short_hash, subject = info.split("\0", 1)
            conflicts.append((short_hash, subject))
    return conflicts


def _format_rename(old_path: str, new_path: str) -> str:
    """Format a file path, showing rename arrow when old and new differ."""
    if old_path != new_path:
        return f"{old_path} => {new_path}"
    return new_path


def resolve_blame_targets(
    revspec: str, *, staged: bool = False
) -> Iterator[BlameTarget]:
    """Yield a BlameTarget for each file with a fixup target."""
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
        for sha, rng in blame_ranges(old_path, ranges, blame_target):
            yield BlameTarget(new_path, old_path, sha, [rng])


def analyze(
    revspec: str, *, staged: bool = False
) -> Iterator[tuple[str, str, str, str, str]]:
    """Yield (new_path, old_path, target_sha, short_hash, subject) per fixup target."""
    for bt in resolve_blame_targets(revspec, staged=staged):
        info = run(
            "git",
            "rev-list",
            "--max-count=1",
            "--no-commit-header",
            "--format=%h%x00%s",
            bt.target,
        )
        short_hash, subject = info.split("\0", 1)
        yield bt.new_path, bt.old_path, bt.target, short_hash, subject


def create_fixups(
    targets: dict[str, list[str]],
    *,
    mode: str = "fixup",
    reedit_message: str | None = None,
    reuse_message: str | None = None,
) -> None:
    """Create fixup or squash commits for staged changes."""
    working_tree_sha = run("git", "stash", "create")
    run("git", "stash", "--keep-index")
    try:
        for target, paths in targets.items():
            cmd = ["git", "commit", f"--{mode}", target]
            if reedit_message:
                cmd += ["-c", reedit_message]
            if reuse_message:
                cmd += ["-C", reuse_message]
            cmd += ["--", *paths]
            run(*cmd)
    finally:
        if working_tree_sha:
            run("git", "stash", "apply", working_tree_sha, "--index", check=False)


def collapse_fixup_targets(
    results: list[BlameTarget], topo_ref: str
) -> dict[str, list[str]]:
    """Collapse per-hunk blame targets to one target per file for fixup creation.

    When hunks in the same file point at different commits, picks the earliest
    ancestor and warns.
    """
    file_targets: dict[str, set[str]] = defaultdict(set)
    for bt in results:
        file_targets[bt.new_path].add(bt.target)

    collapsed: dict[str, str] = {}
    for f, ts in file_targets.items():
        if len(ts) > 1:
            chosen = find_grouped_target(ts, topo_ref)
            collapsed[f] = chosen
            print(
                f"Warning: {f} has hunks targeting different commits; "
                f"collapsing to {run('git', 'rev-parse', '--short', chosen)}.",
                file=sys.stderr,
            )

    targets: dict[str, list[str]] = {}
    seen_files: set[str] = set()
    for bt in results:
        if bt.new_path in seen_files:
            continue
        target = collapsed.get(bt.new_path, bt.target)
        targets.setdefault(target, []).append(bt.new_path)
        seen_files.add(bt.new_path)
    return targets


def main(
    revspec: str,
    *,
    staged: bool = False,
    fixup: bool = False,
    squash: bool = False,
    reedit_message: str | None = None,
    reuse_message: str | None = None,
    group: bool = False,
    null: bool = False,
) -> None:
    results = list(resolve_blame_targets(revspec, staged=staged))

    if staged:
        topo_ref = head_ref = revspec
    else:
        resolved = resolve_revspec(revspec)
        topo_ref, head_ref = resolved[0], resolved[2]

    if group and results:
        all_targets = {bt.target for bt in results}
        grouped = find_grouped_target(all_targets, topo_ref)
        for bt in results:
            bt.target = grouped

    commute_groups: dict[tuple[str, str, str], list[tuple[int, int]]] = {}
    for bt in results:
        key = (bt.old_path, bt.new_path, bt.target)
        commute_groups.setdefault(key, []).extend(bt.ranges)
    for (old_path, new_path, target), ranges in commute_groups.items():
        conflicts = check_commutability(old_path, ranges, target, topo_ref)
        for short_hash, subject in conflicts:
            print(
                f"Warning: {_format_rename(old_path, new_path)}: fixup may not commute past {short_hash} ({subject})",
                file=sys.stderr,
            )

    if fixup or squash:
        targets = collapse_fixup_targets(results, topo_ref)
        create_fixups(
            targets,
            mode="squash" if squash else "fixup",
            reedit_message=reedit_message,
            reuse_message=reuse_message,
        )
        return

    sep = "\0" if null else "\t"
    end = "\0" if null else "\n"
    seen: set[tuple[str, str]] = set()
    for bt in results:
        key = (bt.new_path, bt.target)
        if key in seen:
            continue
        seen.add(key)
        info = run(
            "git",
            "rev-list",
            "--max-count=1",
            "--no-commit-header",
            "--format=%h%x00%s",
            bt.target,
        )
        short_hash, subject = info.split("\0", 1)
        sys.stdout.write(
            f"{_format_rename(bt.old_path, bt.new_path)}{sep}{short_hash}{sep}{subject}{end}"
        )


if __name__ == "__main__":
    args = parse_args()
    main(
        args.revspec,
        staged=args.staged,
        fixup=args.fixup,
        squash=args.squash,
        reedit_message=args.reedit_message,
        reuse_message=args.reuse_message,
        group=args.group,
        null=args.null,
    )
