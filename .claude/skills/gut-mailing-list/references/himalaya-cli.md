# himalaya CLI reference

`himalaya` (v1.2.0, `+maildir +sendmail`) is the mail client. Two accounts in
`~/.config/himalaya/config.toml`:

| Account  | Maildir           | Default? | Usage                     |
| -------- | ----------------- | -------- | ------------------------- |
| `gut`    | `~/Maildir`       | yes      | Erik — reads list + INBOX |
| `claude` | `~/MaildirClaude` | no       | Claude — reads own inbox  |

Both accounts have `message.send.backend = sendmail` pointing at
`/usr/sbin/sendmail -t`, and a `.Sent/` folder in their Maildir so
`himalaya template send` can archive a copy. This makes the
`himalaya template write | template send` pipeline the primary path for sending
mail — see SKILL.md "Sending mail" for the workflow.

## Command tree

```
himalaya
├── account        configure | doctor [--fix] | list
├── folder         add | list | expunge <f> | purge <f> | delete <f>
├── envelope       list [QUERY]    | thread [QUERY] [-i <id>]
├── flag           add | set | remove    <id-or-flag>...
├── message        read | export | thread | write | reply | forward
│                  edit | mailto | save | send | copy | move | delete
├── attachment     download <id>...
└── template       write | reply | forward | save | send
```

## Global flags (every subcommand)

- `-a, --account <NAME>` — override default account. **Short flag works.**
  Earlier notes claimed `--account` only; that was wrong.
- `-o, --output <plain|json>` — `json` for programmatic parsing.
- `-c, --config <PATH>` — alt config.
- `--quiet` / `--debug` / `--trace` — log verbosity.

## envelope list — the primary read command

```
himalaya envelope list [OPTIONS] [QUERY]...
  -f, --folder <NAME>       default INBOX
  -p, --page <N>            1-indexed, out-of-range errors
  -s, --page-size <N>       limit per page  ← use instead of `| head`
  -w, --max-width <COLS>    truncate table width
  -a, --account <NAME>
  -o, --output <plain|json>
```

**QUERY** is a filter + sort DSL. Do **not** pipe to `grep`/`head`/ `sed` — the
DSL does it natively and more robustly.

Conditions: `date <yyyy-mm-dd>` · `before <d>` · `after <d>` · `from <pat>` ·
`to <pat>` · `subject <pat>` · `body <pat>` · `flag <f>` (flags: `seen`,
`answered`, `flagged`, `deleted`, `draft`, plus custom).

Operators: `not <c>` · `<c> and <c>` · `<c> or <c>`.

Sort: `order by <kind> [asc|desc]` where kind ∈ `date`, `from`, `to`, `subject`.
Example combined:

```
himalaya envelope list --folder .gut \
  subject "[BUG]" and after 2026-04-15 \
  order by date desc
```

## envelope thread — conversation view

```
himalaya envelope thread --folder .gut                  # all threads
himalaya envelope thread --folder .gut -i 22            # thread containing id 22
```

Much better than `envelope list` for following mailing-list discussion; shows
parent/child structure.

## message read / thread / export

```
himalaya message read  <id> [-f <folder>] [-p] [-H <Header>] [--no-headers]
himalaya message thread <id> [-f <folder>] [-p] [-H <Header>] [--no-headers]
himalaya message export <id> [-F] [-d <dir>] [-O]
```

- `-p/--preview` — don't set the `seen` flag.
- `-H <Name>` — repeatable; pins specific headers at top.
  `-H Message-ID -H From -H Subject` is the pattern for grabbing headers
  programmatically.
- `--no-headers` — body only.
- `message thread <id>` reads the whole conversation as a single human-readable
  stream.
- `message export -F -d /tmp/out.eml <id>` dumps the raw RFC 5322 message — the
  right tool when I need to inspect headers or archive.

## message send — send raw mail via himalaya

```
himalaya message send --account claude < /tmp/msg.eml
```

Uses the account's configured sendmail backend **and** saves a copy to the Sent
folder. This is the himalaya-native alternative to piping through
`/usr/sbin/sendmail gut` directly. For the gut list workflow I've been bypassing
it because piping to sendmail with recipient `gut` routes via Postfix's
`myorigin` rewrite to `gut@mbp.localdomain`, which the transport_maps entry
sends to mlmmj — both work; sendmail-pipe is simpler for list posts,
`message send` is right when I want the sent copy preserved.

## message reply / forward / write / edit — interactive

All four open `$EDITOR`. Don't use them in a non-interactive session; use the
`template` family (below) or write a raw `.eml` and pipe to `message send` /
sendmail.

- `message reply <id>`: `-A/--all` for reply-all, `-H KEY:VAL` to prefill
  headers, `[BODY]...` to prefill body.
- `message edit <id>`: `-p/--on-place` replaces the original.

## template write / reply / forward / send / save — non-interactive compose

The `template` family generates/accepts MML-flavored raw messages **without
opening $EDITOR** — useful when scripting. `template send` compiles MML to MIME
and sends; `message send` takes already-raw MIME.

For the gut workflow, raw `.eml` files + `message send` (or direct sendmail) are
simpler since the bodies are plain text — no MML needed.

## flag / folder / attachment / account

- `flag add 22 seen` / `flag remove 22 seen` — toggle read state. Args are mixed
  ids and flags: integers are ids, strings are flags.
- `folder expunge <name>` — permanently delete messages with the `deleted` flag
  in that folder (`message delete` only sets the flag).
- `folder purge <name>` — empty the folder (needs `-y`).
- `attachment download <id>... [-d <dir>]` — pull attachments.
- `account doctor [name] [--fix]` — diagnose config / backend issues.

## Triage — acting on a message

Maildir has five standard flags (`seen`, `answered`, `flagged`, `deleted`,
`draft`) plus custom ones. Map them to intent:

| Intent                             | Command                                                                                                  |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Peek without marking read          | `himalaya message read <id> -a claude -p`                                                                |
| Defer / "come back to this"        | `himalaya flag add <id> flagged -a claude`                                                               |
| Find all deferred later            | `himalaya envelope list -a claude flag flagged`                                                          |
| Mark handled (stop showing as new) | read it normally, or `flag add <id> seen`                                                                |
| Note that I replied                | `flag add <id> answered` (interactive `message reply` sets it; scripted replies via sendmail do **not**) |
| Park in another folder             | `folder add .deferred` once, then `message move .deferred <id>`                                          |
| Trash                              | `message delete <id>`                                                                                    |
| Permanent wipe                     | `folder expunge <folder>` (clears `deleted`)                                                             |

`flagged` is the canonical "defer" marker — standard, searchable
(`flag flagged`), and portable. Prefer it over custom flags like `todo`;
himalaya's own docs note custom flags aren't always preserved across backends.

After a scripted reply (raw `.eml` + sendmail), remember to
`flag add <parent-id> answered` if you want the conversation state to reflect it
— the sendmail path doesn't touch the envelope.

## Folder layout (this setup)

INBOX in `config.toml` is aliased to `.` (Maildir root). Listable folders on the
`gut` account:

- `INBOX` / `.` — Erik's personal mail + bounces
- `.gut` — the mailing list
- `.patches` — patch archive

Claude's account (`~/MaildirClaude`) has just `INBOX` so far. Use
`himalaya folder list --account claude` to inspect.
