# it's news

**Make news interesting.**

Today, news mostly comes in two shapes: long articles that are heavy on words,
or long videos you have to sit through. Both are tedious, and both ask for more
time than most readers have. **it's news** replaces the wall of words and the
long video with more creative presentation: timelines, info boards, maps,
charts and other visual formats that get the key facts across in seconds, not
minutes.

## Approaches

There is more than one way to make news quick to take in, so it's news tries
several. Each approach lives in its own folder, with its own README, setup
and tests.

| Approach | What it does |
|---|---|
| [Template rendering](template-rendering/) | An AI agent picks pre-built visual templates (timeline, info board, map, charts and more) for an article. Code checks every figure and quote against the article, then renders a self-contained page, or several stories as one edition. See [an example page](template-rendering/examples/night-train.html) and [an example edition](template-rendering/examples/edition.html). |

## Today's news, every morning

[daily-edition/](daily-edition/) is an Agent Skill that has an AI agent read
today's newsletters from your email (or search the web), write each story up
from them, and render them as one page with an approach. Claude publishes the page as an artifact, on a
schedule if you like; Muse Code and other agents write it to a file. The
folder explains how to run it and how to share the skill.

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

MIT. See [LICENSE](LICENSE). The map data in template rendering comes from
[Natural Earth](https://www.naturalearthdata.com/) and is in the public domain.
