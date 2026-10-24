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
            stories.append(Story(article, storyboard))
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
    return errors
