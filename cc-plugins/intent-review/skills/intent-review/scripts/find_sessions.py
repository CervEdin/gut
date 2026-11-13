#!/usr/bin/env python3
"""List the Claude Code sessions that worked on a change in this repository.

Usage: find_sessions.py RANGE
       find_sessions.py --staged

RANGE is anything `git log` takes, such as origin/HEAD..topic. Run it from
the repository.

Every transcript under ~/.claude/projects is read, whatever directory its
session ran in: a session often works on a worktree, or on a checkout that
has since been removed, from somewhere else. A session matches when:

  edited    it edited or wrote a file whose path ends in a path the change
            touches, unless the directory the path sits in still exists and
            belongs to another repository
  subject   a line of it holds the subject of a commit in RANGE; this finds
            sessions that changed files through the shell, and sessions
            where the user reviewed the change

Both can bring in a session about something else: a common name such as
README.md, or a session that only printed the log. Each match gives the
transcript lines it was found on, so that the turns around them can be read.

A matched session's plan hand-offs and summaries name the transcript they
came from; those are followed until no new session turns up.

Prints one line per match, oldest first: the transcript path, the evidence
with its line numbers, its first and last event time, and its number of
user turns. Exits 1 when nothing matches.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

LINK = re.compile(r"read the full transcript at: (/\S+?\.jsonl)")
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
FIXUP = ("fixup! ", "amend! ", "squash! ")


def git(*args, cwd=None):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True, cwd=cwd).stdout


def common_dir(path):
    """Return the git common dir of the repository at path, or None."""
    try:
        out = git("rev-parse", "--path-format=absolute", "--git-common-dir",
                  cwd=path)
    except subprocess.CalledProcessError:
        return None
    return os.path.realpath(out.strip())


def touched(args):
    """Return the repo-relative paths the change touches."""
    if args.staged:
        out = git("diff", "--cached", "--name-only", "-z")
    else:
        out = git("log", "--name-only", "--format=", "-z", args.range)
    return {p.strip("\n") for p in out.split("\0") if p.strip("\n")}


def subjects(args):
    """Return the subjects of the range's commits, without fixup prefixes."""
    if args.staged:
        return set()
    out = set()
    for subject in git("log", "--format=%s", args.range).splitlines():
        while subject.startswith(FIXUP):
            subject = subject.split(" ", 1)[1]
        out.add(subject)
    return out


def lines(numbers):
    """Format line numbers for the evidence column, the first few only."""
    shown = ",".join(f"L{n}" for n in numbers[:5])
    return shown + (",..." if len(numbers) > 5 else "")


class Repo:
    """Decide whether a directory belongs to this repository."""

    def __init__(self):
        self.ours = common_dir(".")
        self.seen = {}

    def other(self, folder):
        """True when folder exists and belongs to another repository."""
        if folder not in self.seen:
            self.seen[folder] = os.path.isdir(folder) \
                and common_dir(folder) != self.ours
        return self.seen[folder]


def edited(target, rels, repo):
    """Return the touched path target ends in, unless it is another repo's."""
    for rel in rels:
        if target.endswith("/" + rel):
            if not repo.other(target[:-len(rel) - 1]):
                return rel
    return None


def scan(path, want, repo, force=False):
    """Return a summary of one transcript; skip one that names no touched path
    and no subject unless force is set."""
    rels, subjects = want["rels"], want["subjects"]
    with open(path, "rb") as f:
        data = f.read()
    ev = {"path": path, "why": [], "edited": set(), "edit_lines": [],
          "subject_lines": [], "times": [], "user_turns": 0, "links": []}
    if not force and not any(k in data for k in want["keys"]):
        return ev
    for n, raw in enumerate(data.splitlines(), 1):
        if any(k in raw for k in want["subject_keys"]):
            ev["subject_lines"].append(n)
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ts = event.get("timestamp", "")[:19]
        if ts:
            ev["times"].append(ts)
        content = (event.get("message") or {}).get("content")
        if event.get("type") == "user" and isinstance(content, str):
            ev["links"] += LINK.findall(content)
            if not event.get("isMeta"):
                ev["user_turns"] += 1
        if event.get("type") != "assistant" or not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") != "tool_use" \
                    or block.get("name") not in EDIT_TOOLS:
                continue
            inp = block.get("input") or {}
            target = inp.get("file_path") or inp.get("notebook_path")
            rel = edited(target, rels, repo) if target else None
            if rel:
                ev["edited"].add(rel)
                ev["edit_lines"].append(n)
    if ev["edited"]:
        ev["why"].append(f'edited {len(ev["edited"])} of {len(rels)} files'
                         f' at {lines(ev["edit_lines"])}')
    if ev["subject_lines"]:
        ev["why"].append(f'subject at {lines(ev["subject_lines"])}')
    return ev


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("range", nargs="?")
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()
    if bool(args.range) == args.staged:
        ap.error("give either RANGE or --staged")

    rels = touched(args)
    if not rels:
        ap.error("the change touches no files")
    subs = subjects(args)
    subject_keys = [json.dumps(t)[1:-1].encode() for t in subs]
    want = {"rels": rels, "subjects": subs, "subject_keys": subject_keys,
            "keys": [r.encode() for r in rels] + subject_keys}
    repo = Repo()

    projects = os.path.expanduser("~/.claude/projects")
    found = {}
    for path in glob.glob(os.path.join(projects, "*", "*.jsonl")):
        s = scan(path, want, repo)
        if s["why"]:
            found[path] = s

    queue = list(found.values())
    while queue:
        s = queue.pop()
        for link in s["links"]:
            if link in found or not os.path.isfile(link):
                continue
            linked = scan(link, want, repo, force=True)
            linked["why"].append("linked from "
                               + os.path.basename(s["path"])[:8])
            found[link] = linked
            queue.append(linked)

    for s in sorted(found.values(), key=lambda s: min(s["times"] or [""])):
        first, last = min(s["times"] or [""]), max(s["times"] or [""])
        print(f'{s["path"]}  {"; ".join(s["why"])}'
              f'  {first[:16]}..{last[:16]}  user turns: {s["user_turns"]}')
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
