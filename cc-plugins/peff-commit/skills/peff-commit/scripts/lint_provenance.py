#!/usr/bin/env python3
"""Check a provenance file against §3 of peff-commit/COMPOSE.md.

Usage: lint_provenance.py <path>

Checks that the coverage:, budget:, paragraphs: and style: sections are
there, and that style: has a line for every rule in the "Sentences" list
of PEFF-STYLE.md, which is read each run. Prints one "line N: reason" per
problem and exits 1 if there are any; otherwise prints the style count
and exits 0.
"""

import os
import re
import sys

SECTIONS = ("coverage", "budget", "paragraphs", "style")
STYLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PEFF-STYLE.md")
RULE = re.compile(r"^- \*\*(.+?)\.\*\*")


def sentence_rules(path):
    """Return the bold names of the rules under "### Sentences"."""
    rules = []
    inside = False
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                inside = line.strip() == "### Sentences"
                continue
            m = RULE.match(line) if inside else None
            if m:
                rules.append(m.group(1))
    return rules


def parse(lines):
    """Split the file into its top-level lines, each with its indented lines.

    Returns a list of (head, lineno, text, body), where head is the text
    before the first colon and body is a list of (lineno, stripped line).
    """
    sections = []
    for lineno, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith(" "):
            if sections:
                sections[-1][3].append((lineno, line.strip()))
            continue
        sections.append((line.split(":", 1)[0], lineno, line, []))
    return sections


def lint_style(body, rules):
    """Check the lines of a style: section; return (problems, rule -> value)."""
    problems = []
    style = {}
    first = {}
    for lineno, line in body:
        name, sep, value = line.partition(":")
        if not sep or not value.strip():
            problems.append((lineno, "expected '<rule>: ok' or '<rule>: <the fix>'"))
        elif name not in rules:
            problems.append((lineno, "'%s' is not a rule under Sentences in PEFF-STYLE.md" % name))
        elif name in style:
            problems.append((lineno, "'%s' listed twice (first on line %d)" % (name, first[name])))
        else:
            style[name] = value.strip()
            first[name] = lineno
    return problems, style


def lint(lines, rules):
    problems = []
    found = {}  # section -> line number
    style = {}  # rule name -> its value

    for head, lineno, text, body in parse(lines):
        if head not in SECTIONS or ":" not in text:
            continue
        if head in found:
            problems.append((lineno, "second %s: section (first on line %d)" % (head, found[head])))
            continue
        found[head] = lineno
        if head != "style":
            continue
        if text.strip() != "style:":
            problems.append((lineno, "style: takes one indented '<rule>: ...' line per rule, not text"))
        style_problems, style = lint_style(body, rules)
        problems += style_problems

    for section in SECTIONS:
        if section not in found:
            problems.append((1, "no %s: section" % section))
    if "style" in found:
        for rule in rules:
            if rule not in style:
                problems.append((found["style"], "style: does not name '%s'" % rule))
    return problems, style


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = argv[1]
    try:
        rules = sentence_rules(STYLE_FILE)
        with open(path) as f:
            lines = f.readlines()
    except OSError as e:
        print("%s: %s" % (e.filename, e.strerror), file=sys.stderr)
        return 2
    if not rules:
        print("%s: no rules found under '### Sentences'" % STYLE_FILE, file=sys.stderr)
        return 2

    problems, style = lint(lines, rules)
    for lineno, reason in sorted(problems):
        print("line %d: %s" % (lineno, reason))
    if problems:
        return 1
    fixed = sum(1 for value in style.values() if value != "ok")
    print("style: %d rules, %d fixed" % (len(style), fixed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
