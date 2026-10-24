"""The words a page adds around the storyboard: labels, captions, the colophon.

English by default, and replaceable like every approach's labels (see
itsnews_common.labels): pass a dict, or a JSON file with --labels. Topics
read as communities ("r/business"); a French page might use
{"lang": "fr", "topic.world": "r/monde", "bottom_line": "En bref"}.
"""
from __future__ import annotations

from pathlib import Path

from itsnews_common import labels as common
from itsnews_common.labels import BRAND, LabelsError

__all__ = ["BRAND", "DEFAULTS", "Labels", "LabelsError", "load_labels"]

DEFAULTS: dict[str, str] = {
    **common.DEFAULTS,
    "topic.world": "r/world",
    "topic.politics": "r/politics",
    "topic.business": "r/business",
    "topic.science": "r/science",
    "topic.tech": "r/tech",
    "topic.climate": "r/climate",
    "topic.health": "r/health",
    "topic.local": "r/local",
    "topic.culture": "r/culture",
    "topic.sports": "r/sports",
    "bottom_line": "TL;DR",
    "posted_by": "Posted by {brand}",
    "vote": "Vote",
    "serious": "Serious",
    "not_affiliated": "Meme formats redrawn in HTML. Not affiliated with Reddit.",
    "starter_pack.title": "The {subject} starter pack",
    "stonks.caption": "Stonks",
    "trend.up": "up",
    "trend.down": "down",
    "expanding_brain.level": "Level {n}",
    "nope_yep.nope": "Nope",
    "nope_yep.yep": "Yep",
    "distracted.summary": "{who} turns away from {old}, toward {new}.",
    "two_buttons.summary": "{who} has to pick: {left}, or {right}.",
    "thread.reply": "In response:",
    "remindme.command": "RemindMe!",
    "megathread.pinned": "Pinned megathread",
    "megathread.facts": "What we know",
    "megathread.updates": "Updates",
}


class Labels(common.Labels):
    """Look up a label, escaped for HTML: labels("bottom_line")."""

    DEFAULTS = DEFAULTS


def load_labels(path: str | Path) -> Labels:
    return common.load_labels(path, Labels)
