---
name: gut-mailing-list
description: >-
  Participate in the gut project's local mailing list — read and triage unread
  mail, reply to threads, file bug reports, and send patches via git send-email.
  Use when the user asks to check the list, work through unread mail, decide
  what to read first, reply to a thread, file an issue on the list, or send a
  patch to gut@mbp.localdomain.
disable-model-invocation: false
---

# gut-mailing-list

The gut project coordinates via a local mailing list at `gut@mbp.localdomain`.
Mail is delivered by Postfix to `~/Maildir` and read via himalaya.

## Purpose

The list is for discussion of the gut repo itself — its source, its
documentation, and patches against it. Traffic on the list should be grounded in
files that are tracked in this repository.

Follow the conventions established in the repo (see `README.md`,
`CONTRIBUTING.md`, `CLAUDE.md`). The list is a medium, not a source of new
policy — it doesn't override or supplement what the repo already documents.

## When to Use

- Reading the list inbox or a specific message
- Replying to a thread
- Filing a bug report or starting a new discussion
- Sending a patch or patch series
- Diagnosing mail delivery problems

## Infrastructure

| Component                | Role                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Postfix                  | MTA, must be running                                                                    |
| `/etc/postfix/transport` | `gut@mbp.localdomain → mlmmj:gut` (route to the list-manager pipe transport)            |
| `mlmmj-guttest` (podman) | Container running mlmmj for all local lists; per-list state under `~/var/mlmmj/<list>/` |
| Postfix `:10025` smtpd   | Relay endpoint mlmmj uses to hand processed list mail back to the host MTA              |
| `~/bin/deliver-maildir`  | Local Delivery Agent; files by `List-Id` into `~/Maildir/.<listname>/`, otherwise INBOX |
| `~/Maildir`              | Erik's Maildir (inbox + `.gut` list folder + `.Sent`)                                   |
| `~/MaildirClaude`        | Claude's Maildir (delivered via Postfix virtual transport; has `.Sent`)                 |
| himalaya                 | CLI mail client (`~/.config/himalaya/config.toml`)                                      |
| `/etc/postfix/vmailbox`  | Virtual map: `claude@gut.local` → `~/MaildirClaude`, `erik@gut.local` → `~/Maildir`     |

If delivery fails: `sudo postfix start` (check with `sudo postfix status`).

Both accounts' `message.send.backend.cmd` is `/usr/sbin/sendmail -t` — the `-t`
matters, because himalaya doesn't pass recipients on the command line and
sendmail needs to read them from the message's `To:`/`Cc:`/`Bcc:` headers. Each
account's Maildir also has a `.Sent/` subfolder so `himalaya template send` can
archive a copy after sending.

## Identities

Two deliverable identities on this host:

- **Erik** — `erik@localhost` / list address `gut@mbp.localdomain`. Reads in
  himalaya account `gut` (the default).
- **Claude** — `claude@gut.local`. Reads in himalaya account `claude`.

Claude files bug reports and sends patches **from `claude@gut.local`** so
replies to them via plain `r` in neomutt reach Claude's inbox (not bounce).
`@gut.local` mail is delivered through Postfix **virtual_mailbox_maps** — it
does **not** pass through `~/bin/deliver-maildir`.

## CLI reference

The full `himalaya` command reference — query DSL, every subcommand's flags, the
triage flag table, and folder layout — lives in
[`references/himalaya-cli.md`](references/himalaya-cli.md). The workflow
sections below show the commands you'll typically reach for; the reference
covers the rest.

Two accounts in `~/.config/himalaya/config.toml`:

| Account  | Maildir           | Default? | Usage                     |
| -------- | ----------------- | -------- | ------------------------- |
| `gut`    | `~/Maildir`       | yes      | Erik — reads list + INBOX |
| `claude` | `~/MaildirClaude` | no       | Claude — reads own inbox  |

Pass `-a, --account <NAME>` to override the default. Both accounts use
`/usr/sbin/sendmail -t` as the send backend and have a `.Sent/` folder so
`himalaya template send` can archive a copy.

## Reading the list

### Working through an unread stack

When several items are unread, don't read top-to-bottom. Most stacks have one or
two items that need a real response and a long tail of FYI; the goal is to
surface those before spending attention.

**Get the shape first.** Before opening any message:

```
himalaya envelope list -f .gut not flag seen   # what's unread
himalaya envelope thread -f .gut               # how it groups into threads
```

A thread with five unread replies is one unit of work, not five — the latest
reply usually subsumes the earlier ones. Act on the head; the rest collapse with
it.

**Classify before ordering.** Each unread thread falls into one of:

| Class            | Examples                                                    | Order within class                             |
| ---------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| Ball in my court | Direct ask, patch awaiting review, reply to me              | Oldest first — someone's waiting               |
| Engaged          | Thread I'm party to but not blocking                        | Latest reply; skim earlier if you've been away |
| Background       | List traffic, status posts, "What's cooking", notifications | Newest first; skip older entirely              |

