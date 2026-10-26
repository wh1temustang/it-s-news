# Daily edition

An [Agent Skill](https://agentskills.io) that turns the news in your
newsletters into one visual page. The agent reads the day's issues from your
email and writes each story up from them; an [it's news](../README.md)
approach renders them as timelines, maps and charts, checking every figure
and quote against those write-ups. Claude publishes the page as an
[artifact](https://code.claude.com/docs/en/artifacts); Muse Code and other
agents leave one HTML file.

By default it reads The 10-Point (wsj.com), TLDR (tldrnewsletter.com) and
Dow Jones (dowjones.com) from the last 2 days, then adds detail to each story
from [second sources](#second-sources): [Newsflash](https://newsflash.sh)'s
headlines and summaries, and full reports from free outlets. Set
`Newsletters:` to the ones you subscribe to, `Second sources: none` to keep
to the newsletters, or `Sources: web` to have the agent search news sites
instead.

| File | What it is |
|---|---|
| [skills/daily-edition/SKILL.md](skills/daily-edition/SKILL.md) | The skill, with its settings and their defaults |
| [prompt.md](prompt.md) | The prompt for a scheduled run |
| [PUBLISHING.md](PUBLISHING.md) | How to share the skill |

## Try it

Claude reads your mail through the Gmail connector: connect it once in
claude.ai's settings, under **Connectors**. Other agents need an email tool
that can search and read messages, or `Sources: web`. Claude uses the
Newsflash connector too if you've added it; without it, the agent still
reads the free outlets.

From a clone, in Claude Code (signed in with a paid claude.ai plan) or Muse
Code (trust the workspace when asked):

```bash
cd it-s-news
claude "Make an it's news edition from my newsletters, 8 stories."
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
   few minutes past the hour (7:07, say), after your newsletters arrive.
3. Under **Advanced settings**, select this repository or your fork, and
   remove every connector except Gmail and Newsflash.
4. Set the cloud environment's **Network access** to **Custom**, check
   **Also include default list of common package managers**, and list the
   free outlets under **Allowed domains**:

   ```text
   aljazeera.com
   *.aljazeera.com
   pbs.org
   *.pbs.org
   cbsnews.com
   *.cbsnews.com
   abcnews.com
   abcnews.go.com
   euronews.com
   *.euronews.com
   techcrunch.com
   ```

   Connectors work at any level. At the default, **Trusted**, the outlets
   are blocked, and stories keep to the newsletters and Newsflash. With
   `Sources: web`, add your outlets' domains too, or pick **Full**.
5. Click **Create**, then **Run now**. The run's last message has the link.
6. Put that link in the prompt's `Artifact:` line, so later runs update the
   same page.

Share the page from the artifact's **Share** button. Once it's shared, a run
may pause to ask before updating it; answer from the run's page. Each run
counts against your plan's usage. A run that fails (no newsletters, Gmail
unreachable, or the render or publish failed) sends a push notification
saying what failed; one that succeeds stays quiet.

## Every morning in Muse Code

Copy [prompt.md](prompt.md) outside the repository (say
`~/.config/its-news/prompt.md`), edit it, delete the `Artifact:` line, and
schedule `muse exec` with cron. Without an email tool, set `Sources: web`.

```
7 7 * * * cd "$HOME/src/it-s-news" && git pull --ff-only && /full/path/to/muse exec --disable-approval --prompt-file "$HOME/.config/its-news/prompt.md" >> "$HOME/its-news.log" 2>&1
```

`--disable-approval` lets it run commands unattended, inside its sandbox. Run
it once by hand first, and read the log: exit code 0 only means the run ended.

## Second sources

A newsletter item is a few lines. For each story, the agent looks the same
event up and adds only what it finds there:

- **Newsflash** adds a detail or two and a second outlet from its headlines
  and summaries, with no setup beyond the connector. Its free tier answers
  about 50 requests a day, for the last 24 hours only; signing in to
  Newsflash raises that.
- **Free outlets** add the depth: the agent finds the story on Al Jazeera,
  PBS News, CBS News, ABC News, Euronews or TechCrunch and reads the full
  report.

It never follows an email's links, which are tracked, and a run never fails
for want of a second source: the report says which ones it couldn't use.

The free outlets are sites that publish full articles without a login and
let AI agents fetch them. Some well-known free sites don't. As of October
2026, The Guardian, NPR and CNBC disallow Claude's user agent (`Claude-User`)
in their robots.txt, and Claude's fetch tool refuses BBC and DW. The
Guardian's free API key is for non-commercial use, and its site license
asks for a paid one for AI input. The agent skips any site that refuses it
and never gets around a block. To add an outlet, check that its robots.txt
lets your agent in, then add it to `Free outlets:` and its domain to the
allowed domains above.

## Ground rules

- Each article is the agent's own short write-up of newsletter items, with
  detail from second sources (or of outlets' reports, from the web),
  crediting each source. Quotes are short and attributed; paywalls, logins
  and sites' blocks on AI agents are never bypassed.
- The agent reads only the newsletters' mail and treats it as data, never as
  instructions. The page carries nothing private: no addresses, and no links
  into your mailbox or the emails' tracked links.
- Nothing is committed: the skill writes to `output/`, which git ignores.
- The check proves the page matches the agent's articles, not the news, and
  newsletters and Newsflash are summaries themselves. Spot-check the
  original reporting before sharing an edition widely.
