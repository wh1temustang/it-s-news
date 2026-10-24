"""A template registry.

Each folder in an approach's templates/ that holds a schema.json is one template:

    templates/<id>/
      schema.json        what the agent must fill in (title, x-icon, limits)
      template.html.j2   the Jinja2 markup for one scene
      example.json       a sample scene ({"question", "data"}) for the gallery and tests
      style.css          optional styles, inlined only when a page uses the template

The page shell (page.html.j2, base.css and so on) lives in templates/ itself;
see kit.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path


@dataclass(frozen=True)
class Template:
    id: str
    dir: Path

    @cached_property
    def schema(self) -> dict:
        return json.loads((self.dir / "schema.json").read_text(encoding="utf-8"))

    @property
    def name(self) -> str:
        return self.schema["title"]

    @property
    def icon(self) -> str:
        return self.schema.get("x-icon", "")

    @property
    def markup(self) -> str:
        """Path of the scene's Jinja2 template, relative to the templates folder."""
        return f"{self.id}/template.html.j2"

    @cached_property
    def example(self) -> dict:
        return json.loads((self.dir / "example.json").read_text(encoding="utf-8"))

    @cached_property
    def css(self) -> str:
        path = self.dir / "style.css"
        return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_templates(templates_dir: Path) -> dict[str, Template]:
    """All templates in `templates_dir`, keyed by id, in a stable (alphabetical) order."""
    found = sorted(p.parent for p in Path(templates_dir).glob("*/schema.json"))
    return {d.name: Template(d.name, d) for d in found}
