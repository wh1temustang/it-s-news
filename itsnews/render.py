"""Render a checked storyboard into one self-contained HTML page.

Deterministic by design: the same article and storyboard always give the
same bytes. No timestamps, no randomness, no network. CSS is inlined and
the page loads nothing from anywhere else, so it works offline and leaks
nothing about its readers.
"""
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from . import visuals
from .article import Article
from .catalog import TEMPLATES_DIR, Template, load_templates

TOPICS = {
    "world": "World",
    "politics": "Politics",
    "business": "Business",
    "science": "Science",
    "tech": "Tech",
    "climate": "Climate",
    "health": "Health",
    "local": "Local",
    "culture": "Culture",
    "sports": "Sports",
}

FICTIONAL_BANNER = "Fictional sample: this is not real news."


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def _scene(env: Environment, template: Template, scene: dict, index: int) -> dict:
    data = visuals.prepare(template.id, scene["data"])
    html = env.get_template(template.markup).render(data=data, index=index)
    return {
        "id": template.id,
        "name": template.name,
        "icon": template.icon,
        "question": scene["question"],
        "html": Markup(html),
    }


def render_page(storyboard: dict, article: Article,
                templates: dict[str, Template] | None = None,
                banner: str | None = None, checked: bool = True) -> str:
    """The page for a storyboard that has passed storyboard.check().

    `checked` says the storyboard was grounded against `article`; only then
    does the footer promise that every number comes from the article.
    """
    templates = templates if templates is not None else load_templates()
    env = _environment()
    scenes = [
        _scene(env, templates[s["template"]], s, i)
        for i, s in enumerate(storyboard["scenes"])
    ]
    # Base styles, then each template used, in catalog order, once.
    used = {s["template"] for s in storyboard["scenes"]}
    css = (TEMPLATES_DIR / "base.css").read_text(encoding="utf-8")
    css += "".join(t.css for t in templates.values() if t.id in used)

    if banner is None and article.fictional:
        banner = FICTIONAL_BANNER
    headline = storyboard["headline"]
    return env.get_template("page.html.j2").render(
        headline=headline,
        topic_label=TOPICS[headline["topic"]],
        scenes=scenes,
        bottom_line=storyboard.get("bottom_line"),
        source=article.meta.get("source"),
        published=article.meta.get("published"),
        url=article.url,
        banner=banner,
        checked=checked,
        css=Markup(css),
    )


def render_gallery(templates: dict[str, Template] | None = None) -> str:
    """Every template filled with its example, for designing and reviewing templates."""
    templates = templates if templates is not None else load_templates()
    storyboard = {
        "headline": {
            "title": "Template gallery",
            "dek": "Every it's news template, filled with its example data.",
            "topic": "tech",
        },
        "scenes": [
            {"template": t.id, "question": t.example["question"], "data": t.example["data"]}
            for t in templates.values()
        ],
    }
    article = Article(body="", meta={"source": "Example data from each template's example.json"})
    return render_page(storyboard, article, templates,
                       banner="Template gallery: every scene below uses made-up example data.",
                       checked=False)
