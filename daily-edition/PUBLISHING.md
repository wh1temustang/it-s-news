# Publishing the daily-edition skill

Every route needs this repository to stay public: outside a clone, the skill
fetches it from GitHub.

## Before each release

```bash
(cd daily-edition && python3 -m unittest discover -s tests)
claude plugin validate . && claude plugin validate --strict daily-edition
```

(`--strict` needs a recent Claude Code.) Then raise `version` in
[.claude-plugin/plugin.json](.claude-plugin/plugin.json): installs update only
when it changes. Never rename the plugin (`its-news`) or the skill
(`daily-edition`).

## 1. Claude Code plugin from this repository

[../.claude-plugin/marketplace.json](../.claude-plugin/marketplace.json) makes
this repository a plugin marketplace, live once it's on the default branch.
Users run:

```bash
claude plugin marketplace add wh1temustang/it-s-news
claude plugin install its-news@its-news
```

then `/its-news:daily-edition`, and `claude plugin update its-news@its-news`
for new versions.

## 2. Anthropic's directory

Reaches people browsing plugins on claude.ai, in Cowork and in Claude Code.
It needs a paid plan, or an Owner on Team and Enterprise. Go through the
[pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist),
then submit at [claude.ai/directory/manage](https://claude.ai/directory/manage)
as [Submit a plugin](https://claude.com/docs/plugins/submit#submit-a-plugin)
describes. Anthropic reviews each version.

## 3. claude.ai upload

```bash
cd daily-edition/skills && zip -r ~/Desktop/daily-edition.zip daily-edition
```

On claude.ai: **Customize > Skills > + > Create skill > Upload a skill**, with
code execution on. On Team and Enterprise, share it with the organization
from its **⋯** menu. Skills on your account also load in your Claude Code
cloud sessions, scheduled tasks included.

## 4. Muse Code

Inside a clone there's nothing to install. Elsewhere:

```bash
muse skills install daily-edition/skills/daily-edition --scope user
```

Meta documents no marketplace for Muse yet, so share the link to this folder.

## 5. Other agents

Copy [skills/daily-edition/](skills/daily-edition/) into the agent's skills
folder, such as `~/.agents/skills/`.
