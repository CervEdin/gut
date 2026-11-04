# Sources behind comment-review

The evidence for the checks in `SKILL.md`, quoted from Git and Linux project
documents, Git mailing-list reviews and Python. Quote these when a finding needs
backing; do not paraphrase them into stronger claims. The checks with no source
are listed under "Not sourced" at the end.

Revisions: Git `dbe7529fe1`, Linux `05441d697f7f`. Mailing-list messages are
named by author, date, subject and Message-ID; each opens at
`https://lore.kernel.org/git/<Message-ID>/`.

## Where text lives

Git splits the work between comments and the log:

    Clearly written code and in-code comments
    explain how the code works and what is assumed from the surrounding
    context.  The log messages explain what the changes wanted to
    achieve and why the changes were necessary

-- Git `Documentation/CodingGuidelines`, opening section

Those who change the code later read the log for the why:

    those who need to fix or enhance your code in the future
    will need to know _why_ your code does what it does

-- Git `Documentation/SubmittingPatches`, "Describe your changes well"

Text for this round of review goes below the `---` line, and stays out of
history:

    This commentary is important for the on-going email discussion but
    does not belong in the commit message for the permanent project
    history, so place it below the "---" line just under your sign-off.

-- Eric Sunshine, 2014-03-03, "Re: [PATCH] commit.c: Replace starts_with() with
skip_prefix()"
<CAPig+cQuzWv1+yg6F4zBqYfGdH6iz5xteCFHW6_o8Wyx68JT7w@mail.gmail.com>

    Other comments relevant only to the moment or the maintainer, not
    suitable for the permanent changelog, should also go here.

-- Linux `Documentation/process/submitting-patches.rst`

## Why now

A comment that explains the change, not the code, belongs in the log:

    such a
    comment does not help understanding the new code, which is the only
    thing the people who read the comment sees, without knowing what was
    there previously---it belongs to the commit log message as a rationale
    to make that change

-- Junio C Hamano, 2018-07-09, "Re: [PATCH v3 06/24] multi-pack-index: load into
memory" <xmqq36wsdy75.fsf@gitster-ct.c.googlers.com>

    "I wanted the call here for core.commentChar" is better said in the
    log message, as that will not stay true forever

-- Junio C Hamano, 2016-05-02, "Re: [PATCH v2] trailer: load config to handle
core.commentChar" <xmqqy47stjjg.fsf@gitster.mtv.corp.google.com>

    But that kind of information belongs to the log message,
    not in-code comment.

-- Git commit `0d583ff02d`, "show-ref: remove a stale comment"

## Restates, and grep answers it

    It takes longer to read and digest this comment block than it does to
    comprehend the actual logic in code, which is pretty clear in its
    current form.

-- Eric Sunshine, 2015-11-01, "Re: [PATCH v4] checkout: add --progress option"
<CAPig+cSLC_xkpXEznzPQdA=FE6GV5VSuwSrFy62Nzybv7jQf1g@mail.gmail.com>

    If
    someone needs to know which commands share this documentation, a
    suitable "grep" invocation will provide the same information but will
    be correct at that point in time

-- Eric Sunshine, 2025-07-17, "Re: [GSoC][RFC PATCH v2 1/2] builtin/refs: add
list subcommand"
<CAPig+cQgeqz9bNQSFRvTmoyFgqAwEKSV=KpK18DSP7FA-4GDPw@mail.gmail.com>

    Inline comments are unnecessary and in fact distracting if they state
    the obvious.

-- PEP 8, "Inline Comments" (its example: `x = x + 1  # Increment x`)

    Do not reiterate what the code literally does; let the code
    speak for itself.  If the code itself is inscrutable, comments will not help.

-- Linux `Documentation/process/maintainer-kvm-x86.rst`

## Code could say it, and wrong or stale

    comments invariably tend to stale out when the code
    they were describing changes.  Often splitting a function
    into two makes the intention of the code much clearer.

-- Git `Documentation/CodingGuidelines`

The frequency test, one site against several:

    If a check for "is it one of the no-op commands?" appears only
    here, a single liner comment may be sufficient (but necessary)
    to help readers.  Otherwise a single-liner helper function
    [...] with a descriptive name would
    be better than a single liner comment.

-- Junio C Hamano, 2016-12-16, "Re: [PATCH v2 20/34] sequencer (rebase -i): copy
commit notes at end" <xmqqvaujr7ed.fsf@gitster.mtv.corp.google.com>

A new name does not replace a stated assumption:

    I do
    agree it is a good idea to rename it [...]
    but I doubt renaming alone would
    reduce the need for the new comment.

