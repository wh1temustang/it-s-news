# Notes for AI agents

it's news tries more than one approach to making news quick to take in. Each
approach lives in its own folder, with its own AGENTS.md, setup and tests.
Before working in a folder, read its AGENTS.md.

## Approaches

- [template-rendering/](template-rendering/AGENTS.md): an AI agent picks
  pre-built visual templates for an article, and code checks and renders the
  page. Use it when asked to present, storyboard or render a news article,
  unless another approach is named.
- [animated-explainer/](animated-explainer/AGENTS.md): a prototype that tells
  an article as a few pages of click-through vector animation. It has one
  hand-built example and no pipeline yet. Use it only when asked for an
  animated explainer.

## Today's news

- [daily-edition/](daily-edition/AGENTS.md): an Agent Skill that reads
  today's newsletters from email (or searches the web), writes each story up
  as an article, renders them with an approach and publishes the page. When asked for an edition of today's or
  this week's news, follow
  [daily-edition/skills/daily-edition/SKILL.md](daily-edition/skills/daily-edition/SKILL.md).

## Adding an approach

- Give it its own top-level folder with a README.md, an AGENTS.md, a
  CLAUDE.md that holds `@AGENTS.md`, and its own setup and tests.
- List it above, in the "Approaches" table in [README.md](README.md), and as
  a job in [.github/workflows/tests.yml](.github/workflows/tests.yml).

## Rules

- English for code, comments, docs and content.
- This is a public repository. Never commit credentials, `.env` files or
  personal data (see [README.md](README.md)).
- Sample articles must be fictional, say so in their first lines, and set
  `fictional: true` in their front matter.
- Generated output (`output/`) is not committed.
