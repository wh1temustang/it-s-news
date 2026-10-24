# Common

The code the [it's news](../README.md) approaches share. It isn't an
approach itself; approaches install it beside their own package.

```
 article.md ──► storyboard ──► check ──► render ──► page.html
   article.py   storyboard.py  schema.py   kit.py
                               grounding.py
```

| Module | What it does |
|---|---|
| `article.py` | Reads a news article in Markdown, with its front matter |
| `schema.py` | A small JSON Schema validator whose messages tell an agent what to fix |
| `grounding.py` | Checks that every number and quote a reader will see is in the article |
| `storyboard.py` | Loads an agent's storyboard and checks its shape and scenes |
| `catalog.py` | Finds an approach's templates, each a folder with a schema and markup |
| `labels.py` | The words a page adds itself, in English or any other language |
| `edition.py` | Several stories on one page: the manifest, the model and its checks |
| `kit.py` | A **template kit**: one approach's templates, words and hooks, and the deterministic renderer they share |
| `cli.py` | The command line every kit gets: `prompt`, `check`, `render`, `edition`, `gallery`, `templates` |
| `testing.py` | Tests every kit must pass, to mix into an approach's own tests |

## Template kits

Both [template rendering](../template-rendering/) and
[meme rendering](../meme-rendering/) are template kits: an AI agent picks
templates for an article, and shared code checks and renders its choice. A
kit brings its own templates, page shell, words and agent prompt, and hooks
into the shared code in one line:

```python
from itsnews_common.kit import Kit

KIT = Kit("meme_rendering", PACKAGE_DIR, labels=Labels,
          prepare=visuals.prepare, rules=mood.rules)
```

- `labels`: its Labels class, the shared words plus its templates' own.
- `prepare(template_id, data)`: turns a scene's checked data into what its
  template draws, such as chart geometry.
- `rules(storyboard, article, templates)`: checks of its own, run after the
  shared shape and grounding checks. Meme rendering uses it to keep jokes
  off serious stories.

[kit.py](itsnews_common/kit.py) describes the folder layout a kit needs. An
approach that isn't template-based can still use the lower layers on their
own, such as `article.py` and `grounding.py`.

## Setup and tests

Requires Python 3.10 or newer. Run these from this folder.

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

The tests run on a one-template fixture kit in [tests/fixture/](tests/fixture/).

An approach installs this package beside itself, in the same command, so
pip finds it here rather than on PyPI: `pip install -e ../common -e .`
