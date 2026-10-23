# Template rendering

One of the [it's news](../README.md) approaches: render an article with
**pre-built templates**, vivid but deterministic. An AI agent reads the
article (`.md`) and the template catalog, then decides which templates tell
this story. Code checks the agent's choices against the article and renders
the page.

```
 article.md ──► AI agent ──► storyboard.json ──► check ──► render ──► page.html
```

- **Templates:** timeline, info board, map, big number, bar chart, line
  chart, comparison, cause and effect, and quote.
- **The agent** answers one question per scene ("Where does it run?", "What
  happens next?") and picks the template that answers it fastest. It follows
  [agent/prompt.md](agent/prompt.md) and [agent/catalog.md](agent/catalog.md).
- **The check** rejects any figure or quote that isn't in the article, and
  any text over its template's word budget.
- **The page** is one self-contained HTML file, with light and dark themes,
  that loads nothing from the network.

- **An edition** puts several checked stories on one page, grouped into
  sections, for a daily digest or a newsletter.
- **Any language:** the page's own words (labels, credits, the footer) come
  in English and can be replaced with a labels file.

More detail in [agent/README.md](agent/README.md).

## Quick start

Requires Python 3.10 or newer. Run these from this folder.

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
source .venv/bin/activate

# Render a sample article from its storyboard
python -m template_rendering render examples/night-train.md examples/night-train.storyboard.json
open output/night-train.html

# See every template
python -m template_rendering gallery && open output/gallery.html

# Present your own article: print the prompt for your AI agent...
python -m template_rendering prompt my-article.md > prompt.txt
# ...save its reply as my-article.storyboard.json, then:
python -m template_rendering check  my-article.md my-article.storyboard.json
python -m template_rendering render my-article.md my-article.storyboard.json

# Put several checked stories on one page
python -m template_rendering edition examples/edition.json
open output/edition.html

# Run the tests
python -m unittest discover -s tests -v
```

The sample articles in [examples/](examples/) are fictional. Each comes with
its storyboard and the page rendered from it, for example
[examples/night-train.html](examples/night-train.html).
[examples/edition.html](examples/edition.html) shows both as one edition.

Map data comes from [Natural Earth](https://www.naturalearthdata.com/) and is
in the public domain.
