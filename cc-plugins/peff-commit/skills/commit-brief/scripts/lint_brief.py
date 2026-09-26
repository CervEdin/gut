#!/usr/bin/env python3
"""Check a commit-brief file against the format in commit-brief/SKILL.md.

Usage: lint_brief.py [path]

With no path, lints $(git rev-parse --git-path commit-brief). Prints one
"line N: reason" per problem and exits 1 if there are any; otherwise prints
the entry count by tag and exits 0.
"""

import re
import subprocess
import sys
from collections import Counter

FIELDS = ("today", "incident", "change", "alternatives", "deferred", "uncertain")
TAGS = ("diff", "code", "blame", "session", "issue", "asked", "unsourced")
INCIDENT_TAGS = ("asked", "session", "issue", "unsourced")

ENTRY = re.compile(
    r"^(%s)-(\d+): \[(%s)\](.*)$" % ("|".join(FIELDS), "|".join(TAGS)), re.S
)


def split_citation(rest):
    """Return (citation, text) if rest opens with a (citation), else None.

    Parentheses nest, and anything inside double quotes is skipped, so a
    quoted "(" in a session citation does not end it early.
    """
    if not rest.startswith(" ("):
        return None
    depth, quoted = 0, False
    for i, ch in enumerate(rest[1:], start=1):
        if ch == '"':
            quoted = not quoted
        elif quoted:
            continue
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return rest[2:i], rest[i + 1 :]
    return rest[2:], ""


def check_entry(lineno, text, seen, counts):
    errors = []
    m = ENTRY.match(text)
    if not m:
        head = text.split(":", 1)[0]
        if head == "unsourced":
            return [
                "bare 'unsourced:' field; file the gap under the field it "
                "belongs to, as '<field>-N: [unsourced] text'"
            ]
        if head in FIELDS:
            return ["missing entry ID; write '%s-N:'" % head]
        if re.match(r"^\w+-\d+: ", text):
            field = head.rsplit("-", 1)[0]
            if field not in FIELDS:
                return ["unknown field '%s'" % field]
            return ["tag must be one of: %s" % ", ".join(TAGS)]
        return ["not an entry; expected '<field>-N: [tag] (citation) text'"]

    field, num, tag, rest = m.groups()
    entry_id = "%s-%s" % (field, num)
    if entry_id in seen:
        errors.append("duplicate ID %s (first on line %d)" % (entry_id, seen[entry_id]))
    else:
        seen[entry_id] = lineno
    counts[tag] += 1

    if field == "incident" and tag not in INCIDENT_TAGS:
        errors.append(
            "incident cannot be [%s]; use one of: %s"
            % (tag, ", ".join(INCIDENT_TAGS))
        )

    cited = split_citation(rest)
    if tag == "unsourced":
        if cited is not None:
            errors.append("[unsourced] takes no (citation)")
        body = rest
    else:
        if cited is None:
            errors.append("[%s] needs a (citation)" % tag)
            body = rest
        else:
            citation, body = cited
            if not citation.strip():
                errors.append("empty (citation)")
    if not body.strip():
        errors.append("entry has no text")
    return errors


def lint(lines):
    problems = []
    seen = {}
    counts = Counter()
    entry = None  # (lineno, joined text)

    def flush():
        if entry:
            for reason in check_entry(entry[0], entry[1], seen, counts):
                problems.append((entry[0], reason))

    for lineno, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if entry is None:
                problems.append((lineno, "continuation line with no entry above it"))
            else:
                entry = (entry[0], entry[1] + " " + line.strip())
            continue
        flush()
        entry = (lineno, line)
    flush()
    return problems, counts


def main(argv):
    if len(argv) > 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if len(argv) == 2:
        path = argv[1]
    else:
        path = subprocess.run(
            ["git", "rev-parse", "--git-path", "commit-brief"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError as e:
        print("%s: %s" % (path, e.strerror), file=sys.stderr)
        return 2

    problems, counts = lint(lines)
    for lineno, reason in sorted(problems):
        print("line %d: %s" % (lineno, reason))
    if problems:
        return 1
    total = sum(counts.values())
    if not total:
        print("line 1: no entries")
        return 1
    print(
        "%d entries: %s"
        % (total, ", ".join("%s %d" % (t, counts[t]) for t in TAGS if counts[t]))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
