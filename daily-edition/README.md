# Daily edition

An [Agent Skill](https://agentskills.io) that turns today's news into one
visual page. The agent finds the stories and writes each up from its
sources; an [it's news](../README.md) approach renders them as timelines,
maps and charts, checking every figure and quote against those write-ups.
Claude publishes the page as an [artifact](https://code.claude.com/docs/en/artifacts);
Muse Code and other agents leave one HTML file.

| File | What it is |
|---|---|
| [skills/daily-edition/SKILL.md](skills/daily-edition/SKILL.md) | The skill, with its settings and their defaults |
| [prompt.md](prompt.md) | The prompt for a scheduled run |
| [PUBLISHING.md](PUBLISHING.md) | How to share the skill |

## Try it

From a clone, in Claude Code (signed in with a paid claude.ai plan) or Muse
Code (trust the workspace when asked):

```bash
cd it-s-news
claude "Make an it's news edition about tech and climate, 4 stories."
```

Claude publishes an artifact. Muse Code writes
`output/editions/<date>/edition.html`.

## Every morning in Claude

A [scheduled task](https://code.claude.com/docs/en/routines) runs Claude Code
in the cloud, even with your computer off. It needs a Pro, Max, Team or
Enterprise plan with GitHub connected.

1. At [claude.ai/code/routines](https://claude.ai/code/routines), click
   **New task**, then **Set up manually**.
2. Paste [prompt.md](prompt.md) and edit its settings. Schedule it daily, a
   few minutes past the hour (7:07, say).
3. Under **Advanced settings**, select this repository or your fork, and
   remove every connector.
4. In the cloud environment's settings, set **Network access** to **Full**,
   or to **Custom** with your outlets' domains plus the default package list.
   The default, **Trusted**, blocks most news sites.
5. Click **Create**, then **Run now**. The run's last message has the link.
6. Put that link in the prompt's `Artifact:` line, so later runs update the
   same page.

Share the page from the artifact's **Share** button. Once it's shared, a run
may pause to ask before updating it; answer from the run's page. Each run
counts against your plan's usage.

## Every morning in Muse Code

Copy [prompt.md](prompt.md) outside the repository (say
`~/.config/its-news/prompt.md`), edit it, delete the `Artifact:` line, and
schedule `muse exec` with cron:

```
7 7 * * * cd "$HOME/src/it-s-news" && git pull --ff-only && /full/path/to/muse exec --disable-approval --prompt-file "$HOME/.config/its-news/prompt.md" >> "$HOME/its-news.log" 2>&1
```

`--disable-approval` lets it run commands unattended, inside its sandbox. Run
it once by hand first, and read the log: exit code 0 only means the run ended.

## Ground rules

- Each article is the agent's own short write-up, linking the outlets it
  read. Quotes are short and attributed; paywalls are never bypassed.
- Nothing is committed: the skill writes to `output/`, which git ignores.
- The check proves the page matches the agent's articles, not the news.
  Spot-check the sources before sharing an edition widely.
