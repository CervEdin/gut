import json
import os
import re
import statistics
import subprocess
import sys

try:
    import textstat
except ImportError:
    # Reported in main() as one line. A traceback out of a skill step
    # reads like the script is broken rather than absent.
    textstat = None

REPO = "."

FUNCTION_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "at", "for", "with", "by",
    "from", "as", "that", "this", "these", "those",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could",
    "and", "or", "but", "if", "because", "while",
    "although", "so", "than", "then", "not", "no", "it", "its", "their",
    "they", "he", "she", "we", "you", "i",
    "which", "who", "whom", "whose", "what", "when", "where", "why",
    "how", "all", "each", "every", "some",
    "any", "both", "few", "more", "most", "other", "such", "only", "own",
    "same", "too", "very", "just", "also",
    "into", "onto", "upon", "about", "above", "below", "under", "over",
    "through", "during", "before",
    "after", "between", "among", "within", "without", "against", "toward",
    "towards", "per", "via",
}

NOMINAL_SUFFIXES = ("tion", "sion", "ment", "ance", "ence", "ity")

STOCK_PHRASES = [
    # Full hedge/transition clauses distinctive of LLM commit-message
    # voice. Dropped the bare single-word forms of these ("note that",
    # "in order to", "ensures that") after they false-positived on real
    # commits that use them as ordinary formal English.
    r"it'?s worth noting", r"worth noting that", r"it is important to note",
    r"please note that",
    r"the following changes", r"makes the following changes",
    r"backwards? compatible and does not break",
    # Vocabulary that's rare in genuine engineering prose but common in
    # LLM/marketing register. Dropped words that collide with normal
    # technical usage: "robust", "comprehensive", "underlying", "harness"
    # (test harness), "streamlined", "leverage" all showed up as false
    # positives on real commits.
    r"seamless(?:ly)?", r"facilitates?", r"facilitating",
    r"aforementioned", r"paradigm", r"utiliz\w*",
    r"cutting-edge", r"state-of-the-art", r"holistic",
    r"synerg\w*", r"delv\w*", r"showcas\w*",
    r"elevat\w*", r"empower\w*", r"unlock\w*",
    r"meticulous(?:ly)?", r"multifaceted", r"nuanced",
    r"testament to", r"tapestry",
]
STOCK_PHRASE_PATTERN = re.compile(
    r"\b(?:" + "|".join(STOCK_PHRASES) + r")", re.IGNORECASE
)

# Clause-chaining punctuation is rewritten to a sentence break before
# scoring: textstat splits sentences only on .!?, so a paragraph chained
# with dashes, colons or semicolons would otherwise count as one giant
# sentence and swamp the readability metrics with punctuation style.
CLAUSE_PUNCT = re.compile(r"\s*(?:[;:—]|--)\s+")

BACKTICK_SPAN = re.compile(r"`[^`]*`")
CAMEL_OR_PASCAL = re.compile(r"\b[A-Za-z]*[a-z][A-Z][A-Za-z0-9]*\b")
SNAKE_CASE = re.compile(r"\b[a-zA-Z]+_[a-zA-Z_]+\b")
KEBAB_CASE = re.compile(r"\b[a-zA-Z]+(?:-[a-zA-Z]+)+\b")


def strip_code_tokens(text):
    """Drop code identifiers before scoring prose."""
    text = BACKTICK_SPAN.sub(" ", text)
    text = CAMEL_OR_PASCAL.sub(" ", text)
    text = SNAKE_CASE.sub(" ", text)
    text = KEBAB_CASE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(text):
    return re.findall(r"[a-zA-Z']+", text.lower())


def sentences(text):
    # crude but fine for commit-message prose: split on .!? and blank lines
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n", text.strip())
    return [s for s in parts if words(s)]


def nominalization_ratio(ws):
    if not ws:
        return 0.0
    n = sum(1 for w in ws if w.endswith(NOMINAL_SUFFIXES) and len(w) > 6)
    return n / len(ws)


def function_word_ratio(ws):
    if not ws:
        return 0.0
    return sum(1 for w in ws if w in FUNCTION_WORDS) / len(ws)


