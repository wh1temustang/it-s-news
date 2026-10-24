"""Several stories on one page: an edition.

An edition groups checked stories into sections, like a daily digest with
World, Business and Local news. Each story is an article and its storyboard,
drawn as on its own page, and the page opens with a link to every section.
Like a single story, the page is one self-contained file.

The manifest and the model are shared by every approach; see
itsnews_common.edition for the manifest's shape, host markup (Story.extra,
`head`, `foot`) and the element ids on the page.
"""
from __future__ import annotations

from itsnews_common.edition import Edition, EditionError, Section, Story, edition_schema, load

from .kit import KIT

__all__ = ["Edition", "EditionError", "Section", "Story", "check", "edition_schema", "load",
           "render"]

check = KIT.check_edition
render = KIT.render_edition
