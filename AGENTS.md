# Notes for AI agents

## Presenting an article

When asked to present, storyboard or render a news article (`.md`):

1. Read [agent/prompt.md](agent/prompt.md) and [agent/catalog.md](agent/catalog.md)
   in full, then the schema of each template you're considering
   (`itsnews/templates/<id>/schema.json`). Don't work from memory.
2. Read the whole article.
3. Write the storyboard as `<article>.storyboard.json` next to the article,
   following the prompt.
4. Run `python -m itsnews check <article.md> <storyboard.json>` and fix every
   problem it reports. Repeat until it passes. Never change the article to
   make the check pass.
5. Run `python -m itsnews render <article.md> <storyboard.json>`. The page goes
   to `output/<article>.html`.
6. Report which templates you chose and why, plus anything the article
   couldn't support.

## Working on the code

- Setup: `python3 -m venv .venv && .venv/bin/pip install -e .`
- Tests: `.venv/bin/python -m unittest discover -s tests -v`
- Gallery of every template: `.venv/bin/python -m itsnews gallery`, written
  to `output/gallery.html`
- Layout: `itsnews/` is the package (checker, renderer, templates),
  `agent/` holds the prompt and the catalog, `examples/` holds fictional
  sample articles with their storyboards, and `tools/` holds one-off
  data builders.
- Rendering must stay deterministic: no timestamps, randomness or network
  access in `itsnews/`.
- Pages must stay self-contained: inline CSS, no external fonts, scripts or
  images.
- To add a template, follow "Adding a template" in [agent/README.md](agent/README.md).

## Rules

- English for code, comments, docs and content.
- This is a public repository. Never commit credentials, `.env` files or
  personal data (see [README.md](README.md)).
- Sample articles must be fictional, say so in their first lines, and set
  `fictional: true` in their front matter.
- `output/` is generated and not committed.