def phrase_rate(raw_text, word_count):
    """Stock LLM discourse markers per 100 words.

    Matched against raw_text, not the code-stripped text: several phrases
    (cutting-edge, state-of-the-art) are themselves kebab-case and would
    otherwise be stripped before they could match.
    """
    if word_count == 0:
        return 0.0
    hits = len(STOCK_PHRASE_PATTERN.findall(raw_text))
    return hits / word_count * 100


def sentence_uniformity(text):
    """Low value = bursty/human, high value = suspiciously uniform."""
    lens = [len(words(s)) for s in sentences(text)]
    if len(lens) < 2:
        return 0.0
    mean = statistics.mean(lens)
    if mean == 0:
        return 0.0
    cv = statistics.pstdev(lens) / mean  # coefficient of variation
    return cv


def metrics(raw_text):
    text = CLAUSE_PUNCT.sub(". ", strip_code_tokens(raw_text))
    ws = words(text)
    return {
        "words": len(ws),
        "fre": textstat.flesch_reading_ease(text),
        "fkg": textstat.flesch_kincaid_grade(text),
        "fog": textstat.gunning_fog(text),
        "nominal": nominalization_ratio(ws),
        "funcword": function_word_ratio(ws),
        "cv": sentence_uniformity(text),
        "phrase": phrase_rate(raw_text, len(ws)),
    }


MAX_Z = 8.0  # clip: a zero-variance baseline (e.g. phrase rate) would
             # otherwise divide by an epsilon and blow any nonzero hit up
             # to a meaningless billions-sized z-score

FIELDS_HIGH_IS_SLOP = ["fkg", "fog", "nominal", "funcword", "phrase"]
FIELDS_LOW_IS_SLOP = ["cv"]  # sentence-length uniformity: flipped, since
                              # a *low* CV (suspiciously uniform lengths)
                              # is the slop-like direction
FIELDS_FLIPPED = ["fre"]  # flesch reading ease: lower score = harder


def fit_baseline(rows):
    """Median/stdev per metric from a corpus of real commit messages."""
    stats = {}
    for f in FIELDS_HIGH_IS_SLOP + FIELDS_LOW_IS_SLOP + FIELDS_FLIPPED:
        vals = [r[f] for r in rows]
        stats[f] = (statistics.median(vals), statistics.pstdev(vals) or 1e-9)
    return stats


def score_against(row, stats):
    """Signed so that positive always means 'more slop-like'."""
    def clip(z):
        return max(-MAX_Z, min(MAX_Z, z))

    z = {}
    for f in FIELDS_HIGH_IS_SLOP:
        med, sd = stats[f]
        z[f] = clip((row[f] - med) / sd)
    for f in FIELDS_LOW_IS_SLOP + FIELDS_FLIPPED:
        med, sd = stats[f]
        z[f] = clip((med - row[f]) / sd)
    return z, sum(z.values())


def save_baseline(stats, path):
    with open(path, "w") as f:
        json.dump(stats, f, indent=2)


def load_baseline(path):
    with open(path) as f:
        return {k: tuple(v) for k, v in json.load(f).items()}


def load_commits(repo, hashes):
    rows = []
    for h in hashes:
        msg = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%B", h],
            cwd=repo, capture_output=True, text=True,
        ).stdout.strip()
        subject = msg.splitlines()[0] if msg else ""
        m = metrics(msg)
        rows.append({**m, "hash": h[:7], "subject": subject})
    return rows


def recent_hashes(repo, n, author=None):
    cmd = ["git", "log", "--no-merges", f"-n{n}", "--pretty=format:%H"]
    if author:
        cmd.insert(2, f"--author={author}")
    return subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True
    ).stdout.split()


SLOP_VARIANTS = {
    "[slop: nominalization-heavy]": """api: leverage a robust guest language mechanism

This commit ensures that the guest language functionality is implemented
in a manner that facilitates a more comprehensive and streamlined
mechanism for accommodating the aforementioned language preferences,
thereby enhancing the overall user experience and ensuring seamless
integration with the underlying data architecture paradigm.""",

    "[slop: hedge-and-transition]": """Add guest language support to the API

It's worth noting that this change adds support for guest languages.
Additionally, we've made sure to update the relevant endpoints so that
they can properly handle the new field. Furthermore, this should help
ensure a more complete and robust experience for users going forward.
In order to fully support this feature, further changes may be needed
in the future, but this represents a solid first step in that direction.""",

    "[slop: bullet-restates-diff]": """feat: guest languages

This commit makes the following changes:
- Adds a languages field to the guest struct
- Updates the API handler to accept the new field
- Modifies the store layer to persist the change
- Ensures the frontend displays the updated data correctly

Note: this change is backwards compatible and does not break any
existing functionality. This is because the new field is optional
and defaults to an empty list when not provided.""",
}


