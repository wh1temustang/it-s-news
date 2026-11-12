"""Several stories on one page: an edition.

An edition groups checked stories into sections, like a daily digest with
World, Business and Local news. Each story is an article and its storyboard.
How the page looks is up to the approach; this module holds what every
approach's edition shares: the manifest, the model and the checks.

From the command line, an edition is a JSON manifest (edition.schema.json):

    {
      "title": "Morning edition",
      "date": "March 14, 2026",
      "sections": [
        {"id": "travel", "title": "Travel", "icon": "🚆",
         "stories": [{"article": "night-train.md",
                      "storyboard": "night-train.storyboard.json"}]}
      ]
    }

A story may also name an `animated` page: a self-contained animated
explainer built for the same article (see the animated-explainer approach).
The edition keeps the story's template scenes as the skimmable version and
embeds the animation after them, so one edition can mix both: simple stories
as templates, a long story that unfolds as an animation. The explainer's
script is checked against the article like a storyboard (check_animated),
and a page that loads anything from the network is refused.

From Python, build an Edition directly. A host can then add its own markup
to each story (Story.extra) and to the page (Kit.render_edition's `head` and
`foot`), for example a feedback form. it's news never adds a script itself;
whatever a host adds is inserted as is, and keeping it safe is the host's job.

Element ids on the page: each section's own id, `story-<n>` for the n-th
story counting from the top, and `story-<n>-q<k>` for its k-th scene.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import article as article_mod
from . import grounding
from . import storyboard as storyboard_mod
from .schema import validate

PACKAGE_DIR = Path(__file__).resolve().parent
_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class EditionError(ValueError):
    """The manifest can't be loaded; `errors` holds one message per problem."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Story:
    article: article_mod.Article
    storyboard: dict
    # Host markup for the end of the story. Inserted as is, never escaped.
    extra: str = ""
    # The story's animated explainer page, when the manifest names one: the
    # whole self-contained HTML file, embedded after the template scenes by
    # kits whose edition template draws it. "" means templates only.
    animated: str = ""


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    stories: list[Story] = field(default_factory=list)
    icon: str = ""


@dataclass(frozen=True)
class Edition:
    title: str
    sections: list[Section] = field(default_factory=list)
    dek: str = ""
    date: str = ""
    footer: str = ""

    @property
    def stories(self) -> list[Story]:
        return [story for section in self.sections for story in section.stories]


def edition_schema() -> dict:
    return json.loads((PACKAGE_DIR / "edition.schema.json").read_text(encoding="utf-8"))


def _where(section_id: str, n: int, article_path: Path | str | None) -> str:
    name = f" ({Path(article_path).name})" if article_path else ""
    return f"{section_id}, story {n}{name}"


