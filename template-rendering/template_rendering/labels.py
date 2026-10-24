"""The words a page adds around the storyboard: labels, credits, the colophon.

English by default. A host that publishes in another language passes its own
labels, as a dict or (from the command line) a JSON file with --labels. Any
key it leaves out falls back to English. `lang` sets the page's language.

    {"lang": "fr", "bottom_line": "L'essentiel", "topic.world": "Monde",
     "template.timeline": "Chronologie"}

Keys named `topic.<id>` label the topics; keys named `template.<id>` rename a
template's scenes, which otherwise show the title in its schema.json.

The page shell's words are shared by every approach (itsnews_common.labels);
the ones below are this approach's templates' own.
"""
from __future__ import annotations

from pathlib import Path

from itsnews_common import labels as common
from itsnews_common.labels import BRAND, LabelsError

__all__ = ["BRAND", "DEFAULTS", "Labels", "LabelsError", "load_labels"]

DEFAULTS: dict[str, str] = {
    **common.DEFAULTS,
    "timeline.now": "Now",
    "timeline.next": "Ahead",
    "comparison.vs": "vs",
    "map.credit": "Map data: Natural Earth",
    "trend.up": "up to",
    "trend.down": "down to",
    "trend.flat": "flat to",
}


class Labels(common.Labels):
    """Look up a label, escaped for HTML: labels("bottom_line")."""

    DEFAULTS = DEFAULTS


def load_labels(path: str | Path) -> Labels:
    return common.load_labels(path, Labels)
