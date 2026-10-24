"""Render a checked storyboard into one self-contained HTML page.

Deterministic by design: the same article and storyboard always give the
same bytes. No timestamps, no randomness, no network. The renderer is shared
by every approach (itsnews_common.kit); this approach brings the templates,
the words and the drawing code.

Several stories on one page are an edition; see edition.py.
"""
from __future__ import annotations

from .kit import KIT
from .labels import DEFAULTS

FICTIONAL_BANNER = DEFAULTS["fictional"]

environment = KIT.environment
story_view = KIT.story_view
stylesheet = KIT.stylesheet
render_page = KIT.render_page
render_gallery = KIT.render_gallery
