# The storyboard workflow

it's news presents an article in three steps. An AI agent makes the editorial
choices, and plain code does everything that should come out the same every
time.

```
 article.md ──► agent ──► storyboard.json ──► itsnews check ──► itsnews render ──► page.html
                  ▲                                │
                  └──── fix what check reports ◄───┘
```

| Step | Who | What happens |
|---|---|---|
| 1. Storyboard | AI agent | Reads the article, the [prompt](prompt.md) and the [catalog](catalog.md); picks the scenes and fills their data |
| 2. Check | `itsnews check` | Validates every field against the schemas, and every figure and quote against the article |
| 3. Render | `itsnews render` | Fills the templates and writes one self-contained HTML page |

## What's in this folder

| File | What it is |
|---|---|
| [prompt.md](prompt.md) | The agent's instructions: how to read an article, pick scenes, and fill them without inventing anything |
| [catalog.md](catalog.md) | Which template answers which reader question, what each needs, and when to skip it |

The template schemas live with the templates, in `itsnews/templates/<id>/schema.json`.

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
  `itsnews check` enforces both mechanically. The only exception is map
  coordinates, which are general knowledge.
- **Brevity is enforced by the schemas.** Character limits are the word
  budget. A storyboard that runs long fails the check, so pages stay
  scannable.
- **Any agent works.** Nothing here calls a model or needs an API key.
  `itsnews prompt` prints everything an agent needs in one block of text.

## Running it

With any LLM tool, generate the prompt, hand it to the model, and save the
JSON it returns:

```bash
python -m itsnews prompt examples/night-train.md > prompt.txt
# give prompt.txt to the model, then save its reply as storyboard.json
python -m itsnews check  examples/night-train.md storyboard.json
python -m itsnews render examples/night-train.md storyboard.json -o output/night-train.html
```

With a coding agent working in this repo (Claude Code, for example), ask it
to present an article. [AGENTS.md](../AGENTS.md) tells it the steps.

If `check` reports problems, give the messages back to the agent. Each one
names the field, what is wrong, and what to do.

## Adding a template

1. Create `itsnews/templates/<id>/` with:
   - `schema.json`: a `title`, an `x-icon`, a one-line `description`, and the
     fields with tight `maxLength` limits. Mark quoted text `"x-verbatim": true`
     and general-knowledge fields `"x-ungrounded": true`. Don't name a field
     `items`, `keys`, `values` or `get`, because Jinja reads `data.items` as
     the dict method.
   - `template.html.j2`: the markup for one scene. Its data is in `data`.
   - `style.css`: styles that use only the tokens in `templates/base.css`
     (`var(--accent)` and so on), so dark mode keeps working.
   - `example.json`: `{"question": …, "data": …}`, shown in the gallery.
2. If the template draws something that needs geometry, add a function to
   `itsnews/visuals.py`.
3. Add a row to [catalog.md](catalog.md) and a note on when to use it.
4. Run `python -m itsnews gallery` to look at it, and `python -m unittest` to
   check that the catalog, schema, example and markup agree.
