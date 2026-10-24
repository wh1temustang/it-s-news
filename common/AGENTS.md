# Common: notes for AI agents

The repo-wide rules in [../AGENTS.md](../AGENTS.md) apply here too. Run the
commands below from this folder.

This folder is shared code, not an approach: every approach that depends on
it changes when it does. [README.md](README.md) lists the modules.

## Working on the code

- Setup: `python3 -m venv .venv && .venv/bin/pip install -e .`
- Tests: `.venv/bin/python -m unittest discover -s tests -v`
- After any change here, run the tests of every approach that installs
  `itsnews-common` too (each one's AGENTS.md says how). Their committed
  example pages must still match a fresh render; a byte that changes there
  is a change readers see.
- Only code that two or more approaches need belongs here. Anything about
  one approach's look, words or rules stays in that approach, and reaches
  the shared code through its `Kit` (`labels`, `prepare`, `rules`).
- Keep the public names stable. Approaches re-export some of them (for
  example `template_rendering.edition.Story`), and hosts import those.
- Rendering must stay deterministic: no timestamps, randomness or network
  access. Pages must stay self-contained.
- Messages from `schema.py`, `grounding.py` and `storyboard.py` are read by
  the agent that wrote the storyboard: name the field, what is wrong and
  what to do.
- Standard library and Jinja2 only.
