# Meme rendering

One of the [it's news](../README.md) approaches: news for readers who'd
rather scroll Reddit. Each story reads as a post, and an AI agent tells it
with **meme formats** they already know: the distracted boyfriend for a
change of course, stonks for numbers that moved, two buttons for a dilemma,
the expanding brain for something that keeps growing. The jokes are in the
format, never in the facts: code checks every number and quote on the page
against the article.

```
 article.md ──► AI agent ──► storyboard.json ──► check ──► render ──► page.html
                                                (facts + mood)
```

- **Formats:** distracted, nope/yep, two buttons, stonks, expanding brain,
  starter pack and change my mind for light stories; a megathread, a comment
  thread of quotes and RemindMe dates for any story.
- **Serious stories stay serious.** Every storyboard sets a mood. A
  `serious` story gets a [Serious] flair and straight formats only, and the
  check refuses a joke format in one. An article that reports deaths,
  injuries, violence or a disaster is serious whatever the agent says.
- **Honest Reddit.** No usernames, vote counts or comments that nobody made.
  People appear under the names the article gives them, and the page says
  it isn't affiliated with Reddit.
- **The memes are redrawn, not downloaded.** Each format is HTML, CSS and
  emoji, so the page is one self-contained file that loads nothing from the
  network, needs no Reddit account or API key, and carries no one else's
  images.
- **An edition** puts several stories in one feed, grouped into sections,
  like a daily digest.

See [an example page](examples/self-checkout.html),
[a serious story](examples/river-flood.html) and
[an example edition](examples/edition.html).

## How it relates to template rendering

It's built the same way as [template rendering](../template-rendering/), on
the shared code in [../common/](../common/): the article reader, the schema
validator, the fact check, editions, labels in any language, the renderer
and the command line are all shared. This approach brings only its own
formats, page shell, words, agent prompt and mood rules.

## Quick start

Requires Python 3.10 or newer. Run these from this folder.

```bash
python3 -m venv .venv && .venv/bin/pip install -e ../common -e .
source .venv/bin/activate

# Render a sample article from its storyboard
python -m meme_rendering render examples/self-checkout.md examples/self-checkout.storyboard.json
open output/self-checkout.html

# See every format
python -m meme_rendering gallery && open output/gallery.html

# Present your own article: print the prompt for your AI agent...
python -m meme_rendering prompt my-article.md > prompt.txt
# ...save its reply as my-article.storyboard.json, then:
python -m meme_rendering check  my-article.md my-article.storyboard.json
python -m meme_rendering render my-article.md my-article.storyboard.json

# Put several checked stories in one feed
python -m meme_rendering edition examples/edition.json

# Run the tests
python -m unittest discover -s tests -v
```

With a coding agent working in this repo, ask it to "present this article as
memes". [AGENTS.md](AGENTS.md) tells it the steps.

## Using it as a library

```python
from itsnews_common import article, edition, storyboard
from meme_rendering.kit import KIT
from meme_rendering.labels import Labels

art, sb = article.load("a.md"), storyboard.load("a.storyboard.json")
problems = KIT.check(sb, art)  # empty means ready
html = KIT.render_page(sb, art, labels=Labels({"lang": "fr", "topic.world": "r/monde"}))
```

Editions work as in template rendering (`KIT.render_edition`, with the
host's `extra`, `head` and `foot`), and the page follows a host's
`data-theme="light"` or `"dark"` on the root element.

## Adding a format

Follow "Adding a template" in
[../template-rendering/agent/README.md](../template-rendering/agent/README.md),
with two additions: say in the schema whether the format is a joke
(`"x-joke": true` or `false`), and add it to the catalog's table and notes in
[agent/catalog.md](agent/catalog.md). Redraw the format in HTML and CSS;
never embed a meme image or a real person's photo.

The sample articles in [examples/](examples/) are fictional.
