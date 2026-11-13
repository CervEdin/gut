#!/usr/bin/env python3
"""Print what the user said in Claude Code session transcripts.

Usage: user_turns.py TRANSCRIPT.jsonl [...]

For each transcript, prints in order, one entry per line group:

  L<n> user:       a message the user typed (system reminders removed)
  L<n> ran:        a shell command the user ran with `!`
  L<n> command:    a slash command the user typed, with its arguments
  L<n> pasted:     a message that is only pasted text
  L<n> answered:   an AskUserQuestion answer, as "question" = "answer"
  L<n> rejected plan: the user turned down the plan put up just before,
                   with what they said
  L<n> approved plan: the user approved the plan put up just before
  L<n> interrupt:  the user stopped the turn
  L<n> model-written (<kind>): text that arrives as a user turn but was
                   written by a model: a plan hand-off, a compaction
                   summary, a skill body, a plan put up for approval

L<n> is the line in the .jsonl file, so a finding can cite it. Tool output,
task notifications and meta events are left out.
"""

import json
import re
import sys

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
TAG = re.compile(r"<(\w[\w-]*)>(.*?)</\1>", re.S)

MODEL_WRITTEN = (
    ("Implement the following plan:", "plan hand-off, approved"),
    ("This session is being continued from a previous conversation", "summary"),
    ("Base directory for this skill:", "skill body"),
)

SKIP_TAGS = ("task-notification", "local-command-stdout", "bash-stdout",
             "bash-stderr", "local-command-caveat")


def indent(text):
    return "\n".join("    " + line for line in text.strip().splitlines())


def string_turn(text):
    """Classify a user turn given as a string; return (label, text) or None."""
    text = REMINDER.sub("", text).strip()
    if not text:
        return None
    for prefix, kind in MODEL_WRITTEN:
        if text.startswith(prefix):
            return f"model-written ({kind})", text
    if text.startswith("<bash-input>"):
        tags = dict(TAG.findall(text))
        return "ran", "!" + tags.get("bash-input", "").strip()
    if text.startswith(("<command-name>", "<command-message>")):
        tags = dict(TAG.findall(text))
        name = tags.get("command-name", "").strip()
        args = tags.get("command-args", "").strip()
        return "command", (name + " " + args).strip()
    if any(text.startswith(f"<{t}>") for t in SKIP_TAGS):
        return None
    if text.startswith("[Request interrupted"):
        return "interrupt", text.splitlines()[0]
    stripped = re.sub(r"<pasted_content[^>]*>.*?</pasted_content>", "", text,
                      flags=re.S).strip()
    if not stripped:
        return "pasted", text
    return "user", text


def tool_result_turns(event, block, name):
    """Yield (label, text) for a tool result that carries a user decision."""
    result = event.get("toolUseResult")
    if isinstance(result, dict) and isinstance(result.get("answers"), dict):
        notes = result.get("annotations") or {}
        for question, answer in result["answers"].items():
            line = f'"{question}" = "{answer}"'
            note = (notes.get(question) or {}).get("notes")
            if note:
                line += f"\n(note: {note})"
            yield "answered", line
        return
    content = block.get("content")
    if isinstance(content, list):
        content = " ".join(b.get("text", "") for b in content
                           if isinstance(b, dict))
    if not isinstance(content, str):
        return
    if name == "ExitPlanMode" and not block.get("is_error") \
            and content.startswith("User has approved your plan"):
        yield "approved plan", content.splitlines()[0]
        return
    if not block.get("is_error"):
        return
    if content.startswith("The user doesn't want to proceed"):
        if name != "ExitPlanMode":
            return
        said = content.split("the user said:\n", 1)
        if len(said) == 2:
            yield "rejected plan", \
                said[1].split("\n\nNote: The user's next", 1)[0]
        else:
            yield "rejected plan", "(no reason given)"
    elif content.startswith("[Request interrupted"):
        yield "interrupt", content.splitlines()[0]


def turns(path):
    tool_names = {}
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("isMeta"):
                continue
            content = (event.get("message") or {}).get("content")
            if event.get("type") == "assistant" and isinstance(content, list):
                for block in content:
                    if block.get("type") != "tool_use":
                        continue
                    tool_names[block.get("id")] = block.get("name")
                    if block.get("name") == "ExitPlanMode":
                        plan = (block.get("input") or {}).get("plan", "")
                        yield n, "model-written (plan for approval)", plan
                continue
            if event.get("type") != "user":
                continue
            if isinstance(content, str):
                turn = string_turn(content)
                if turn:
                    yield (n, *turn)
                continue
            for block in content or []:
                if block.get("type") == "text":
                    turn = string_turn(block.get("text", ""))
                    if turn:
                        yield (n, *turn)
                elif block.get("type") == "tool_result":
                    name = tool_names.get(block.get("tool_use_id"), "?")
                    for label, text in tool_result_turns(event, block, name):
                        yield n, label, text


def main(paths):
    if not paths:
        print((__doc__ or "").strip(), file=sys.stderr)
        return 2
    for path in paths:
        print(f"== {path}")
        for n, label, text in turns(path):
            print(f"L{n} {label}:")
            print(indent(text))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
