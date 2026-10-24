"""The words a page adds around the storyboard: labels, credits, the colophon.

English by default. A host that publishes in another language passes its own
labels, as a dict or (from the command line) a JSON file with --labels. Any
key it leaves out falls back to English. `lang` sets the page's language.

    {"lang": "fr", "bottom_line": "L'essentiel", "topic.world": "Monde",
     "template.timeline": "Chronologie"}

Keys named `topic.<id>` label the topics; keys named `template.<id>` rename a
template's scenes, which otherwise show the title in its schema.json.

DEFAULTS below holds the words every page shell uses. Each approach
subclasses Labels and adds the words its own templates need:

    class Labels(common.Labels):
        DEFAULTS = {**common.DEFAULTS, "timeline.now": "Now"}
"""
from __future__ import annotations

import json
from pathlib import Path

from markupsafe import Markup, escape

BRAND = Markup("<b>it's news</b>")

DEFAULTS: dict[str, str] = {
    "lang": "en",
    "topic.world": "World",
    "topic.politics": "Politics",
    "topic.business": "Business",
    "topic.science": "Science",
    "topic.tech": "Tech",
    "topic.climate": "Climate",
    "topic.health": "Health",
    "topic.local": "Local",
    "topic.culture": "Culture",
    "topic.sports": "Sports",
    "bottom_line": "Bottom line",
    "sources": "Sources",
    "label_sep": ": ",
    "list_sep": ", ",
    "read_more": "Read the full article",
    "read_more_at": "Read the full article at {source}",
    "presented_by": "Presented by {brand}.",
    "checked": "Every figure and quote in this story was checked against the article.",
    "checked_edition": "Every figure and quote in these stories was checked against their articles.",
    "fictional": "Fictional sample: this is not real news.",
    "sections": "Sections",
}

_OPEN_PREFIXES = ("topic.", "template.")


class LabelsError(ValueError):
    pass


class Labels:
    """Look up a label, escaped for HTML: labels("bottom_line")."""

    DEFAULTS: dict[str, str] = DEFAULTS

    def __init__(self, overrides: dict | None = None):
        overrides = overrides or {}
        if not isinstance(overrides, dict):
            raise LabelsError("labels must be a JSON object of strings")
        for key, value in overrides.items():
            if key not in self.DEFAULTS and not key.startswith(_OPEN_PREFIXES):
                raise LabelsError(
                    f"unknown label {key!r}. Known labels: {', '.join(self.DEFAULTS)}"
                )
            if not isinstance(value, str):
                raise LabelsError(f"label {key!r} must be a string")
        self._text = {**self.DEFAULTS, **overrides}

    @property
    def lang(self) -> str:
        return self._text["lang"]

    def __call__(self, key: str, **values) -> Markup:
        """The label, escaped; `values` fill its {placeholders} and are escaped too."""
        text = escape(self._text[key])
        return text.format(**values) if values else text

    def topic(self, topic_id: str) -> str:
        return self._text.get(f"topic.{topic_id}", topic_id)

    def template(self, template) -> str:
        return self._text.get(f"template.{template.id}", template.name)


def load_labels(path: str | Path, labels: type[Labels] = Labels) -> Labels:
    """Read a labels file into `labels`, the approach's own Labels class."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise LabelsError(f"{path}: {err}") from None
    return labels(data)
