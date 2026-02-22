#!/usr/bin/env python3
"""git-delorean: automatically create fixup commits targeting the right ancestor.

For each modified file, finds which lines changed, blames those lines against
the parent, then identifies the earliest ancestor commit that touched those
lines — i.e. the commit your changes should be a fixup of.

Modes:
  git-delorean [revspec]   Analyze changes in a commit (default: HEAD).
  git-delorean --staged    Analyze staged changes and create fixup commits.
"""

import argparse
import re
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-delorean",
        description="Automatically create fixup commits targeting the right ancestor.",
    )
    parser.add_argument(
        "revspec",
        nargs="?",
        default="HEAD",
        help="commit to analyze (default: HEAD)",
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
    if args.fixup:
        args.staged = True
    return args


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def _parse_name_status_z(raw: str) -> list[tuple[str, str]]:
    """Parse NUL-separated `git diff --name-status -z` output.

    Format: M\0path\0  or  Rnnn\0old\0new\0
    """
    it = iter(raw.split("\0"))
    result: list[tuple[str, str]] = []
    for status in it:
        if status == "M":
            path = next(it)
            result.append((path, path))
        elif status.startswith("R"):
            old, new = next(it), next(it)
            result.append((new, old))
    return result


def find_modified_files(revspec: str, *, staged: bool = False) -> list[tuple[str, str]]:
    """Discover which files were modified or renamed in the given revspec.

    Returns (new_path, old_path) tuples.  For plain modifications both paths
    are identical; for renames they differ.
    """
    args = [
        "git",
        "diff",
        "--name-status",
        "-z",
        "--relative",
        "-M",
        "--diff-filter=MR",
    ]
    if staged:
        output = run(*base, "--cached")
    else:
        output = run(*base, f"{revspec}^", revspec)
    if not output:
        return []
    return _parse_name_status_z(output)


def parse_diff_line_ranges(
    new_path: str, old_path: str, revspec: str, *, staged: bool = False
) -> list[str]:
    """Parse `git diff` output to extract changed line ranges in the old file.

    Returns ranges like ["10,15", "20,20"] for use with `git blame -L`.
    """
    # Both paths must appear in the pathspec so -M can detect renames.
    if staged:
        diff_output = run(
            "git", "diff", "-U0", "-M", "--cached", "--", old_path, new_path
        )
    else:
        diff_output = run(
            "git", "diff", "-U0", "-M", f"{revspec}^", revspec, "--", old_path, new_path
        )
    ranges = []
    for line in diff_output.splitlines():
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+", line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        # BUG (carried over): When there are only adds (@@ -XX,0 +YY,x)
        # the first line will be XX. It should probably be YY + x.
        if count == 0:
            ranges.append(f"{start},{start}")
        else:
            ranges.append(f"{start},{start + count - 1}")
    return ranges


def blame_commits(file: str, ranges: list[str], blame_target: str) -> set[str]:
    """Run `git blame --incremental` with all ranges and collect unique commit SHAs."""
    cmd = ["git", "blame", "--incremental"]
    for r in ranges:
        cmd += ["-L", r]
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


def main(
    revspec: str, *, staged: bool = False, fixup: bool = False, null: bool = False
) -> None:
    blame_target = revspec if staged else f"{revspec}^"

    file_pairs = find_modified_files(revspec, staged=staged)
    if not file_pairs:
        if staged:
            print("No fixup targets found in staged changes.", file=sys.stderr)
        else:
            print(f"No file changes found in {revspec}.", file=sys.stderr)
        return

    if fixup:
        # Stash dance: isolate the index for committing
        working_tree_sha = run("git", "stash", "create")
        run("git", "stash", "--keep-index")

    try:
        for new_path, old_path in file_pairs:
            ranges = parse_diff_line_ranges(new_path, old_path, revspec, staged=staged)
            if not ranges:
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

            if fixup:
                run("git", "commit", "--fixup", target, "--", new_path)
            else:
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
    finally:
        if fixup and working_tree_sha:
            run("git", "stash", "apply", working_tree_sha, "--index", check=False)


if __name__ == "__main__":
    args = parse_args()
    main(args.revspec, staged=args.staged, fixup=args.fixup, null=args.null)
