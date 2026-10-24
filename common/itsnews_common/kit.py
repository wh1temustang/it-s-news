"""A template kit: what makes one approach's pages look and read its way.

An approach that presents articles with templates an agent picks is a kit.
Its package holds:

    <package>/
      storyboard.schema.json   the storyboard's shape (see storyboard.py)
      templates/
        base.css               design tokens and the page shell's styles
        page.html.j2           one story on its own page
        edition.html.j2        several stories on one page
        edition.css            styles that only editions need
        <id>/                  one template each (see catalog.py)

and beside the package, in a clone of the repository:

    agent/prompt.md, agent/catalog.md   what the agent reads before it writes a storyboard

A kit adds three hooks of its own: `labels`, its Labels class with the
words its templates add (labels.py); `prepare`, which turns a scene's
checked data into what its template draws; and `rules`, checks of its own
that run after the shared shape and grounding checks.

Rendering is deterministic by design: the same article and storyboard
always give the same bytes. No timestamps, no randomness, no network. CSS is
inlined and the page loads nothing from anywhere else, so it works offline
and leaks nothing about its readers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from . import edition as edition_mod
from . import storyboard as storyboard_mod
from .article import Article
from .catalog import Template, load_templates
from .labels import BRAND, Labels


def _as_is(template_id: str, data: dict) -> dict:
    return dict(data)


def _no_rules(storyboard: dict, article: Article, templates: dict[str, Template]) -> list[str]:
    return []


@dataclass(frozen=True)
class Kit:
    name: str
    package_dir: Path
    labels: type[Labels] = Labels
    prepare: Callable[[str, dict], dict] = _as_is
    rules: Callable[[dict, Article, dict[str, Template]], list[str]] = _no_rules

    @property
    def templates_dir(self) -> Path:
        return self.package_dir / "templates"

    @property
    def agent_dir(self) -> Path:
        """agent/ sits beside the package, so it only exists in a clone."""
        return self.package_dir.parent / "agent"

    def load_templates(self) -> dict[str, Template]:
        return load_templates(self.templates_dir)

    def storyboard_schema(self) -> dict:
        path = self.package_dir / "storyboard.schema.json"
        return json.loads(path.read_text(encoding="utf-8"))

    # --- checking ---

    def check(self, storyboard: dict, article: Article,
              templates: dict[str, Template] | None = None) -> list[str]:
        """Everything that must hold before rendering. Empty means ready."""
        templates = templates if templates is not None else self.load_templates()
        return (storyboard_mod.check(storyboard, article, self.storyboard_schema(), templates)
                + self.rules(storyboard, article, templates))

    def check_edition(self, edition: edition_mod.Edition,
                      templates: dict[str, Template] | None = None) -> list[str]:
        """Everything that must hold before rendering, for the edition and every story."""
        templates = templates if templates is not None else self.load_templates()
        return edition_mod.check(edition, lambda sb, a: self.check(sb, a, templates))

    # --- rendering ---

    def environment(self) -> Environment:
        return Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def story_view(self, env: Environment, templates: dict[str, Template], storyboard: dict,
                   article: Article, t: Labels, anchor: str = "", first_index: int = 0) -> dict:
        """What story.html.j2 draws for one story.

        `anchor` prefixes the scenes' element ids and `first_index` numbers them,
        so that several stories can share a page without their ids colliding.
        """
        scenes = []
        for i, scene in enumerate(storyboard["scenes"]):
            template = templates[scene["template"]]
            data = self.prepare(template.id, scene["data"])
            html = env.get_template(template.markup).render(data=data, index=first_index + i, t=t)
            scenes.append({
                "id": template.id,
                "name": t.template(template),
                "icon": template.icon,
                "question": scene["question"],
                "anchor": f"{anchor}q{i + 1}",
                "html": Markup(html),
            })

        # `sources` credits several outlets; a lone `source` keeps the plain byline.
        credits = article.sources
        if not credits and article.meta.get("source"):
            credits = [(article.meta["source"], article.url)]
        headline = storyboard["headline"]
        return {
            "headline": headline,
            "topic_label": t.topic(headline["topic"]),
            "scenes": scenes,
            "bottom_line": storyboard.get("bottom_line"),
            "credits": credits,
            "credits_labelled": bool(article.sources),
            "published": article.meta.get("published"),
        }

    def stylesheet(self, templates: dict[str, Template], storyboards: list[dict],
                   *extra: str) -> Markup:
        """Base styles, any extra sheets, then each template used, in catalog order, once."""
        used = {s["template"] for sb in storyboards for s in sb["scenes"]}
        css = (self.templates_dir / "base.css").read_text(encoding="utf-8")
        css += "".join((self.templates_dir / name).read_text(encoding="utf-8") for name in extra)
        css += "".join(t.css for t in templates.values() if t.id in used)
        return Markup(css)

    def render_page(self, storyboard: dict, article: Article,
                    templates: dict[str, Template] | None = None,
                    banner: str | None = None, checked: bool = True,
                    labels: Labels | None = None) -> str:
        """The page for a storyboard that has passed check().

        `checked` says the storyboard was grounded against `article`; only then
        does the footer promise that every number comes from the article.
        """
        templates = templates if templates is not None else self.load_templates()
        t = labels or self.labels()
        env = self.environment()
        if banner is None and article.fictional:
            banner = t("fictional")
        return env.get_template("page.html.j2").render(
            story=self.story_view(env, templates, storyboard, article, t),
            source=article.meta.get("source"),
            url=article.url,
            banner=banner,
            checked=checked,
            css=self.stylesheet(templates, [storyboard]),
            t=t,
            brand=BRAND,
        )

    def render_gallery(self, templates: dict[str, Template] | None = None,
                       labels: Labels | None = None) -> str:
        """Every template filled with its example, for designing and reviewing templates."""
        templates = templates if templates is not None else self.load_templates()
        storyboard = {
            "headline": {
                "title": "Template gallery",
                "dek": "Every template, filled with its example data.",
                "topic": "tech",
            },
            "scenes": [
                {"template": t.id, "question": t.example["question"], "data": t.example["data"]}
                for t in templates.values()
            ],
        }
        article = Article(body="", meta={"source": "Example data from each template's example.json"})
        return self.render_page(storyboard, article, templates,
                                banner="Template gallery: every scene below uses made-up example data.",
                                checked=False, labels=labels)

    def render_edition(self, edition: edition_mod.Edition,
                       templates: dict[str, Template] | None = None,
                       labels: Labels | None = None, head: str = "", foot: str = "",
                       document: bool = True) -> str:
        """The page for an edition that has passed check_edition().

        `head` goes after the page's styles and `foot` at the very end, both
        inserted as is, like each story's `extra`. With `document=False` the
        page has no <!doctype>, <html>, <head> or <body> of its own, for hosts
        that wrap every page in theirs.
        """
        templates = templates if templates is not None else self.load_templates()
        t = labels or self.labels()
        env = self.environment()
        sections, n, index = [], 0, 0
        for section in edition.sections:
            stories = []
            for story in section.stories:
                n += 1
                anchor = f"story-{n}"
                view = self.story_view(env, templates, story.storyboard, story.article, t,
                                       anchor=f"{anchor}-", first_index=index)
                index += len(view["scenes"])
                stories.append({**view, "anchor": anchor, "fictional": story.article.fictional,
                                "extra": Markup(story.extra)})
            sections.append({"id": section.id, "title": section.title, "icon": section.icon,
                             "stories": stories})

        return env.get_template("edition.html.j2").render(
            edition=edition,
            sections=sections,
            css=self.stylesheet(templates, [s.storyboard for s in edition.stories], "edition.css"),
            head=Markup(head),
            foot=Markup(foot),
            document=document,
            t=t,
            brand=BRAND,
        )

    # --- the agent's instructions ---

    def build_prompt(self, article_path: Path) -> str:
        """The agent's instructions, the catalog, every schema, then the article."""
        templates = self.load_templates()
        parts = [
            (self.agent_dir / "prompt.md").read_text(encoding="utf-8").strip(),
            (self.agent_dir / "catalog.md").read_text(encoding="utf-8").strip(),
            "# Schemas\n\nThe storyboard:\n\n```json\n"
            + json.dumps(self.storyboard_schema(), indent=2, ensure_ascii=False)
            + "\n```",
        ]
        for template in templates.values():
            parts.append(
                f"Template `{template.id}` (the scene's `data`):\n\n```json\n"
                + json.dumps(template.schema, indent=2, ensure_ascii=False)
                + "\n```"
            )
        text = Path(article_path).read_text(encoding="utf-8").strip()
        parts.append(f"# The article\n\nFile: `{Path(article_path).name}`\n\n````markdown\n{text}\n````")
        return "\n\n".join(parts) + "\n"
