# Daily edition: notes for AI agents

The rules in [../AGENTS.md](../AGENTS.md) apply here too. To make an edition,
follow [skills/daily-edition/SKILL.md](skills/daily-edition/SKILL.md).

When changing the skill:

- Keep it agent-neutral, and label anything only one agent can do.
- Frontmatter takes only `name`, `description`, `license`, `compatibility`,
  `metadata` and `allowed-tools`; claude.ai rejects the rest.
- Point to the approaches' AGENTS.md rather than copying them.
- Raise `version` in [.claude-plugin/plugin.json](.claude-plugin/plugin.json)
  for each release. Never rename the plugin or the skill.
- Tests, from this folder: `python3 -m unittest discover -s tests -v`
