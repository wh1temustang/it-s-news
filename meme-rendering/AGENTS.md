# Meme rendering: notes for AI agents

The repo-wide rules in [../AGENTS.md](../AGENTS.md) apply here too. Run the
commands below from this folder.

## Presenting an article as memes

When asked to present an article as memes, or in a Reddit style:

1. Read [agent/prompt.md](agent/prompt.md) and [agent/catalog.md](agent/catalog.md)
   in full, then the schema of each format you're considering
   (`meme_rendering/templates/<id>/schema.json`). Don't work from memory.
2. Read the whole article, and set the mood before you pick any format.
3. Write the storyboard as `<article>.storyboard.json` next to the article,
   following the prompt.
4. Run `python -m meme_rendering check <article.md> <storyboard.json>` and
   fix every problem it reports. Repeat until it passes. Never change the
   article to make the check pass, and never set a serious story's mood to
   `light` to get a joke through.
5. Run `python -m meme_rendering render <article.md> <storyboard.json>`.
   The page goes to `output/<article>.html`.
6. Report the mood, which formats you chose and why, and anything the
   article couldn't support.

## Presenting several articles as one feed

Write a storyboard for each article as above, then list them in a manifest
(its shape is in `../common/itsnews_common/edition.schema.json`; see
`examples/edition.json`) and run
`python -m meme_rendering edition <manifest.json>`. It checks every
storyboard again and writes `output/<manifest>.html`. For a page in another
language, pass `--labels <file.json>` (see `meme_rendering/labels.py`).

## Working on the code

- Setup: `python3 -m venv .venv && .venv/bin/pip install -e ../common -e .`.
  The checker, the renderer and the command line are shared with the other
  approaches and live in [../common/](../common/AGENTS.md); this package holds
  the formats, their words (`labels.py`), the mood rules (`mood.py`) and the
  kit that ties them together (`kit.py`).
- Tests: `.venv/bin/python -m unittest discover -s tests -v`
- Gallery of every format: `.venv/bin/python -m meme_rendering gallery`,
  written to `output/gallery.html`
- The example pages (`examples/<name>.html` and `examples/edition.html`) are
  committed. After changing a format, the shell or an example, render them
  again with
  `.venv/bin/python -m meme_rendering render examples/<name>.md examples/<name>.storyboard.json -o examples/<name>.html`
  and
  `.venv/bin/python -m meme_rendering edition examples/edition.json -o examples/edition.html`.
  A test fails while they're stale.
- Every format's schema says `"x-joke": true` or `false`. Serious stories
  may use only the `false` ones, so keep at least a megathread, a thread and
  RemindMe straight.
- Formats are redrawn in HTML, CSS and emoji. Never embed a meme image, a
  real person's photo, Reddit's logo, a username or a vote count.
- Pages must stay deterministic and self-contained: no timestamps,
  randomness, network access, external fonts, scripts or images.
- Styles use the tokens in `templates/base.css` only. The `--meme-*` tokens
  keep their colours in dark mode, because memes are pictures; everything
  else follows the theme.
- Page text that isn't from the storyboard goes through `labels.py`, so
  other languages can replace it. Don't hard-code words in templates.
