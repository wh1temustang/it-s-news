# it's news

**Make news interesting.**

Today, news mostly comes in two shapes: long articles that are heavy on words,
or long videos you have to sit through. Both are tedious, and both ask for more
time than most readers have. **it's news** replaces the wall of words and the
long video with more creative presentation: timelines, info boards, maps,
charts and other visual formats that get the key facts across in seconds, not
minutes.

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

MIT. See [LICENSE](LICENSE).
