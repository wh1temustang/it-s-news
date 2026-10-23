# it's news

**Make news interesting.**

Today, news mostly comes in two shapes: long articles that are heavy on words,
or long videos you have to sit through. Both are tedious, and both ask for more
time than most readers have. **it's news** replaces the wall of words and the
long video with more creative presentation: timelines, info boards, maps,
charts and other visual formats that get the key facts across in seconds, not
minutes.

## How it works

The first approach renders an article with **pre-built templates**: vivid,
but deterministic. An AI agent reads the article (`.md`) and the template
catalog, then decides which templates tell this story. Code checks the
agent's choices against the article and renders the page.

```
 article.md ──► AI agent ──► storyboard.json ──► itsnews check ──► itsnews render ──► page.html
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

More detail in [agent/README.md](agent/README.md).

## Quick start

Requires Python 3.10 or newer.

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
source .venv/bin/activate

# Render a sample article from its storyboard
python -m itsnews render examples/night-train.md examples/night-train.storyboard.json
open output/night-train.html

# See every template
python -m itsnews gallery && open output/gallery.html

# Present your own article: print the prompt for your AI agent...
python -m itsnews prompt my-article.md > prompt.txt
# ...save its reply as my-article.storyboard.json, then:
python -m itsnews check  my-article.md my-article.storyboard.json
python -m itsnews render my-article.md my-article.storyboard.json

# Run the tests
python -m unittest discover -s tests -v
```

The sample articles in [examples/](examples/) are fictional. Each comes with
its storyboard and the page rendered from it, for example
[examples/night-train.html](examples/night-train.html).

## Open source: no credentials, no private data

it's news is an open-source project. Everything committed here is public, and
git history keeps it public even after a file is deleted. **Never commit
credentials or anything that could violate someone's privacy**, including:

- API keys, access tokens, passwords, session cookies, private keys and
  certificates
- `.env` files or local config that holds secrets. Read secrets from
  environment variables, and if a config template helps, commit a
  `.env.example` with placeholder values only.
- Personal data: names, emails, phone numbers, addresses or anything else
  that identifies a private person, such as user data or reader feedback
- Your own private details, such as a work email in git commit metadata.
  GitHub's `noreply` commit email keeps your address out of the history.

If a secret is committed by accident, **revoke or rotate it right away**.
Rewriting history does not undo the leak, because clones and forks may
already have it.

## Languages

- **Human language:** English. It's the primary language for the news
  content, code, comments, docs, issues and pull requests.
- **Programming languages:** Python and Rust.

## License

MIT. See [LICENSE](LICENSE). Map data comes from
[Natural Earth](https://www.naturalearthdata.com/) and is in the public domain.
