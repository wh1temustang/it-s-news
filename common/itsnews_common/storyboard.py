"""Load a storyboard and check it before anything is rendered.

A storyboard is the JSON an agent writes after reading an article: which
templates to use, in what order, filled with what. Each approach has its own
storyboard schema and templates, but they share this shape:

    {"headline": {"title": "…", "dek": "…", "topic": "…"},
     "scenes": [{"template": "…", "question": "…", "data": {…}}],
     "bottom_line": "… (optional)"}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import grounding
from .article import Article
from .catalog import Template
from .schema import validate as validate_schema

# Agents often wrap their answer in a ```json fence; accept that.
_FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*?)\n[ \t]*```", re.DOTALL)


class StoryboardError(ValueError):
    pass


def parse(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as first:
        match = _FENCE.search(text)
        if not match:
            raise StoryboardError(f"not valid JSON: {first}") from None
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as err:
            raise StoryboardError(f"the ```json block is not valid JSON: {err}") from None
    if not isinstance(data, dict):
        raise StoryboardError("a storyboard must be a JSON object")
    return data


def load(path: str | Path) -> dict:
    return parse(Path(path).read_text(encoding="utf-8"))


def validate(storyboard: dict, schema: dict, templates: dict[str, Template]) -> list[str]:
    """Shape, template ids, each scene's data, and one question per scene."""
    errors = validate_schema(storyboard, schema)
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return errors

    seen: dict[str, int] = {}
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        template_id = scene.get("template")
        template = templates.get(template_id)
        if template is None:
            errors.append(
                f"$.scenes[{i}].template: unknown template {template_id!r}. "
                f"Use one of: {', '.join(templates)}"
            )
        elif isinstance(scene.get("data"), dict):
            errors += validate_schema(scene["data"], template.schema, f"$.scenes[{i}].data")

        question = str(scene.get("question", "")).strip().lower()
        if question and question in seen:
            errors.append(
                f"$.scenes[{i}].question: scene {seen[question]} already answers this "
                "question. Each scene answers a different one; merge or drop it."
            )
        seen.setdefault(question, i)
    return errors


def check(storyboard: dict, article: Article, schema: dict,
          templates: dict[str, Template]) -> list[str]:
    """Shape and grounding: everything every approach needs. Empty means ready."""
    return validate(storyboard, schema, templates) + grounding.check(
        storyboard, article, templates
    )
