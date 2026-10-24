---
name: daily-edition
description: Finds today's news, writes each story up as a short Markdown article from its sources, renders them as one visual it's news edition (timelines, maps, charts) and publishes the page, as a Claude artifact where possible. Use for a daily news digest or briefing page, or when a scheduled run asks for an it's news edition.
license: MIT
compatibility: Needs git, Python 3.10 or newer, network access, and a web search or browsing tool.
---

# it's news: daily edition

## Settings

Take them from the request and use these defaults for the rest. Don't stop
to ask.

- Topics: world, business, tech, science, climate (one section each)
- Stories: 5, at most 2 per topic
- Region: none. Outlets: established ones readable without a login. Window:
  the last 24 hours.
- Language: English. Approach: `template-rendering`. Title: it's news daily.
- Artifact: none, so publish a new one. A claude.ai artifact link means
  update that artifact.

## 1. Set up

Work in the it's news repository if you're in it; otherwise run
`git clone --depth 1 https://github.com/wh1temustang/it-s-news.git`. Read its
`AGENTS.md`, find the approach the settings name (stop if it isn't listed),
then read that approach's `AGENTS.md` and set it up. Where it differs from
this skill, it wins. Write everything to `output/editions/<date>/` at the
repository root, with `<date>` from `date +%F`, and never commit it.

## 2. Pick and read the stories

- Search each topic within the window, region and outlets. Prefer stories
  that several outlets report and that have figures, dates, places, events
  and named quotes: they make the page.
- Skip opinion, sponsored content, live blogs, and anything behind a login
  or paywall. Never get around one.
- One story per event. When updating an earlier edition, read it and skip
  what it covered unless there's news. Leave out topics with nothing good.
- Read each story on one to three outlets' own pages, not search snippets.
  Ask fetch tools for figures and quotes verbatim. Drop what you can't read.

## 3. Write each article

`output/editions/<date>/<slug>.md`, with a short lowercase slug:

```markdown
---
title: Port strike halts container traffic in Rotterdam
sources: [Example Times](https://example.com/strike), [Example Wire](https://example.org/rotterdam)
published: 2026-10-23
---

# Port strike halts container traffic in Rotterdam

Most important facts first.
```

`sources` links every outlet you read; `published` is the newest report's
date. The page is checked only against this article, so:

- Every fact comes from a page you read, nothing from memory.
- Copy figures as the source writes them: no rounding, converting or adding.
- Quotes are word for word, short and attributed. Mark translated ones.
- Attribute claims as the sources do. When they disagree, give each version.
- Write 150 to 400 words of your own, in the edition's language.

## 4. Render

Follow the approach's `AGENTS.md` for an edition, one section per topic. With
`template-rendering`, from its folder:

1. Write `<slug>.storyboard.json` beside each article and run
   `.venv/bin/python -m template_rendering check ../output/editions/<date>/<slug>.md ../output/editions/<date>/<slug>.storyboard.json`
   until it passes. Fix the storyboard, not the article. Drop a story that
   still fails after three rounds.
2. Write `output/editions/<date>/edition.json`, shaped as
   `template-rendering/template_rendering/edition.schema.json` describes, with
   paths relative to it: the title, the date as readers write it, a one-line
   `dek`, and the `footer` "Written by an AI agent from the reports linked
   under each headline.", in the edition's language.
3. For a language other than English, write `labels.json` with the page's
   words translated (keys in `template-rendering/template_rendering/labels.py`)
   and pass `--labels`.
4. Run `.venv/bin/python -m template_rendering edition ../output/editions/<date>/edition.json -o ../output/editions/<date>/edition.html`

## 5. Publish and report

If you can publish Claude artifacts, publish `edition.html` with the
edition's title, updating the Artifact setting's artifact if there is one.
Leave sharing to its owner. Otherwise, give the file's full path.

End with the link or path, each story with its outlets, the stories you
dropped and why, and the defaults you used.
