# The storyboard workflow

Template rendering presents an article in three steps. An AI agent makes the
editorial choices, and plain code does everything that should come out the
same every time.

```
 article.md ──► agent ──► storyboard.json ──► check ──► render ──► page.html
                  ▲                             │
                  └── fix what check reports ◄──┘
```

| Step | Who | What happens |
|---|---|---|
| 1. Storyboard | AI agent | Reads the article, the [prompt](prompt.md) and the [catalog](catalog.md); picks the scenes and fills their data |
| 2. Check | `python -m template_rendering check` | Validates every field against the schemas, and every figure and quote against the article |
| 3. Render | `python -m template_rendering render` | Fills the templates and writes one self-contained HTML page |

## What's in this folder

| File | What it is |
|---|---|
| [prompt.md](prompt.md) | The agent's instructions: how to read an article, pick scenes, and fill them without inventing anything |
| [catalog.md](catalog.md) | Which template answers which reader question, what each needs, and when to skip it |

The template schemas live with the templates, in `template_rendering/templates/<id>/schema.json`.

## Design choices

- **Judgement and drawing are separate.** The agent decides *what* to show:
  which questions, which templates, which facts. The templates decide *how*
  it looks. The same storyboard always renders to the same bytes, so a
  template change can be reviewed by re-rendering old storyboards without
  calling the agent again.
- **The storyboard is the hand-off.** It's small, readable JSON. Each scene
  records the reader question it answers and, in `why`, the reason for the
  template, so a reviewer can follow the agent's choices.
- **Facts are checked, not trusted.** Every figure a reader will see must
  appear in the article, and every quote must match it word for word.
  `check` enforces both mechanically. The only exception is map
  coordinates, which are general knowledge.
- **Brevity is enforced by the schemas.** Character limits are the word
  budget. A storyboard that runs long fails the check, so pages stay
  scannable.
- **Any agent works.** Nothing here calls a model or needs an API key.
  `python -m template_rendering prompt` prints everything an agent needs in
  one block of text.

## Running it

With any LLM tool, generate the prompt, hand it to the model, and save the
JSON it returns. Run these from the `template-rendering/` folder:

```bash
python -m template_rendering prompt examples/night-train.md > prompt.txt
# give prompt.txt to the model, then save its reply as storyboard.json
python -m template_rendering check  examples/night-train.md storyboard.json
python -m template_rendering render examples/night-train.md storyboard.json -o output/night-train.html
```

With a coding agent working in this repo (Claude Code, for example), ask it
to present an article. [AGENTS.md](../AGENTS.md) tells it the steps.

If `check` reports problems, give the messages back to the agent. Each one
names the field, what is wrong, and what to do.

## Editions

An edition puts several checked stories on one page, grouped into sections,
with links to each section at the top. Each story looks as it does on its
own page. List the stories in a manifest and render it:

```bash
python -m template_rendering edition examples/edition.json -o output/edition.html
```

The manifest's shape is in `../common/itsnews_common/edition.schema.json`,
shared by every approach.

## Other languages

The storyboard is written in the article's language. The words the page adds
itself, such as "Bottom line", the topic labels and the footer, are English
by default. A labels file replaces any of them; `template_rendering/labels.py`
lists every key.

```bash
python -m template_rendering edition my-edition.json --labels labels.fr.json
```

## Using it as a library

A site or pipeline that publishes with it's news can call it from Python
instead of the command line. Pin a version, for example as a git submodule,
and install it with the shared code beside it, in one command:
`pip install ./common ./template-rendering`.

```python
from template_rendering import article, edition, storyboard
from template_rendering.labels import Labels

story = edition.Story(article.load("a.md"), storyboard.load("a.storyboard.json"),
                      extra='<aside class="my-feedback">…</aside>')
issue = edition.Edition("Morning edition", [edition.Section("world", "World", [story])])
problems = edition.check(issue)  # empty means ready
html = edition.render(issue, labels=Labels({"lang": "fr"}),
                      head="<style>…</style>", foot="<script>…</script>")
```

`extra`, `head` and `foot` are the host's own markup, inserted as is. it's
news itself adds no scripts, so anything interactive (a feedback form, say)
is the host's to write and keep safe. Its CSS can use the tokens in
`templates/base.css`, so it follows the page into dark mode.

Hosts that wrap every page in their own `<html>`, `<head>` and `<body>` pass
`document=False` to get the page without them. A host that lets readers pick
a theme sets `data-theme="light"` or `"dark"` on the root element, and the
page follows it instead of the system setting.

## Adding a template

1. Create `template_rendering/templates/<id>/` with:
   - `schema.json`: a `title`, an `x-icon`, a one-line `description`, and the
     fields with tight `maxLength` limits. Mark quoted text `"x-verbatim": true`
     and general-knowledge fields `"x-ungrounded": true`. Don't name a field
     `items`, `keys`, `values` or `get`, because Jinja reads `data.items` as
     the dict method.
   - `template.html.j2`: the markup for one scene. Its data is in `data`.
     Any word the template adds itself goes through `t("<key>")`, with the
     English default added to `DEFAULTS` in `template_rendering/labels.py`.
   - `style.css`: styles that use only the tokens in `templates/base.css`
     (`var(--accent)` and so on), so dark mode keeps working.
   - `example.json`: `{"question": …, "data": …}`, shown in the gallery.
2. If the template draws something that needs geometry, add a function to
   `template_rendering/visuals.py`.
3. Add a row to [catalog.md](catalog.md) and a note on when to use it.
4. Run `python -m template_rendering gallery` to look at it, and `python -m unittest` to
   check that the catalog, schema, example and markup agree.
