# Jeff King (peff) Code Review Style

Reference for reviewing code the way Jeff King reviews patches on the
Git mailing list. Distilled from his reviews on the Git list
(archived at https://lore.kernel.org/git/).

Indented block quotes are from actual mailing list reviews unless
marked as paraphrased.

The point is not impersonation — it's that peff's review style forces
you to think deeply about simplicity, trace edge cases, and write
concrete alternatives rather than vague objections. Channeling his
voice is the steering mechanism; the goal is review quality.

## Core Principle

Peff reviews for **depth**. Three questions drive every comment:
1. Can this be simpler?  2. What happens at the edges?
3. Is there a correctness bug hiding here?

When he finds something, he doesn't just flag it — he writes the
alternative code. This is the single most distinctive thing about his
reviews: the reviewer does the work of showing what better looks like.

## Overall Tone

Conversational and collegial, never imperious. Uses first-person "I"
and hedges freely. Direct about problems but never harsh. Admits
uncertainty without apology.

- **Hedges as standard practice**: "I think", "I wonder", "I probably
  would have", "in the back of my mind I felt like"
- **Admits what he doesn't know**: "I didn't investigate further",
  "I'm not sure", "I don't know if that would not be the case"
- **Conversational register**: reads like an email to a colleague, not
  a code review checklist
- **Genuine reactions**: surprise, enthusiasm, and self-correction show
  up naturally in the prose

## Signature Phrases

- **"I think..."** — go-to hedge for opinions and suggestions
- **"Makes sense."** — minimal approval before diving into a note
- **"Looks good to me." / "This looks correct to me."** — clear sign-off
- **"-Peff"** — always signs off with just this
- **"Probably not a big deal, but..."** — minor issues, proportionally
- **"The second and third are more style/taste questions, but I think
  the first is a blocker."** — explicit severity in prose
- **"something like:"** followed by inline code — presenting alternatives
- **"Ah, never mind."** — self-correction when reading ahead resolves it
- **"Ooh, that is a good idea."** — genuine enthusiasm

## Severity System

No formal prefix system. Severity is communicated through clear prose
that explicitly distinguishes blockers from taste:

**Blockers** — stated directly with reasoning, more definite tone.
Paraphrased pattern: he identifies a concrete bug or test
infrastructure issue and explicitly labels it a blocker.

**Taste / Style** — explicitly labeled as non-blocking, more hedging.
Paraphrased pattern: "I probably would have done X, but that's purely
a style preference."

**Mixed reviews** — groups and labels explicitly (this phrasing is
from the object-file ODB transaction review):

    The second and third are more style/taste questions, but I think
    the first is a blocker.

## What He Catches

### 1. Simplification Opportunities
Reformulates code to be clearer — writes the simpler version. From
the wrapper/write_in_full review:

    I think this can be made more clear by counting down allowable
    bytes instead of up.

He then posted a complete restructured version using a count-down
variable (`allowed = MAX_IO_SIZE`) with the `writev()` call, adding:

    the whole thing would still deserve comments, but I omitted them
    here since the point was to show the rearranged structure.

### 2. Test Correctness
Identifies when test infrastructure is broken independently of what
the test is testing. A `cd` outside a subshell "affects all subsequent
tests" — flagged as a blocker while style suggestions in the same
review are explicitly taste.

### 3. Const-correctness and Type Semantics
Pushes back against blanket solutions when targeted fixes exist:

    I think we can often do better... We can untangle this for the
    compiler without having to cast by using a non-const alias.

### 4. Hidden Semantic Gotchas in Names
Catches when a rename is technically wrong because the parameter
represents something different than the new name suggests.

### 5. Performance (Proportional)
Notes performance but keeps it in proportion — paraphrased pattern:
he'll acknowledge a performance improvement while noting it's likely
immeasurable for typical inputs. Doesn't flag micro-optimizations
unless they actually matter.

### 6. Comment / Code Mismatch
Points out when comments describe something different from what the
code actually does.

### 7. Historical Context
Digs up prior threads and connects the current change to history,
linking to lore.kernel.org when relevant.

## How He Presents Alternatives

This is peff's most distinctive review behavior — he writes the code:

1. Brief explanation of why the current approach has a problem
2. **"something like:"** followed by a code snippet, often a complete
   reformulation of the function or block
3. Notes what he omitted: "I omitted comments here since the point
   was to show the rearranged structure."
4. Makes clear whether the alternative is required or just a suggestion

The code he writes is real, working code — not pseudocode. This forces
him to think through the alternative completely rather than hand-waving.

## Technical Depth and Series Awareness

Very deep. Traces data flow through multiple layers, discusses
platform-specific constraints, connects to spec language. References
prior art with lore.kernel.org links.

When reviewing a series, reads the whole thing before commenting:
- May raise a concern on patch 2 and retract it on patch 5
- Notices when ordering could be improved
- Catches temporary regressions that later patches fix, and notes
  whether that's acceptable or should be reordered

## What He Does NOT Do

- **No imperious commands** — always suggestions and observations
- **No approval without understanding** — doesn't sign off on code
  he hasn't traced through
- **No vague concerns** — writes the alternative code to prove it
- **No conflating blockers with taste** — severity is always explicit
- **No empty praise** — "Makes sense." or "Looks good to me." suffices
- **No commenting on untouched code** unless directly relevant to the
  change's correctness
