# Jeff King (peff) Commit Message Style

Reference for writing commit messages that channel Jeff King's voice and
approach. Distilled from his patches to git@vger.kernel.org.

The point is not impersonation — it's that peff's style forces you to
articulate the reasoning behind a change. Channeling his voice is the
steering mechanism; the goal is reasoning quality.

## Subject Line

The default peff format is:

```
area: lowercase imperative description
```

However, **the repo's existing convention always wins**. If the recent
commit log uses Conventional Commits (`feat:`, `fix:`, `chore:`,
`feat(scope):`, etc.), use that format instead:

```
fix(auth): handle nil pointer in batch resolver
feat: add retry logic for transient failures
```

General rules regardless of format:

- **50 char soft limit**, 72 hard limit
- Lowercase after the colon
- Imperative mood: "fix", "use", "avoid", not "fixed", "uses", "avoided"
- No period at the end
- If the repo does NOT use Conventional Commits, area prefix matches the
  file, subsystem, or logical component (peff's default)
- For tightly scoped changes, a function name works as the area prefix:
  `check_connected(): delay opening new_pack`,
  `find_last_dir_sep(): convert inline function to macro`

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
- **Tentative where appropriate** — "my guess is", "curiously",
  "I suspect", "I don't think it matters much"
- **Humble about scope** — "not urgent, but since we're here we might as
  well fix it", "probably not worth as many words as I wrote"
- **Prose paragraphs preferred** — but numbered lists are fine when
  enumerating genuinely distinct items (e.g., "two independent reasons
  this is broken: 1. ... 2. ...")
- **No markdown headers** in the commit body

### Paragraph Structure

- Typically 2-4 paragraphs
- First paragraph: the problem (longest, most detailed)
- Middle paragraphs: context, history, or subtleties if needed
- Final paragraph: the fix (often just 1-2 sentences)

### Discussing Alternatives

A distinctive peff pattern: explain approaches you considered but didn't
take, and why. This proves you understand the design space, not just the
diff. Examples from real patches:

> One option to prevent this is to limit the depth of recursion we'll
> allow. This is conceptually easy to implement, but it raises other
> questions: what should the limit be, and do we need a configuration
> knob for it?

> It would be easy-ish to insert an extra check like:
> `can_filter_bitmap(&opt->objects_filter);` into the conditional, but
> I didn't bother here. It would be redundant with the call in
> for_each_bitmapped_object(), and the can_filter helper function is
> static local in the bitmap code.

You don't need to manufacture alternatives — but when you genuinely
considered another approach, say so and say why you didn't take it.

### Quantitative Evidence

When the change has measurable impact, include the numbers. Peff
frequently embeds benchmark output, object counts, or timing data
directly in the commit body. The data grounds the reasoning in reality
rather than hand-waving about performance.

### Emphasis and References

- Uses _italics-style_ emphasis sparingly for subtle distinctions
  (rendered in email as underscores: "dispatched _from_")
- References other commits by abbreviated sha and subject:
  "1f3fd68e06 (odb/source: make read_object_stream() pluggable, 2026-03-05)"
- References related discussion: "This was caught during review of ..."
- Credits others when their report or review led to the fix

## What NOT to Do

- No bullet-point changelogs ("- changed X", "- added Y")
- No "This commit does X" self-referential framing
- No JIRA ticket numbers in the subject (put in footer if needed)
- No emoji
- No "Fixes #123" GitHub shorthand in the body (reference PRs by URL or
  prose instead)
- No restating what the diff already shows — explain the WHY
- No false confidence — if you're not sure why something works, say so

## Closing

End with a `Signed-off-by:` line using the actual author's identity.

If the change is a port of a fix from elsewhere, say so plainly:
"Apply the same fix here."

## Notes

Notes are observations that sit alongside the commit message but aren't
part of it. They surface your reasoning, uncertainties, and caveats —
the things that help a reviewer (or your future self) understand not
just what you decided, but what you were thinking.

Use notes for:
- **Alternatives not taken** — why another approach was tempting but wrong
- **Caveats** — things that are still ugly or incomplete
- **Uncertainties** — things you're not confident about
- **Scope decisions** — why you stopped where you did

From peff's real patches:

> It would perhaps make more sense for diff-highlight to chomp all
> incoming lines, then do its comparisons, and then add a newline back
> on output. That's a bigger change, so I punted on it for now.

> I think the rewrite of xmkstemp() triggered Coverity to consider this
> a "new" problem, even though it has been there for years. So not
> urgent, but this is mostly just trying not to waste the brain cycles I
> spent analyzing. :)

The notes are the reasoning checkpoint. If someone reads your notes and
thinks "wait, that alternative is actually better" or "that's not why
we're doing this", it surfaces the misunderstanding before it gets
committed.

## Examples of Good Final Paragraphs

```
This could easily be fixed by chomping the prefix, too, but I think the
problem is deeper. [...] So let's catch this early in
is_pair_interesting() and bail to our usual passthrough strategy.
```

```
So we know that bitmaps help when there's filtering to be done, but
otherwise make things worse. Let's only use them when there's a filter.
```

```
The recursion here is simple enough that we can avoid those questions by
just converting it to iteration instead.
```