# Under this many words of prose (code identifiers stripped) the
# readability metrics are summarising three or four sentences, and the
# score reports sampling noise rather than anything about the writing.
MIN_PROSE_WORDS = 40

# The baseline ships next to this script so scoring works from any cwd.
DEFAULT_BASELINE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "slop_baseline.json"
)


def cmd_score(args):
    raw_text = open(args.file).read() if args.file else sys.stdin.read()
    try:
        stats = load_baseline(args.baseline)
    except FileNotFoundError:
        raise SystemExit(
            f"no baseline at {args.baseline!r} — run `slop_score.py fit` first"
        )

    row = metrics(raw_text)
    z, combined = score_against(row, stats)
    hits = STOCK_PHRASE_PATTERN.findall(raw_text)

    fields = FIELDS_HIGH_IS_SLOP + FIELDS_LOW_IS_SLOP + FIELDS_FLIPPED
    prose_fields = [f for f in fields if f != "phrase"]
    worst = max(prose_fields, key=lambda f: z[f])

    # The two axes are reported apart because they call for different
    # repairs: a phrase hit saturates at MAX_Z whatever the rest of the
    # prose does, so summing it into one number hides both the cause and
    # the fix. Naming the worst prose metric does the same job for the
    # other direction, where a metric sitting low masks another's spike.
    print(f"combined z-score: {combined:.1f}")
    if hits:
        print(f"  stock-phrase penalty {z['phrase']:+.1f} of that; "
              f"the prose alone scores {combined - z['phrase']:+.1f}")
    print(f"  strongest prose signal: {worst} {z[worst]:+.1f}")
    print()

    print(f"{'metric':10}{'value':>10}{'z':>7}")
    for f in fields:
        print(f"{f:10}{row[f]:>10.3f}{z[f]:>7.1f}")
    if hits:
        print(f"\nstock-phrase hits: {', '.join(hits)}")
    if row["words"] < MIN_PROSE_WORDS:
        print(f"\nonly {row['words']} words of prose after stripping code."
              f" Under {MIN_PROSE_WORDS} the metrics are summarising too few"
              f"\nsentences to mean much; judge a message this short by eye.")


def cmd_fit(args):
    hashes = recent_hashes(args.repo, args.n, args.author)
    rows = load_commits(args.repo, hashes)
    stats = fit_baseline(rows)
    save_baseline(stats, args.baseline)
    print(f"fit baseline from {len(rows)} commits -> {args.baseline}")

    print(f"\n{'label':32}{'z':>6}")
    for label, text in SLOP_VARIANTS.items():
        row = metrics(text)
        _, combined = score_against(row, stats)
        print(f"{label:32}{combined:>6.1f}")


def main():
    import argparse

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    score_p = sub.add_parser(
        "score", help="score a commit message from a file or stdin (default)"
    )
    score_p.add_argument("file", nargs="?", help="omit to read stdin")
    score_p.add_argument("--baseline", default=DEFAULT_BASELINE_PATH)
    score_p.set_defaults(func=cmd_score)

    fit_p = sub.add_parser("fit", help="fit a baseline from a git corpus")
    fit_p.add_argument("-n", type=int, default=300, help="commits to sample")
    fit_p.add_argument("--repo", default=REPO)
    fit_p.add_argument("--author", default=None)
    fit_p.add_argument("--baseline", default=DEFAULT_BASELINE_PATH)
    fit_p.set_defaults(func=cmd_fit)

    # Default to `score` when no subcommand is given, so `slop_score.py`
    # and `slop_score.py msg.txt` both work without saying `score` first.
    argv = sys.argv[1:]
    if not argv or argv[0] not in ("score", "fit", "-h", "--help"):
        argv = ["score"] + argv

    args = ap.parse_args(argv)
    if textstat is None:
        raise SystemExit(
            "slop_score.py needs the textstat package: "
            "pip install textstat"
        )
    args.func(args)


if __name__ == "__main__":
    main()
