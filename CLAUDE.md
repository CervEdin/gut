# gut — Claude Code Instructions

## Mailing List

Development is coordinated via a local mailing list at `gut@mbp.localdomain`.
Two deliverable identities on this host:

- **Erik** — `erik@localhost`, list address `gut@mbp.localdomain`. Mail lands in
  `~/Maildir`; read via himalaya account `gut` (default).
- **Claude** — `claude@gut.local`. Mail lands in `~/MaildirClaude`; read via
  himalaya account `claude`.

Claude sends bug reports and patches **from `claude@gut.local`** so that
plain-reply in neomutt reaches Claude (not a bounce).

### Reading mail

```bash
himalaya envelope list                  # Erik's inbox (default `gut` account)
himalaya envelope list --folder .gut    # the mailing list folder
himalaya envelope list --account claude # Claude's inbox
himalaya message read <id>              # read a message
himalaya message reply <id>             # reply to a thread
```

The flag is `--account NAME`, **not** `-a NAME`.

### Sending patches

```bash
git send-email -1                     # send last commit
git send-email origin/main..HEAD      # send a patch series
```

`git send-email` is configured to deliver via local sendmail to `gut` (no domain
— bare username bypasses git's FQDN validation).

### Sending arbitrary mail

```bash
/usr/sbin/sendmail gut <<EOF
From: Claude <claude@gut.local>
To: gut@mbp.localdomain
Subject: your subject
Date: $(date -R)

Body here.
EOF
```

### Infrastructure

| Component                | Role                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Postfix                  | MTA; routes `gut@mbp.localdomain` to the mlmmj pipe transport                           |
| `/etc/postfix/transport` | `gut@mbp.localdomain → mlmmj:gut` (list-manager pipe transport)                         |
| `mlmmj-guttest` (podman) | Container running mlmmj; per-list state under `~/var/mlmmj/<list>/`                     |
| Postfix `:10025` smtpd   | Relay endpoint mlmmj uses to hand processed list mail back to the host MTA              |
| `~/bin/deliver-maildir`  | Local Delivery Agent; files by `List-Id` into `~/Maildir/.<listname>/`, otherwise INBOX |
| `/etc/postfix/vmailbox`  | Virtual map: `claude@gut.local` → `~/MaildirClaude`, `erik@gut.local` → `~/Maildir`     |
| `~/Maildir`              | Erik's Maildir (INBOX, `.gut`, `.patches`)                                              |
| `~/MaildirClaude`        | Claude's Maildir                                                                        |
| himalaya                 | CLI mail client (`~/.config/himalaya/config.toml`); accounts: `gut`, `claude`           |

`@gut.local` mail uses Postfix's **virtual** transport and **bypasses**
`~/bin/deliver-maildir`. If debugging `@gut.local` delivery, look at
`/etc/postfix/vmailbox` and the `virtual_mailbox_*` settings in
`/etc/postfix/main.cf` — not the script.

Postfix must be running. If it isn't: `sudo postfix start`