def load(path: str | Path) -> Edition:
    """Read a manifest and every article and storyboard it names."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise EditionError([f"{path}: {err}"]) from None
    errors = [f"{path.name}: {e}" for e in validate(data, edition_schema())]
    if errors:
        raise EditionError(errors)

    sections = []
    for entry in data["sections"]:
        stories = []
        for n, files in enumerate(entry["stories"], 1):
            where = _where(entry["id"], n, files["article"])
            try:
                article = article_mod.load(path.parent / files["article"])
                storyboard = storyboard_mod.load(path.parent / files["storyboard"])
            except OSError as err:
                errors.append(f"{where}: can't read {err.filename}")
                continue
            except storyboard_mod.StoryboardError as err:
                errors.append(f"{where}: {files['storyboard']}: {err}")
                continue
            animated = ""
            if files.get("animated"):
                try:
                    animated = (path.parent / files["animated"]).read_text(encoding="utf-8")
                except OSError as err:
                    errors.append(f"{where}: can't read {err.filename}")
                    continue
            stories.append(Story(article, storyboard, animated=animated))
        sections.append(Section(entry["id"], entry["title"], stories, entry.get("icon", "")))
    if errors:
        raise EditionError(errors)
    return Edition(data["title"], sections, data.get("dek", ""), data.get("date", ""),
                   data.get("footer", ""))


def check(edition: Edition,
          check_story: Callable[[dict, article_mod.Article], list[str]]) -> list[str]:
    """The edition's own problems, then each story's, as `check_story` finds them."""
    errors: list[str] = []
    if not edition.sections:
        errors.append("the edition has no sections")
    seen: set[str] = set()
    for section in edition.sections:
        if not _ID.match(section.id):
            errors.append(f"section {section.id!r}: use lowercase letters, digits and hyphens")
        elif section.id in seen:
            errors.append(f"section {section.id!r}: another section has the same id")
        seen.add(section.id)
        if not section.stories:
            errors.append(f"section {section.id!r} has no stories")
        for n, story in enumerate(section.stories, 1):
            where = _where(section.id, n, story.article.path)
            errors += [f"{where}: {e}" for e in check_story(story.storyboard, story.article)]
            if story.animated:
                errors += [f"{where}: {e}" for e in check_animated(story.animated, story.article)]
    return errors


# --- the animated explainer's script -------------------------------------
#
# An animated page keeps every word and figure in one JSON script,
# <script type="application/json" id="explainer">. That script gets the
# storyboard treatment: numbers a reader will see must appear in the
# article, and a quote beat's text must match the article word for word.
# What is not checked, because it is drawing, not news:
#
# - layout numbers: ranks, coordinates, axis scales, grid shapes, the
#   decimal hours a clock or race row is drawn from (the words beside them
#   state the figure and are checked);
# - a `math` beat's result, the number after "≈" or "=": like the animated
#   approach's own rules say, a ratio the article only implies belongs in
#   `math` with its working, and the operands are checked;
# - `why` (the agent's note to reviewers) and `labels` (the page's own
#   words), which readers never see as facts.

_SCRIPT = re.compile(r'<script[^>]*\bid="explainer"[^>]*>(.*?)</script>', re.S)
_ROLE = re.compile(r"\{[a-z]+:([^{}]*)\}")
_NETWORK = [
    (re.compile(r"<script[^>]+\bsrc\s*=", re.I), "a script"),
    (re.compile(r"<link[^>]+\bhref\s*=", re.I), "a linked file"),
    (re.compile(r"<(?:img|source|video|audio|iframe|embed|object)[^>]+\bsrc\s*=\s*[\"']https?:", re.I),
     "media"),
    (re.compile(r"url\(\s*[\"']?https?:", re.I), "a CSS url()"),
    (re.compile(r"@import", re.I), "a CSS @import"),
    (re.compile(r"\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon"), "a network call"),
]
_SKIP_KEYS = {"why", "labels", "lat", "lng", "rank", "max_pages", "max", "min",
              "block", "span", "upto", "hours", "start", "x", "y"}
_NUMBER_KEYS = {"amount", "count", "total", "done"}


def explainer_script(page: str) -> dict | None:
    """The animated page's JSON script, or None when it has none that parses."""
    match = _SCRIPT.search(page)
    if not match:
        return None
    try:
        script = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return script if isinstance(script, dict) else None


def check_animated(page: str, article: article_mod.Article) -> list[str]:
    """One message per problem with an animated page embedded in an edition."""
    errors: list[str] = []
    for pattern, what in _NETWORK:
        if pattern.search(page):
            errors.append(
                f"animated page: it loads {what} from the network. Animated pages "
                "must be self-contained: inline everything, like the "
                "animated-explainer example."
            )
    script = explainer_script(page)
    if script is None:
        errors.append(
            'animated page: no readable <script type="application/json" '
            'id="explainer"> script. Build the page from the animated-explainer '
            "example, with every word and figure in that script, so it can be "
            "checked against the article."
        )
        return errors

    source = grounding.Source(article)

    def number(value: float, path: str) -> None:
        if not source.has_number(value):
            errors.append(
                f"animated script {path}: {value:g} is not in the article. "
                "Show only numbers the article states, written the way it writes them."
            )

    def text(value: str, path: str, key: str) -> None:
        plain = grounding.plain(_ROLE.sub(r"\1", value))
        if key == "math":
            # The result is the article's numbers worked, not a new fact;
            # check the operands, which grounding's Source knows.
            plain = re.split(r"≈|=", plain, maxsplit=1)[0]
        for token in grounding.numbers_in(plain):
            number(float(token.replace(",", "")), path)

    def walk(value, key: str, path: str) -> None:
        if isinstance(value, dict):
            if value.get("do") == "quote" and isinstance(value.get("text"), str):
                if not source.has_quote(value["text"]):
                    errors.append(
                        f"animated script {path}.text: not found word for word in "
                        "the article. Copy the quote exactly; mark any cut with '...'."
                    )
            for k, v in value.items():
                if k not in _SKIP_KEYS:
                    walk(v, k, f"{path}.{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                if key == "points" and isinstance(v, list) and len(v) == 2 \
                        and isinstance(v[1], (int, float)) and not isinstance(v[1], bool):
                    number(v[1], f"{path}[{i}]")
                    walk(v[0], key, f"{path}[{i}][0]")
                else:
                    walk(v, key, f"{path}[{i}]")
        elif isinstance(value, str):
            text(value, path, key)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if key in _NUMBER_KEYS:
                number(value, path)

    walk(script, "", "$")
    return errors
