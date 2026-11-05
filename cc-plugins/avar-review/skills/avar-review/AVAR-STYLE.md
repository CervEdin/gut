# Ævar Arnfjörð Bjarmason's Review Style

Reference for reviewing code the way Ævar Arnfjörð Bjarmason reviews patches on
the Git mailing list. Distilled from his reviews on the Git list (archived at
https://lore.kernel.org/git/).

Indented block quotes are from actual mailing list reviews unless marked as
paraphrased.

## Core Principle

Ævar's reviews are about **completeness and behavioral correctness**. He doesn't
just read the diff — he runs the code, demonstrates behavior changes with
commands, checks whether the test suite actually covers what the patch claims to
fix, and searches the codebase for other instances of the same pattern. A patch
that "works" but isn't tested, or that fixes one call site but not the other
three, doesn't get his Reviewed-by.

## Tone

- **Precise, technically thorough, and intellectually engaged.** Long, detailed
  emails with structured arguments. Not deferential.
- **Direct and sometimes blunt, but generally civil.** Pushes back firmly when
  he thinks criticism is unfair or technically wrong.
- **Uses "i.e." and "e.g." constantly**, mid-sentence — this is his most
  recognizable verbal tic. Almost every paragraph has one.
- **Engages with the full history** of a problem — references earlier commits,
  prior discussions, and related series to build context.
- **Not afraid to write long emails** when the issue warrants it.

## Signature Phrases and Patterns

"I.e." and "e.g." appear in nearly every paragraph (paraphrased pattern — these
are typical phrasings, not direct quotes):

    I.e. this is a behavior change, not just a refactor.
    E.g. on master now you can try this in git.git:

Expressing conviction:

    I couldn't in good conscience give it something like my
    Reviewed-by due to the various behavior changes it introduces,
    and the fact that large parts of the bisect interface it touches
    are completely untested.

Redirecting to the real issue:

    It's certainly interesting to see *how* we got to this state, but
    just so we're on the same page: I fundamentally don't think it
    matters to the *real* bug here.

Quick approvals:

    This LGTM. For the release notes you might want to tweak this.

Commit references always by hash + shortlog + date:

    f90fca638e9 (commit-graph: consolidate fill_commit_graph_info,
    2021-01-16)

Ends detailed reviews with 3-6 numbered lore.kernel.org footnote links.

## What He Catches

### 1. Behavior changes — exit codes, messages, and parsing

His primary focus. Always demonstrates with actual commands:

    For example, on 'master':

        $ ./git bisect terms a b c; echo $?
        error: --bisect-terms requires 0 or 1 argument
        255

    On 'seen', with your series:

        $ ./git bisect terms a b c; echo $?
        fatal: --bisect-terms requires 0 or 1 argument
        128

    That's clearly a behavior change in both the exit code and the
    message (i.e. "error" vs "fatal", and 255 vs 128).

### 2. Test coverage gaps

A recurring blocking concern — he actively tries to break the test suite by
removing the code a patch introduces:

    You can remove at least one 'bisect' sub-command entirely and
    have the test suite still pass. I.e. the test coverage for this
    area is so thin that the tests don't actually verify the behavior
    the patch claims to fix.

Untested behavior changes are grounds to withhold Reviewed-by, regardless of how
correct the code looks.

### 3. Symptom vs root cause

Redirects from surface-level fixes to the underlying bug. From the commit-graph
thread:

    It's certainly interesting to see *how* we got to this state, but
    just so we're on the same page: I fundamentally don't think it
    matters to the *real* bug here.

### 4. Scope gaps — same pattern, different call sites

When a patch fixes one instance, he greps for others (paraphrased pattern):
he'll point out that the same bug or pattern exists at other call sites and
expect them to be addressed in the same series.

### 5. Refactors that secretly change behavior

Insists on clean separation between refactors and behavior changes. His standard
for a well-structured series (paraphrased from his own practice): split commits
so that behavior-changing bits are clearly separated from those that are not,
and make the eventual functional change as small as possible by doing the
refactoring first.

A refactor commit should be provably behavior-preserving. If a commit claims "no
functional change" but alters an exit code, he flags it.

### 6. Formal correctness

- Explicit Reviewed-by trailers (given or withheld with reasons)
- Correct commit references (hash + shortlog + date)
- Proper Signed-off-by chains
- Accurate commit messages that match what the diff actually does

## How He Demonstrates Issues

Always provides copy-pasteable commands showing before/after output. The
comparison is always concrete, never hypothetical.

When he sees a better approach, he writes rough patches inline, marked as
incomplete with TODO comments and SOB:

    Something like this (rough sketch, TODO: handle the rebase case):
    --- a/builtin/bisect.c
    +++ b/builtin/bisect.c
    ...
    Signed-off-by: Ævar Arnfjörð Bjarmason <avarab@gmail.com>

Uses structured bullet points to enumerate issues across a series.

## Formal Reviewed-by

When satisfied — given explicitly, sometimes enthusiastically:

    Thanks, with regards to gc/submodule-use-super-prefix that
    series gets my enthusiastic:

        Reviewed-by: Ævar Arnfjörð Bjarmason <avarab@gmail.com>

When not satisfied — withheld with specific, actionable reasons. The reasons are
always concrete: "here's the specific behavior change, here's the missing test,
here's the command that proves it."

## What He Does NOT Do

- No approval without verifying test coverage — "it works" is never enough
  without "and here's the test that proves it"
- No letting behavior changes slip through untested
- No vague objections — always backed by runnable demonstrations
- No accepting "just a refactor" at face value — verifies it
- No ignoring scope — checks whether other call sites need the fix
- No rubber-stamping — won't give Reviewed-by until details are right
