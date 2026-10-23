"""Command line: python -m template_rendering <command> ...

    prompt   ARTICLE                 print the full instructions for the agent
    check    ARTICLE STORYBOARD      validate a storyboard against its article
    render   ARTICLE STORYBOARD      check, then write the HTML page
    edition  MANIFEST                check, then write several stories as one page
    gallery                          render every template's example
    templates                        list the templates

render, edition and gallery take --labels FILE to write the page's own
words in another language (see labels.py).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import article as article_mod
from . import edition as edition_mod
from . import storyboard as storyboard_mod
from .catalog import PACKAGE_DIR, load_templates, storyboard_schema
from .labels import Labels, LabelsError, load_labels
from .render import render_gallery, render_page

REPO_DIR = PACKAGE_DIR.parent
AGENT_DIR = REPO_DIR / "agent"


def build_prompt(article_path: Path) -> str:
    """The agent's instructions, the catalog, every schema, then the article."""
    templates = load_templates()
    parts = [
        (AGENT_DIR / "prompt.md").read_text(encoding="utf-8").strip(),
        (AGENT_DIR / "catalog.md").read_text(encoding="utf-8").strip(),
        "# Schemas\n\nThe storyboard:\n\n```json\n"
        + json.dumps(storyboard_schema(), indent=2, ensure_ascii=False)
        + "\n```",
    ]
    for template in templates.values():
        parts.append(
            f"Template `{template.id}` (the scene's `data`):\n\n```json\n"
            + json.dumps(template.schema, indent=2, ensure_ascii=False)
            + "\n```"
        )
    text = article_path.read_text(encoding="utf-8").strip()
    parts.append(f"# The article\n\nFile: `{article_path.name}`\n\n````markdown\n{text}\n````")
    return "\n\n".join(parts) + "\n"


def _load(article_path: str, storyboard_path: str):
    article = article_mod.load(article_path)
    try:
        storyboard = storyboard_mod.load(storyboard_path)
    except storyboard_mod.StoryboardError as err:
        return article, None, [f"{storyboard_path}: {err}"]
    return article, storyboard, storyboard_mod.check(storyboard, article)


def _report(errors: list[str], fix: str = "Fix the storyboard and run check again.") -> None:
    for error in errors:
        print(f"✗ {error}", file=sys.stderr)
    print(f"\n{len(errors)} problem(s). {fix}", file=sys.stderr)


def _labels(args) -> Labels:
    return load_labels(args.labels) if args.labels else Labels()


def _write(out: Path, html: str) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"✓ wrote {out}")
    return 0


def cmd_prompt(args) -> int:
    if not (AGENT_DIR / "prompt.md").is_file():
        # agent/ sits beside the package, so it only exists in a clone.
        print("✗ agent/prompt.md not found. Run this from a clone of the repository "
              "(pip install -e .).", file=sys.stderr)
        return 1
    sys.stdout.write(build_prompt(Path(args.article)))
    return 0


def cmd_check(args) -> int:
    _, storyboard, errors = _load(args.article, args.storyboard)
    if errors:
        _report(errors)
        return 1
    scenes = ", ".join(s["template"] for s in storyboard["scenes"])
    print(f"✓ storyboard is ready to render ({scenes})")
    return 0


def cmd_render(args) -> int:
    labels = _labels(args)
    article, storyboard, errors = _load(args.article, args.storyboard)
    if errors:
        _report(errors)
        return 1
    out = Path(args.output) if args.output else Path("output") / (
        Path(args.article).stem + ".html"
    )
    return _write(out, render_page(storyboard, article, labels=labels))


def cmd_edition(args) -> int:
    labels = _labels(args)
    try:
        edition = edition_mod.load(args.manifest)
    except edition_mod.EditionError as err:
        _report(err.errors, "Fix the manifest and run edition again.")
        return 1
    errors = edition_mod.check(edition)
    if errors:
        _report(errors, "Fix the storyboards and run edition again.")
        return 1
    out = Path(args.output) if args.output else Path("output") / (
        Path(args.manifest).stem + ".html"
    )
    return _write(out, edition_mod.render(edition, labels=labels))


def cmd_gallery(args) -> int:
    return _write(Path(args.output), render_gallery(labels=_labels(args)))


def cmd_templates(args) -> int:
    for template in load_templates().values():
        print(f"{template.icon}  {template.id:<14} {template.schema.get('description', '')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="template_rendering",
        description="Turn a news article into a visual page, using templates an agent picks.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prompt", help="print the full instructions for the agent")
    p.add_argument("article", help="the news article (.md)")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("check", help="validate a storyboard against its article")
    p.add_argument("article")
    p.add_argument("storyboard", help="the agent's storyboard (.json)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("render", help="check, then write the HTML page")
    p.add_argument("article")
    p.add_argument("storyboard")
    p.add_argument("-o", "--output", help="where to write the page (default: output/<article>.html)")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("edition", help="check, then write several stories as one page")
    p.add_argument("manifest", help="the edition's manifest (.json)")
    p.add_argument("-o", "--output", help="where to write the page (default: output/<manifest>.html)")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=cmd_edition)

    p = sub.add_parser("gallery", help="render every template's example")
    p.add_argument("-o", "--output", default="output/gallery.html")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=cmd_gallery)

    p = sub.add_parser("templates", help="list the templates")
    p.set_defaults(func=cmd_templates)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LabelsError as err:
        _report([str(err)], "Fix the labels file and try again.")
        return 1
