"""Render a checked storyboard into one self-contained HTML page.

Deterministic by design: the same article and storyboard always give the
same bytes. No timestamps, no randomness, no network. CSS is inlined and
the page loads nothing from anywhere else, so it works offline and leaks
nothing about its readers.

Several stories on one page are an edition; see edition.py.
"""
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from . import visuals
from .article import Article
from .catalog import TEMPLATES_DIR, Template, load_templates
from .labels import BRAND, DEFAULTS, Labels

FICTIONAL_BANNER = DEFAULTS["fictional"]


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def story_view(env: Environment, templates: dict[str, Template], storyboard: dict,
               article: Article, t: Labels, anchor: str = "", first_index: int = 0) -> dict:
    """What story.html.j2 draws for one story.

    `anchor` prefixes the scenes' element ids and `first_index` numbers them,
    so that several stories can share a page without their ids colliding.
    """
    scenes = []
    for i, scene in enumerate(storyboard["scenes"]):
        template = templates[scene["template"]]
        data = visuals.prepare(template.id, scene["data"])
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


def stylesheet(templates: dict[str, Template], storyboards: list[dict], *extra: str) -> Markup:
    """Base styles, any extra sheets, then each template used, in catalog order, once."""
    used = {s["template"] for sb in storyboards for s in sb["scenes"]}
    css = (TEMPLATES_DIR / "base.css").read_text(encoding="utf-8")
    css += "".join((TEMPLATES_DIR / name).read_text(encoding="utf-8") for name in extra)
    css += "".join(t.css for t in templates.values() if t.id in used)
    return Markup(css)


def render_page(storyboard: dict, article: Article,
                templates: dict[str, Template] | None = None,
                banner: str | None = None, checked: bool = True,
                labels: Labels | None = None) -> str:
    """The page for a storyboard that has passed storyboard.check().

    `checked` says the storyboard was grounded against `article`; only then
    does the footer promise that every number comes from the article.
    """
    templates = templates if templates is not None else load_templates()
    t = labels or Labels()
    env = environment()
    if banner is None and article.fictional:
        banner = t("fictional")
    return env.get_template("page.html.j2").render(
        story=story_view(env, templates, storyboard, article, t),
        source=article.meta.get("source"),
        url=article.url,
        banner=banner,
        checked=checked,
        css=stylesheet(templates, [storyboard]),
        t=t,
        brand=BRAND,
    )


def render_gallery(templates: dict[str, Template] | None = None,
                   labels: Labels | None = None) -> str:
    """Every template filled with its example, for designing and reviewing templates."""
    templates = templates if templates is not None else load_templates()
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
    return render_page(storyboard, article, templates,
                       banner="Template gallery: every scene below uses made-up example data.",
                       checked=False, labels=labels)
