"""The template registry.

Each folder in template_rendering/templates/ that holds a schema.json is one template:

    templates/<id>/
      schema.json        what the agent must fill in (title, x-icon, limits)
      template.html.j2   the Jinja2 markup for one scene
      example.json       a sample scene ({"question", "data"}) for the gallery and tests
      style.css          optional styles, inlined only when a page uses the template

The page shell (page.html.j2, base.css) lives in templates/ itself.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


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
        """Path of the scene's Jinja2 template, relative to TEMPLATES_DIR."""
        return f"{self.id}/template.html.j2"

    @cached_property
    def example(self) -> dict:
        return json.loads((self.dir / "example.json").read_text(encoding="utf-8"))

    @cached_property
    def css(self) -> str:
        path = self.dir / "style.css"
        return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_templates() -> dict[str, Template]:
    """All templates, keyed by id, in a stable (alphabetical) order."""
    found = sorted(p.parent for p in TEMPLATES_DIR.glob("*/schema.json"))
    return {d.name: Template(d.name, d) for d in found}


def storyboard_schema() -> dict:
    return json.loads((PACKAGE_DIR / "storyboard.schema.json").read_text(encoding="utf-8"))
