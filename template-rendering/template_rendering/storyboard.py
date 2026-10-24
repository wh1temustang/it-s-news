"""Load a storyboard and check it before anything is rendered.

A storyboard is the JSON an agent writes after reading an article: which
templates to use, in what order, filled with what. See
storyboard.schema.json for the shape and agent/prompt.md for how to write one.
Loading and checking are shared by every approach (itsnews_common.storyboard);
this module checks against this approach's templates.
"""
from __future__ import annotations

from itsnews_common import storyboard as common
from itsnews_common.article import Article
from itsnews_common.catalog import Template
from itsnews_common.storyboard import StoryboardError, load, parse

from .kit import KIT

__all__ = ["StoryboardError", "check", "load", "parse", "validate_storyboard"]


def validate_storyboard(storyboard: dict, templates: dict[str, Template]) -> list[str]:
    """Shape, template ids, each scene's data, and one question per scene."""
    return common.validate(storyboard, KIT.storyboard_schema(), templates)


def check(storyboard: dict, article: Article,
          templates: dict[str, Template] | None = None) -> list[str]:
    """Everything that must hold before rendering. Empty means ready."""
    return KIT.check(storyboard, article, templates)
