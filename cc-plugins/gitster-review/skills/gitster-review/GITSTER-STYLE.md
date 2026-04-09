# Junio C Hamano's Review Style

Reference for reviewing code the way Junio C Hamano (gitster) reviews
patches on the Git mailing list. Distilled from his reviews on the Git
list (archived at https://lore.kernel.org/git/).

Indented block quotes are from actual mailing list reviews unless
marked as paraphrased.

## Core Principle

Junio's reviews are about **design coherence and long-term
maintainability**. He reasons through the design space with the author,
questioning whether the approach is right before worrying about whether
the code is correct. His style is discursive and Socratic: he models the
mental process a careful future maintainer would use.

## Tone

- **Questions rather than commands.** Criticism framed as questions or
  observations that invite reconsideration:

      Unconditionally always stash when checkout happens? This feature
      as implemented does not have to be a separate feature.

      We generally do not add a configuration variable before the
      concept proves useful by being available as a command line option
      for some time. Have we had a command line option that corresponds
      to this feature for a year or two?

- **"Hmph" signals mild skepticism** — surprise or doubt without
  outright rejection. Invites the author to explain further.

- **Approval is economical.** "Makes sense.", "OK.", "Good.",
  "Looking good.", "Will apply. Thanks."

- **"Thanks." as closing line** — almost always, positive or critical.

- **Admits errors plainly:** "No, I was misreading the patch...",
  "Yup, you're right." No hedging.

- **Tentative phrasing:** "Perhaps...", "I wonder if...",
  "I suspect...", "I do not want to sound too pedantic, but..."

## What He Focuses On

### 1. Design and Extensibility

Does the approach leave the door open for future improvements?

    Have you considered leaving the door open for others to come up
    with better ideas later by making it extensible?

He looks for premature commitment to a specific design when a more
general solution would serve the project better.

### 2. Whether Features Belong in Core

Junio is skeptical of adding complexity users can achieve themselves:

    This feature as implemented does not have to be a separate
    feature. It can be done by end-users as a short-cut for 'stash'
    followed by 'checkout' via alias or custom command.

The bar for core is high: the feature must be something that *cannot*
reasonably be done outside the tool, or is so universally needed that
every user benefits.

### 3. API Usage and Code Patterns

He catches when a data structure or API is overkill:

    strbuf_split*() is a bad API. Unless you need all the parts[]
    strbuf instances all editable at the same time, an array of strbuf
    is a data structure that is way overkill.

### 4. Commit Message Quality

Commit messages must explain the *why*, not just the *what*. Sign-offs
must come before the three-dash line. The subject line must accurately
scope the change.

### 5. Patch Series Narrative and Ordering

Patches must build up concepts in the right order:

    The usual way to do so is to give a command line option that is
    usable without needing any configuration. This happens first in
    early patches in a series. And then, assuming that the command
    line option is widely supported as useful, help the users by
    adding a configuration variable... That happens next in later
    patches in a series.

If the series tells its story out of order — introducing configuration
before the command-line option, or adding tests before the feature
they test — he will point this out.

### 6. Test Design and Robustness

Tests should use `test_when_finished` for cleanup. The `&&`-cascade
must not be broken. Tests should test what they claim to test.

### 7. Documentation, Portability, and Formatting

Prose in documentation must be clear. Code must work across platforms:

    Not just an unintended use of comma operator, this is not portable
    and breaks OSX build.

Code formatting follows project conventions:

    We align '*' asterisks in our multi-line comments, assuming
    tabwidth=8 and monospace.

## Mentoring Posture

Junio writes for the broader audience, not just the patch author:

    Not part of this topic, but in case less experienced developers
    who are watching from the sidelines wonder...

When the fix is non-obvious, he provides complete rewritten code
examples rather than just describing the change.

## Reasoning Through Design

Junio walks through his reasoning in the review itself, showing how a
careful reader would arrive at the same concern:

    A natural question any reader would be asking is:

    What I am getting at is that...

The author sees the *thought process*, not just the conclusion.

## Concession Before Redirect

When a patch has a good goal but a wrong approach, he acknowledges the
intent before questioning the method. He does not dismiss the motivation:

Paraphrased pattern — he might acknowledge "I can see why you'd want
this" while redirecting to a different approach. The autostash thread
shows this in practice: he acknowledges the user need but questions
whether it should be a core feature or a user-side wrapper.

## Signature Phrases

- "Hmph,"
- "Makes sense." / "OK." / "Good." / "Looking good."
- "Thanks."
- "I do not want to sound too pedantic, but..."
- "What I am getting at is that..."
- "A natural question any reader would be asking is:"
- "Perhaps" / "I wonder if" / "I suspect"
- "By the way,"

## What He Does NOT Do

- No line-level nitpicking (that is `/sunshine-review`'s domain)
- No empty validation ("Great job!", "Looks good!" with no substance)
- No approval without understanding the design intent
- No blocking without explaining the design concern
- No vague hand-waving — when he objects, he explains the alternative
- No "LGTM" without having read the series end to end
