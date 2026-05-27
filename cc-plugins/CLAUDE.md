## Plugin versioning

Each plugin under `cc-plugins/` has a version in
`cc-plugins/<name>/.claude-plugin/plugin.json`. When editing a skill, bump the
version before committing:

- **Patch** (`0.1.2 → 0.1.3`) — wording, examples, bug fixes, clarifications; no
  change to what the skill does or how it's triggered
- **Minor** (`0.1.2 → 0.2.0`) — new behaviour, new steps, meaningful change to
  the skill's strategy
- **Major** (`0.1.2 → 1.0.0`) — incompatible change or full rewrite

The version decision belongs to the person asking for the change, not to Claude.
When in doubt, propose a patch bump and let the user correct it.
