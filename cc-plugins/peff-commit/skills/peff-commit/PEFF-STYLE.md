# Jeff King (peff) Commit Message Style

Reference for writing commit messages the way Jeff King writes them on the
Git mailing list. Distilled from his patches to git@vger.kernel.org.

## Subject Line

```
area: lowercase imperative description
```

- **50 char soft limit**, 72 hard limit
- Lowercase after the colon
- Imperative mood: "fix", "use", "avoid", not "fixed", "uses", "avoided"
- No period at the end
- Area prefix matches the file, subsystem, or logical component

## Body: Narrative Prose

The body reads like a debugging story or design explanation. It is NOT a
changelog entry. Peff walks the reader through the mechanism:

1. **Start with what the code does** — describe the current behavior or
   code path ("We mmap() a loose object file, storing the result in...")
2. **Show how that leads to the problem** — trace the causal chain
   ("But if we hit an error, we jump to a label which does X, and X is
   wrong because...")
3. **State the fix** — often a short final paragraph ("Use Y instead",
   "Apply the same fix here", "Drop the stale assignment")

### Tone

- **Conversational but precise** — uses "we", "our", as if talking to a
  peer on a mailing list
- **Plain language** — avoids jargon when a simpler word works
- **Tentative where appropriate** — "my guess is", "curiously", "I suspect"
- **No bullet points** — prose paragraphs only
- **No markdown headers** in the commit body

### Paragraph Structure

- Typically 2-4 paragraphs
- First paragraph: the problem (longest, most detailed)
- Middle paragraphs: context, history, or subtleties if needed
- Final paragraph: the fix (often just 1-2 sentences)

### Emphasis and References

- Uses _italics-style_ emphasis sparingly for subtle distinctions
  (rendered in email as underscores: "dispatched _from_")
- References other commits by abbreviated sha and subject:
  "1f3fd68e06 (odb/source: make read_object_stream() pluggable, 2026-03-05)"
- References related discussion: "This was caught during review of ..."
- Credits others when their report or review led to the fix

## What NOT to Do

- No bullet-point lists of changes
- No "This commit does X" self-referential framing
- No JIRA ticket numbers in the subject (put in footer if needed)
- No emoji
- No "Fixes #123" GitHub shorthand in the body (reference PRs by URL or
  prose instead)
- No restating what the diff already shows — explain the WHY

## Closing

End with a `Signed-off-by:` line using the actual author's identity.

If the change is a port of a fix from elsewhere, say so plainly:
"Apply the same fix here."

## Examples of Good Final Paragraphs

```
Use the pr_number input when available, falling back to github.ref for
non-dispatch triggers. That way each PR review gets its own concurrency
group regardless of how it was triggered.
```

```
Fix this by munmap()-ing the local "mapped" variable in the error path,
rather than st.mapped (which hasn't been assigned yet at that point).
```

```
So let's just drop the assignment entirely; nobody reads the value
after this point anyway.
```