"Newest first" is the right default _only_ when you can't classify. Once you
can, prefer the class-specific order — replying to yesterday's direct ask
matters more than reading yesterday's broadcast.

**The two accounts carry different priors.**

- `-a claude` (Claude's INBOX) — direct replies to Claude's mail. Default to
  ball-in-court until proven otherwise.
- `-a gut -f .gut` (Erik's `.gut` folder) — the list. Mostly broadcast;
  ball-in-court here is patches Claude sent or threads Claude opened.

Then act on each thread: `flagged` to defer, `seen` (implicit on plain `read`)
for handled, `answered` when you've replied. The full flag table is in
[`references/himalaya-cli.md`](references/himalaya-cli.md).

### Reading commands

Default to `-p/--preview` on `message read`. It shows the message without
flipping the `seen` flag. You can't put a message back to unread reliably once
you've read it without `-p` — flipping it manually via `flag remove <id> seen`
works, but only if you remember to, and only before any other tool has touched
the envelope. Read first, decide second.

```
himalaya envelope list -f .gut                          # recent first
himalaya envelope list -f .gut -s 20                    # last 20
himalaya envelope list -f .gut not flag seen            # unread only
himalaya envelope thread -f .gut -i 22                  # thread of msg 22
himalaya message read 22 -f .gut -p                     # read without marking seen
himalaya message read 22 -f .gut -p -H Message-ID       # pin specific headers
himalaya message read 22 -f .gut --no-headers -p        # body only
himalaya message read 22 -f .gut                        # marks seen — only after you've decided
```

**Claude's own inbox** (replies to Claude's mail land here):

```
himalaya envelope list -a claude
himalaya envelope list -a claude not flag seen
himalaya message read <id> -a claude -p
```

## Sending mail

Use himalaya's template pipeline. It lets the client generate `Date`,
`Message-ID`, MIME structure, and (for replies) threading headers — you provide
the parts that only you know (To, Subject, body). Two shapes cover everything:

### New message (bug report, announcement, RFC, …)

```bash
himalaya template write -a claude \
  -H "To: gut@mbp.localdomain" \
  -H "Subject: [BUG] short description" \
  "Body text. Literal \$vars, \`backticks\`, any content — it's a
single positional argument, no heredoc tricks needed." \
| himalaya template send -a claude
```

- `-a claude` picks Claude's account, which also fixes `From:` to
  `Claude <claude@gut.local>` — the deliverable identity that makes plain-reply
  in neomutt reach Claude's inbox.
- `-H KEY:VAL` prefills specific headers; repeat for each.
- The positional argument is the body. For longer bodies, write the body to a
  file and use `"$(cat /tmp/body.txt)"` as the argument, or feed it through a
  process substitution — whichever is cleaner in context.
- `template send` compiles the template to MIME, fills `Date:` and a real
  `Message-ID:`, delivers via `/usr/sbin/sendmail -t`, and archives a copy in
  `~/MaildirClaude/.Sent/`.

### Reply (preserves threading)

```bash
himalaya template reply <parent-id> -a gut -f .gut \
  -H "From: Claude <claude@gut.local>" \
  "ack, will investigate" \
| himalaya template send -a claude
```

- `-a gut -f .gut` is how you read the parent: the mailing list lives in Erik's
  account's `.gut` folder, so `template reply` has to look there.
- `-H "From: Claude <claude@gut.local>"` overrides the template's default
  `From:` (which would otherwise be Erik, since the parent is in Erik's
  maildir). The send-time account (`-a claude` on `template send`) determines
  the SMTP/sendmail backend and the `.Sent` folder, but the `From:` header comes
  from whatever is in the template — hence the explicit override.
- `template reply` auto-populates `Subject: Re: …`, `In-Reply-To`, `References`,
  and a reasonable `To:` (original sender + list). Add `-A` for reply-all if the
  parent has other recipients.

### Reply etiquette

`template reply` populates threading headers but does not author your body —
that's on you. The list is a public archive; write replies that stand on their
own for a future reader who lands on the message cold.

- **Quote the parent inline.** Use `>` to cite the lines you're responding to,
  then write your response below each quoted block.
- **Open with attribution.** Lead with `On <date>, <person> wrote:` before the
  first quoted block. Match the format already on the list, e.g.
  `On 26/04/23 06:46PM, Erik Cervin-Edin wrote:`.
- **Trim the quote to what you're addressing.** Keep the lines relevant to your
  response; drop signatures and unrelated sections.
- **No bare-agreement openings.** "Fair point", "Sounds good", "Yes" with no
  quoted context leave a future archive reader unable to tell _what_ the point
  was. Either quote the line you're agreeing to and respond inline, or don't
  reply.
- **Own the actual lesson when conceding.** If the reviewer's critique is "X is
  wrong because of Y", don't reply "X was misleading" — name Y. Misframing the
  cause invites the same mistake next time.

### Subject conventions

- `[PATCH]` / `[PATCH n/N]` — submitting a patch / patch series. `n/N` only when
  the patches form one topic; multiple unrelated fixes go out individually. See
  `CONTRIBUTING.md` § "Series vs standalone".
- `[BUG]` — blocking correctness bug
- `[MINOR]` — small correctness or style issue
- `[RFC]` — request for comments before implementing
- `Re:` is added automatically by `template reply`

Keep each message coherent: the issues in one message should be related. Don't
batch unrelated topics — split into separate threads so each can be discussed on
its own terms.

### Raw-eml escape hatch

When the template pipeline doesn't fit (e.g., you need to send a pre-built RFC
5322 message from elsewhere, or debug delivery with a hand-crafted message),
pipe raw text to sendmail directly:

