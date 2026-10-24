"""Meme rendering as a template kit: its formats, words, mood rules and drawing code.

The checking and rendering themselves are shared by every approach; see
itsnews_common.kit. A host renders with KIT directly:

    from itsnews_common import article, edition, storyboard
    from meme_rendering.kit import KIT

    problems = KIT.check(sb, art)          # empty means ready
    html = KIT.render_page(sb, art)
"""
from __future__ import annotations

from pathlib import Path

from itsnews_common.kit import Kit

from . import mood, visuals
from .labels import Labels

PACKAGE_DIR = Path(__file__).resolve().parent

KIT = Kit("meme_rendering", PACKAGE_DIR, labels=Labels, prepare=visuals.prepare,
          rules=mood.rules)
