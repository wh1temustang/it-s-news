"""The template kit: catalog, schemas, examples and markup must agree.

A template the catalog doesn't list is one the agent never picks; a catalog
row with no folder behind it is one the agent picks and can't use.
"""
from __future__ import annotations

import re
import unittest

from template_rendering.catalog import PACKAGE_DIR, TEMPLATES_DIR, load_templates
from template_rendering.article import Article
from template_rendering.labels import Labels
from template_rendering.render import environment, story_view
from template_rendering.schema import validate

CATALOG = (PACKAGE_DIR.parent / "agent" / "catalog.md").read_text(encoding="utf-8")
TEMPLATES = load_templates()
# Jinja resolves data.items to dict.items(), not data["items"].
DICT_METHODS = {"items", "keys", "values", "get", "pop", "update", "copy", "clear"}


def field_names(schema: dict):
    for key, sub in schema.get("properties", {}).items():
        yield key
        yield from field_names(sub)
    if "items" in schema:
        yield from field_names(schema["items"])


class CatalogTests(unittest.TestCase):
    def test_the_templates_the_user_asked_for_exist(self):
        for name in ("timeline", "info-board", "map"):
            self.assertIn(name, TEMPLATES)

    def test_every_template_is_in_the_catalog_table(self):
        table = {m for m in re.findall(r"^\|[^|]+\| `([a-z-]+)` \|", CATALOG, re.M)}
        self.assertEqual(table, set(TEMPLATES))

    def test_every_template_has_a_catalog_note(self):
        for name in TEMPLATES:
            self.assertIn(f"**`{name}`**", CATALOG, name)


class TemplateTests(unittest.TestCase):
    def test_each_template_has_its_files(self):
        for template in TEMPLATES.values():
            for name in ("schema.json", "template.html.j2", "example.json", "style.css"):
                self.assertTrue((template.dir / name).is_file(), f"{template.id}/{name}")

    def test_each_schema_names_and_describes_itself(self):
        for template in TEMPLATES.values():
            schema = template.schema
            self.assertTrue(schema.get("title"), template.id)
            self.assertTrue(schema.get("x-icon"), template.id)
            self.assertTrue(schema.get("description"), template.id)
            self.assertEqual(schema.get("type"), "object", template.id)
            self.assertIs(schema.get("additionalProperties"), False, template.id)

    def test_every_text_field_has_a_word_budget(self):
        def strings(schema, path):
            if schema.get("type") == "string" and "enum" not in schema:
                yield path, schema
            for key, sub in schema.get("properties", {}).items():
                yield from strings(sub, f"{path}.{key}")
            if "items" in schema:
                yield from strings(schema["items"], f"{path}[]")

        for template in TEMPLATES.values():
            for path, schema in strings(template.schema, template.id):
                self.assertIn("maxLength", schema, path)

    def test_no_field_shadows_a_dict_method(self):
        for template in TEMPLATES.values():
            clash = DICT_METHODS & set(field_names(template.schema))
            self.assertFalse(clash, f"{template.id}: {clash}")

    def test_each_example_is_valid_and_renders(self):
        env = environment()
        for template in TEMPLATES.values():
            example = template.example
            self.assertLessEqual(len(example["question"]), 60, template.id)
            self.assertEqual(validate(example["data"], template.schema), [], template.id)
            storyboard = {"headline": {"title": "T", "dek": "D", "topic": "world"},
                          "scenes": [{"template": template.id, **example}]}
            scene = story_view(env, TEMPLATES, storyboard, Article(body=""), Labels())["scenes"][0]
            self.assertIn("<", scene["html"], template.id)
            self.assertNotIn("{{", scene["html"], template.id)

    def test_styles_use_tokens_not_raw_colours(self):
        # Raw colours would break dark mode; base.css is where tokens are defined.
        for path in [*TEMPLATES_DIR.glob("*/style.css"), TEMPLATES_DIR / "edition.css"]:
            css = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", css), path)

    def test_keyframes_do_not_collide(self):
        names = re.findall(r"@keyframes ([\w-]+)",
                           "".join(t.css for t in TEMPLATES.values()))
        self.assertEqual(len(names), len(set(names)), names)


if __name__ == "__main__":
    unittest.main()
