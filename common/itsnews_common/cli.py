"""The command line every template kit shares: python -m <package> <command> ...

    prompt   ARTICLE                 print the full instructions for the agent
    check    ARTICLE STORYBOARD      validate a storyboard against its article
    render   ARTICLE STORYBOARD      check, then write the HTML page
    edition  MANIFEST                check, then write several stories as one page
    gallery                          render every template's example
    templates                        list the templates

render, edition and gallery take --labels FILE to write the page's own
words in another language (see labels.py).

An approach's own cli.py calls main() with its kit:

    def main(argv=None):
        return cli.main(KIT, argv, "Turn a news article into a visual page.")
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import article as article_mod
from . import edition as edition_mod
from . import storyboard as storyboard_mod
from .kit import Kit
from .labels import LabelsError, load_labels


def _report(errors: list[str], fix: str = "Fix the storyboard and run check again.") -> None:
    for error in errors:
        print(f"✗ {error}", file=sys.stderr)
    print(f"\n{len(errors)} problem(s). {fix}", file=sys.stderr)


def _write(out: Path, html: str) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"✓ wrote {out}")
    return 0


class _Commands:
    def __init__(self, kit: Kit):
        self.kit = kit

    def _labels(self, args):
        return load_labels(args.labels, self.kit.labels) if args.labels else self.kit.labels()

    def _load(self, article_path: str, storyboard_path: str):
        article = article_mod.load(article_path)
        try:
            storyboard = storyboard_mod.load(storyboard_path)
        except storyboard_mod.StoryboardError as err:
            return article, None, [f"{storyboard_path}: {err}"]
        return article, storyboard, self.kit.check(storyboard, article)

    def prompt(self, args) -> int:
        if not (self.kit.agent_dir / "prompt.md").is_file():
            print("✗ agent/prompt.md not found. Run this from a clone of the repository "
                  "(pip install -e .).", file=sys.stderr)
            return 1
        sys.stdout.write(self.kit.build_prompt(Path(args.article)))
        return 0

    def check(self, args) -> int:
        _, storyboard, errors = self._load(args.article, args.storyboard)
        if errors:
            _report(errors)
            return 1
        scenes = ", ".join(s["template"] for s in storyboard["scenes"])
        print(f"✓ storyboard is ready to render ({scenes})")
        return 0

    def render(self, args) -> int:
        labels = self._labels(args)
        article, storyboard, errors = self._load(args.article, args.storyboard)
        if errors:
            _report(errors)
            return 1
        out = Path(args.output) if args.output else Path("output") / (
            Path(args.article).stem + ".html"
        )
        return _write(out, self.kit.render_page(storyboard, article, labels=labels))

    def edition(self, args) -> int:
        labels = self._labels(args)
        try:
            edition = edition_mod.load(args.manifest)
        except edition_mod.EditionError as err:
            _report(err.errors, "Fix the manifest and run edition again.")
            return 1
        errors = self.kit.check_edition(edition)
        if errors:
            _report(errors, "Fix the storyboards and run edition again.")
            return 1
        out = Path(args.output) if args.output else Path("output") / (
            Path(args.manifest).stem + ".html"
        )
        return _write(out, self.kit.render_edition(edition, labels=labels))

    def gallery(self, args) -> int:
        return _write(Path(args.output), self.kit.render_gallery(labels=self._labels(args)))

    def templates(self, args) -> int:
        for template in self.kit.load_templates().values():
            print(f"{template.icon}  {template.id:<16} {template.schema.get('description', '')}")
        return 0


def main(kit: Kit, argv: list[str] | None = None, description: str = "") -> int:
    commands = _Commands(kit)
    parser = argparse.ArgumentParser(prog=kit.name, description=description)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prompt", help="print the full instructions for the agent")
    p.add_argument("article", help="the news article (.md)")
    p.set_defaults(func=commands.prompt)

    p = sub.add_parser("check", help="validate a storyboard against its article")
    p.add_argument("article")
    p.add_argument("storyboard", help="the agent's storyboard (.json)")
    p.set_defaults(func=commands.check)

    p = sub.add_parser("render", help="check, then write the HTML page")
    p.add_argument("article")
    p.add_argument("storyboard")
    p.add_argument("-o", "--output", help="where to write the page (default: output/<article>.html)")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=commands.render)

    p = sub.add_parser("edition", help="check, then write several stories as one page")
    p.add_argument("manifest", help="the edition's manifest (.json)")
    p.add_argument("-o", "--output", help="where to write the page (default: output/<manifest>.html)")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=commands.edition)

    p = sub.add_parser("gallery", help="render every template's example")
    p.add_argument("-o", "--output", default="output/gallery.html")
    p.add_argument("--labels", help="a JSON file of the page's own words in another language")
    p.set_defaults(func=commands.gallery)

    p = sub.add_parser("templates", help="list the templates")
    p.set_defaults(func=commands.templates)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LabelsError as err:
        _report([str(err)], "Fix the labels file and try again.")
        return 1
