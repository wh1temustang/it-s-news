# Template rendering: notes for AI agents

The repo-wide rules in [../AGENTS.md](../AGENTS.md) apply here too. Run the
commands below from this folder.

## Presenting an article

When asked to present, storyboard or render a news article (`.md`):

1. Read [agent/prompt.md](agent/prompt.md) and [agent/catalog.md](agent/catalog.md)
   in full, then the schema of each template you're considering
   (`template_rendering/templates/<id>/schema.json`). Don't work from memory.
2. Read the whole article.
3. Write the storyboard as `<article>.storyboard.json` next to the article,
   following the prompt.
4. Run `python -m template_rendering check <article.md> <storyboard.json>` and
   fix every problem it reports. Repeat until it passes. Never change the
   article to make the check pass.
5. Run `python -m template_rendering render <article.md> <storyboard.json>`.
   The page goes to `output/<article>.html`.
6. Report which templates you chose and why, plus anything the article
   couldn't support.

## Presenting several articles as one edition

Write a storyboard for each article as above, then list them in a manifest
(see `template_rendering/edition.py` and `examples/edition.json`) and run
`python -m template_rendering edition <manifest.json>`. It checks every
storyboard again and writes `output/<manifest>.html`. For a page in another
language, pass `--labels <file.json>` (see `template_rendering/labels.py`).

## Working on the code

- Setup: `python3 -m venv .venv && .venv/bin/pip install -e .`
- Tests: `.venv/bin/python -m unittest discover -s tests -v`
- Gallery of every template: `.venv/bin/python -m template_rendering gallery`,
  written to `output/gallery.html`
- Layout: `template_rendering/` is the package (checker, renderer,
  templates), `agent/` holds the prompt and the catalog, `examples/` holds
  fictional sample articles with their storyboards and rendered pages, and
  `tools/` holds one-off data builders.
- The example pages (`examples/<name>.html`) are committed, an exception to
  the repo's "no generated output" rule. After changing a template, the
  renderer or an example, render them again with
  `.venv/bin/python -m template_rendering render examples/<name>.md examples/<name>.storyboard.json -o examples/<name>.html`,
  and the example edition with
  `.venv/bin/python -m template_rendering edition examples/edition.json -o examples/edition.html`.
  A test fails while they're stale.
- Rendering must stay deterministic: no timestamps, randomness or network
  access in `template_rendering/`.
- Pages must stay self-contained: inline CSS, no external fonts, scripts or
  images. The only markup it's news doesn't write itself is what a host
  passes to an edition (`Story.extra`, `head`, `foot`).
- Page text that isn't from the storyboard goes through `labels.py`, so
  other languages can replace it. Don't hard-code words in templates.
- To add a template, follow "Adding a template" in [agent/README.md](agent/README.md).