```bash
/usr/sbin/sendmail gut < /tmp/raw.eml
```

You own every header — including `Date:` and (optionally) `Message-ID:`. Prefer
the template pipeline unless you have a reason to go raw.

## Sending patches

Use `git send-email` — it's already configured (see repo `.gitconfig`).

**Always pass `--from 'Claude <claude@gut.local>'`.** The repo's
`sendemail.from` is Erik's identity, so without the override, patches from
Claude ship signed as Erik and plain-replies bounce (same root cause as the
bug-report From: rule above).

```
git send-email --from 'Claude <claude@gut.local>' -1
git send-email --from 'Claude <claude@gut.local>' origin/main..HEAD
git send-email --from 'Claude <claude@gut.local>' -v2 -1
git send-email --from 'Claude <claude@gut.local>' --cover-letter ...
```

Delivery goes via local sendmail to bare `gut` (no `@domain` — this bypasses
git's FQDN validation, which otherwise rejects `localhost`).

### Rerolling a series

For v2+ rerolls — tagging convention (`<topic>/v<N>`), the two `--range-diff`
forms (bare tag for a single patch, range for a cover letter), `git notes` /
`--notes` for per-version prose, and the retrofit when v1 wasn't tagged — see
[`references/rerolling.md`](references/rerolling.md).

### Reading review feedback on the list

When Erik replies to a patch on the list, the review is _also_ a review of this
skill. If the mistake he points out is one this skill should have prevented,
update the skill to capture the lesson **before** re-rolling. The re-roll fixes
the one patch; the skill update fixes the next.

Before sending a patch, follow the "Generate and review your patch" step in
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md) — re-read the generated patch.
Most framing mistakes Erik has to point out on the list would be obvious from a
careful read before `git send-email`.

### Policy vs mechanics

Policy questions about patches — choice of starting point, when to use
`[PATCH n/N]` vs standalone, commit message conventions, the `Signed-off-by`
trailer and DCO, cover-letter expectations, iteration-and-conflict handling —
live in [`CONTRIBUTING.md`](../../../CONTRIBUTING.md), not here. This skill
documents the local mechanics (himalaya, git-send-email flags, mail
infrastructure); the canonical contribution policy is in the repo doc.

## Troubleshooting

- **Nothing arrives** — Postfix isn't running. `sudo postfix start`.
- **`template send` errors with "Recipient addresses must be specified"** —
  himalaya's configured sendmail command is missing `-t`. The config's
  `message.send.backend.cmd` must be `/usr/sbin/sendmail -t` so sendmail pulls
  recipients from headers.
- **`template send` errors with "cannot find maildir matching name Sent"** — the
  account's Maildir is missing a `.Sent/` folder. The message was still
  delivered (sendmail ran first); only the archive step failed. Create it:
  `mkdir -p ~/MaildirClaude/.Sent/{new,cur,tmp}` (same for `~/Maildir/.Sent`).
- **`git send-email` rejects the recipient** — pass bare `gut`, which bypasses
  git's FQDN check. Postfix appends `myorigin` to produce `gut@mbp.localdomain`,
  which the transport_maps entry routes to mlmmj. `gut@mbp.localdomain` works as
  the explicit form.
- **himalaya shows stale inbox** — `himalaya envelope list --refresh`.
- **Message in `~/Maildir/new/` but himalaya doesn't see it** —
  `~/bin/deliver-maildir` may have written to a wrong subfolder; check
  `ls ~/Maildir/`.
- **`@gut.local` mail missing** — not handled by `deliver-maildir`. Check
  `/etc/postfix/vmailbox` and the `virtual_mailbox_*` settings in
  `/etc/postfix/main.cf`; after edits:
  `sudo postmap /etc/postfix/vmailbox && sudo postfix reload`.

## Tips

- Keep lines under ~72 columns where practical.
- Sign off with your name on its own line, Git mailing list style.
- For multi-message sends (a patch series cover + patches, or several distinct
  bug reports), prefer invoking the template pipeline per message rather than
  batching — each send is cheap, and a per-message invocation keeps failure
  modes scoped.
