"""Template rendering as a template kit: its templates, words and drawing code.

The checking and rendering themselves are shared by every approach; see
itsnews_common.kit.
"""
from __future__ import annotations

from pathlib import Path

from itsnews_common.kit import Kit

from . import visuals
from .labels import Labels

PACKAGE_DIR = Path(__file__).resolve().parent

KIT = Kit("template_rendering", PACKAGE_DIR, labels=Labels, prepare=visuals.prepare)
