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

### Which stories get an animation

By default an edition is templates throughout. One story may also carry an
**animated explainer**, embedded in the same page after its template scenes:
the templates stay the skimmable version, the animation is the deep version.
The reader never has to choose in advance, and neither do you per story —
route by these rules unless the user says otherwise:

- **Templates only** for a simple story: one number, one quote, one result,
  or anything a reader takes in at a glance. Most stories are this.
- **Add an animation** when a story is long (roughly 500+ words) *and*
  unfolds: a process or mechanism in steps, a journey, a dated sequence, a
  build-up with a "but wait" in it — material a reader grasps better one
  idea at a time than all at once — and it supports 3–5 animated scenes
  whose every beat the article grounds.
- **At most one animated story per edition** — the deepest one. An edition
  is still a digest; five click-throughs would bury it.
- **Never animate grave news** (deaths, disasters, war, crime, illness):
  a click-through pace is the wrong register, whatever its length.
- If a story qualifies but the animated page can't be built or checked,
  ship the edition templates-only and say so. Never hold the edition for
  the animation.

To build one: follow [../animated-explainer/AGENTS.md](../animated-explainer/AGENTS.md)
to make the story's animated page from the example's engine (content goes
in the script, facts follow the same rules as a storyboard), save it beside
the article as `<article-stem>.animated.html`, and name it in the story's
manifest entry as `"animated": "<article-stem>.animated.html"`. The edition
check then verifies the script's numbers and quotes against the article and
refuses a page that loads anything from the network, exactly as it checks
storyboards.

## Working on the code

- Setup: `python3 -m venv .venv && .venv/bin/pip install -e ../common -e .`.
  The checker, the renderer and the command line are shared with the other
  approaches and live in [../common/](../common/AGENTS.md); this package holds
  the templates, their words (`labels.py`) and their drawing code
  (`visuals.py`, `geo.py`).
- Tests: `.venv/bin/python -m unittest discover -s tests -v`
- Gallery of every template: `.venv/bin/python -m template_rendering gallery`,
  written to `output/gallery.html`
- Layout: `template_rendering/` is the package (templates, the kit in
  `kit.py`, drawing code), `agent/` holds the prompt and the catalog,
  `examples/` holds fictional sample articles with their storyboards and
  rendered pages, and `tools/` holds one-off data builders.
- The example pages (`examples/<name>.html`) are committed, an exception to
  the repo's "no generated output" rule. After changing a template, the
  renderer or an example, render them again with
  `.venv/bin/python -m template_rendering render examples/<name>.md examples/<name>.storyboard.json -o examples/<name>.html`,
  and the example edition with
  `.venv/bin/python -m template_rendering edition examples/edition.json -o examples/edition.html`.
  A test fails while they're stale.
- Rendering must stay deterministic: no timestamps, randomness or network
  access in `template_rendering/` or `../common/`.
- Pages must stay self-contained: inline CSS, no external fonts, scripts or
  images. The only markup it's news doesn't write itself is what a host
  passes to an edition (`Story.extra`, `head`, `foot`).
- Page text that isn't from the storyboard goes through `labels.py`, so
  other languages can replace it. Don't hard-code words in templates.
- To add a template, follow "Adding a template" in [agent/README.md](agent/README.md).