-- Junio C Hamano, 2016-10-03, "Re: [PATCH] diff_unique_abbrev(): document its
assumtion and limitation" <xmqqr37x743x.fsf@gitster.mtv.corp.google.com>

An assertion over a "caller must hold" comment:

    In PROVE_LOCKING kernels, lockdep_assert_held() emits a warning
    if the caller doesn't hold the lock.  Comments can't do that.

-- Linux `Documentation/process/maintainer-tip.rst`, "Documenting locking
requirements"

Unless the assertion checks less than the comment. Python's lock has no owner,
so no assertion can say "the caller holds it":

    A lock is not owned by the thread that locked it; another thread may
    unlock it.

-- Python `threading.Lock` docstring (3.13)

## Keep check

    Certain things should always be commented.  Uses of memory barriers should
    be accompanied by a line explaining why the barrier is necessary.  The
    locking rules for data structures generally need to be explained somewhere.
    [...] Non-obvious dependencies between separate bits of code should be pointed
    out.  Anything which might tempt a code janitor to make an incorrect
    "cleanup" needs a comment saying why it is done the way it is.

-- Linux `Documentation/process/4.Coding.rst`

A removed comment can take an invariant with it:

    Granted, the comment above the block points out why there aren't
    duplicates, but will that be obvious to future readers now that you've
    removed the whole comment?

-- Elijah Newren, 2025-02-11, "Re: [GSoC][PATCH] merge-recursive: optimize
string_list construction"
<CABPp-BHMgTX2J4pRM=DjU-Ye46JtVZJsi95VUqcPHTcrzJgwOg@mail.gmail.com>

A lasting subtlety can earn its way out of history into the source:

    Make sure we don't need to look again into the depths of git blame in
    order not to miss a subtle part about how rcu-tasks is dealing with
    exiting tasks.

-- Linux commit `e4e1e8089c5f`, "rcu-tasks: Improve comments explaining
tasks_rcu_exit_srcu purpose"

Comments that pass the keep check, all in Linux at `05441d697f7f`:

- `mm/filemap.c`, the "Lock ordering:" block near the top of the file.
- `arch/x86/kernel/cpu/amd.c`, `fix_erratum_1386()`: why XSAVES is cleared and
  why XSAVEC is equivalent on the affected parts.
- `kernel/fork.c`, `copy_process()`: why the racy `nr_threads` check is
  harmless.
- `kernel/sched/core.c`, `try_to_wake_up()`: "Pairs with the smp_store_release()
  in finish_task()", naming the other half of the ordering.

## Wrong place in the code

Contract at the definition, justification at the use:

    ``# Safety`` sections specify the contract that callers
    (for functions) or implementors (for traits) need to abide by. ``// SAFETY:``
    comments show why a call (for functions) or implementation (for traits) actually
    respects the preconditions stated in a ``# Safety`` section

-- Linux `Documentation/rust/coding-guidelines.rst`. Cited here for placement
only; `// SAFETY:` itself is a directive.

## API docs

    Multi-line docstrings consist of a summary line just like a one-line
    docstring, followed by a blank line, followed by a more elaborate
    description.

-- PEP 257, "Multi-line Docstrings"

    Do not add boilerplate
    kernel-doc which simply reiterates what's obvious from the signature
    of the function.

-- Linux `Documentation/process/coding-style.rst`, added by `e5880f95a979`

## Form follows the file

    Modifications to existing
    code are expected to match the style the surrounding code already
    uses (even if it doesn't match the overall style of existing code).

-- Git `Documentation/CodingGuidelines`

## Touched docs: common case first

A user report, not a stated rule. Users asked for the common case first in Git's
manual pages:

    One user also commented that "If no pathspec was given..." makes
    `git checkout <branch>` sounds like a special edge case, instead of
    being one of the most common ways to use this core Git command.

-- Git commit `21a5f9442e`, "doc: git-checkout: clarify intro sentence"

## Not sourced

These rules in `SKILL.md` have no source above. Do not quote this file to back
them; say they are the skill's own rule.

- The words that suggest keep (lock, ordering, race, pairs with, erratum,
  workaround, upstream, spec). They send a comment back to the keep check and
  decide nothing on their own.
- "Repeated" at three or more places for prose. The frequency test above sets
  the line for a helper at more than one site; no source sets one for prose.
- The "Working note" step, including its `TODO`/`NEEDSWORK` advice.
- The "Directives" step.
- The "Touched docs" rules other than common case first: an example where one
  helps, removed behaviour removed, active voice and short sentences.
- Mood and person in API docs. PEP 257 uses the imperative ("Return the ..."),
  and Javadoc is said to use the third person ("Returns the ..."), but the
  Javadoc guide was not read. "Follow the file" rests on the Git quote above.
