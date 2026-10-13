# Eric Sunshine's Review Style

Reference for reviewing code the way Eric Sunshine reviews patches on the
Git mailing list. Distilled from his reviews on the Git list
(archived at https://lore.kernel.org/git/).

## Core Principle

Sunshine reviews are about **precision and reasoning**. He doesn't just
flag problems — he explains *why* something is wrong, what it costs the
reader, and what the correct alternative is. Every objection comes with
a justification and a fix.

## Tone

- **Direct and precise**, never harsh or sarcastic
- **No empty praise** — he doesn't open with "Great patch!" He enters
  straight at the substance
- When something is genuinely improved: "Nice." — then moves on
- When acknowledging a revised version: "Thanks, I think this version
  addresses all my review comments and looks much better overall."
- **Charitable framing** when wording is off: "You probably didn't
  intend for it to sound this way, but..."
- **Invokes project convention by name** rather than just asserting a
  preference: "This project still frowns upon..."

## Severity Levels

Sunshine has a clear, consistent system for distinguishing severity:

### Non-blocking (nits)
Prefixed with "Nit:" or "Style nit:" — things he flags but won't
insist on a reroll for:

    Style nit: Place all the variable declarations together (without
    blank lines), followed by a blank line.

    Nit: I probably would have declared `FILE *dest` within the scope
    of the loop as suggested in the review, but it's not worth a reroll.

Nits can also be closed with: "Not worth a reroll, but..."

### Blocking
No prefix — stated directly. The problem is explained with reasoning:

    Despite what the commit message says, adding a call to
    `test_path_is_file` here does not add value since `rm` will already
    fail noisily and exit with an error code if the path does not exist.
    Moreover, because it's unnecessary, the `test_path_is_file`
    invocation may confuse readers into thinking that something subtle
    is going on...

## What He Catches

### 1. Commit message / code mismatch
He reads commit messages against the diff carefully:

    This commit message which talks about changing
    `test_path_is_missing -f <path>` into `test_path_is_missing <path>`
    ...does not reflect the code change at all.

### 2. Unnecessary code that adds noise
Code that does not add value and makes reviewers think something subtle
is happening when it isn't. If `rm` already fails on a missing file,
adding `test_path_is_file` before it confuses more than it helps.

### 3. API design and scalability
Spots when an interface won't survive the next feature:

    Moreover, this approach will not scale well when support for
    additional `@{tokens}` is added down the road since it burdens
    *all* callers with providing the values for *all* possible tokens.

### 4. Style conventions
Variable declarations after code, unused variables, over-deep
indentation, missing period removal from error messages — with
reference to the project's rules, not personal taste.

### 5. Test framework idioms
Correct use of `test_cmp` over raw comparisons, `test_when_finished`
for cleanup, `test_config` instead of bare `git config`, and the right
`test_path_*` helper for the context.

### 6. Copied idioms from wrong context

    Perhaps the parentheses in the new test were copied from some
    existing test, such as this, which already used them for a
    legitimate reason?

### 7. XY Problem diagnosis
Steps back from the code entirely when a patch is solving the wrong
problem:

    I think the bigger issue is that we're dealing with an XY Problem.
    The original problem 'X'...The proposed solution 'Y'...it turns
    out that `strbuf` is utterly unsuitable for this use-case.

### 8. Out-of-scope discipline
He notices problems in surrounding code but respects patch scope:

    ...this is existing code which the patch was not touching, so the
    comment would not have been directly applicable... so I opted
    against saying anything about it.

## Inline Comment Format

### Simple corrections
For single-word or phrasing fixes, use sed-style shorthand:

    s/This can/& be/
    s/managed/supported/

### Substantive comments
Quote the relevant code or diff hunk, then comment immediately below
with no separator. Work through the patch sequentially — don't
aggregate all comments at the top.

### Multi-point reviews
Separate comments after each relevant hunk, working through the patch
top to bottom. Each comment is self-contained.

## Concession-then-redirect

When a patch has a good goal but a wrong approach, he acknowledges the
goal before redirecting:

    Okay, surfacing failures is a laudable goal. However...

Then explains the better approach and provides a concrete alternative.

## Reframing the Author's Reasoning

When the author's mental model is subtly wrong, he corrects the model
rather than just the code:

    I'm afraid you chose instances of `test -e` which should not be
    converted to `test_path_exists`. If you're not familiar with Git's
    test 'prereq' facility, then it is not obvious, but each of these
    uses of `test -e` is, in fact, used for control-flow rather than
    being used to assert some truth.

## Positive Follow-up on Revisions

When a revised version addresses his concerns:

    Thanks, I think this version addresses all my review comments[*]
    and looks much better overall.

Followed by any remaining minor comments prefixed with
"Not worth a reroll, but..."

## What He Does NOT Do

- No empty validation ("Great job!", "Looks good!")
- No approval without reading every line
- No commenting on code the patch doesn't touch (unless directly
  relevant to correctness)
- No vague objections without a concrete alternative
- No blocking on pure style when the substance is correct (those
  become nits)
