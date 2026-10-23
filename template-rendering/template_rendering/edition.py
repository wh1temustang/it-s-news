"""Several stories on one page: an edition.

An edition groups checked stories into sections, like a daily digest with
World, Business and Local news. Each story is an article and its storyboard,
drawn as on its own page, and the page opens with a link to every section.
Like a single story, the page is one self-contained file.

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
to each story (Story.extra) and to the page (render's `head` and `foot`),
for example a feedback form. it's news never adds a script itself; whatever
a host adds is inserted as is, and keeping it safe is the host's job.

Element ids on the page: each section's own id, `story-<n>` for the n-th
story counting from the top, and `story-<n>-q<k>` for its k-th scene.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from markupsafe import Markup

from . import article as article_mod
from . import storyboard as storyboard_mod
from .catalog import PACKAGE_DIR, Template, load_templates
from .labels import BRAND, Labels
from .render import environment, story_view, stylesheet
from .schema import validate

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


def check(edition: Edition, templates: dict[str, Template] | None = None) -> list[str]:
    """Everything that must hold before rendering, for the edition and every story."""
    templates = templates if templates is not None else load_templates()
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
            errors += [f"{where}: {e}"
                       for e in storyboard_mod.check(story.storyboard, story.article, templates)]
    return errors


def render(edition: Edition, templates: dict[str, Template] | None = None,
           labels: Labels | None = None, head: str = "", foot: str = "",
           document: bool = True) -> str:
    """The page for an edition that has passed check().

    `head` goes after the page's styles and `foot` at the very end, both
    inserted as is, like each story's `extra`. With `document=False` the
    page has no <!doctype>, <html>, <head> or <body> of its own, for hosts
    that wrap every page in theirs.
    """
    templates = templates if templates is not None else load_templates()
    t = labels or Labels()
    env = environment()
    sections, n, index = [], 0, 0
    for section in edition.sections:
        stories = []
        for story in section.stories:
            n += 1
            anchor = f"story-{n}"
            view = story_view(env, templates, story.storyboard, story.article, t,
                              anchor=f"{anchor}-", first_index=index)
            index += len(view["scenes"])
            stories.append({**view, "anchor": anchor, "fictional": story.article.fictional,
                            "extra": Markup(story.extra)})
        sections.append({"id": section.id, "title": section.title, "icon": section.icon,
                         "stories": stories})

    return env.get_template("edition.html.j2").render(
        edition=edition,
        sections=sections,
        css=stylesheet(templates, [s.storyboard for s in edition.stories], "edition.css"),
        head=Markup(head),
        foot=Markup(foot),
        document=document,
        t=t,
        brand=BRAND,
    )
