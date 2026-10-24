"""Command line: python -m meme_rendering <command> ...

    prompt   ARTICLE                 print the full instructions for the agent
    check    ARTICLE STORYBOARD      validate a storyboard against its article
    render   ARTICLE STORYBOARD      check, then write the HTML page
    edition  MANIFEST                check, then write several stories as one page
    gallery                          render every format's example
    templates                        list the formats

render, edition and gallery take --labels FILE to write the page's own
words in another language (see labels.py). The commands are shared by every
approach; see itsnews_common.cli.
"""
from __future__ import annotations

from itsnews_common import cli

from .kit import KIT


def main(argv: list[str] | None = None) -> int:
    return cli.main(KIT, argv,
                    "Turn a news article into a Reddit-style post of memes an agent picks.")
