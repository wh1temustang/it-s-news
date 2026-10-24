"""Tests every template kit must pass, to mix into an approach's own tests.

    class KitConformance(testing.KitTests, unittest.TestCase):
        kit = KIT

    class Examples(testing.ExampleTests, unittest.TestCase):
        kit = KIT
        examples = Path(__file__).parent.parent / "examples"

A template the catalog doesn't list is one the agent never picks; a catalog
row with no folder behind it is one the agent picks and can't use. The
example pages are committed, so they must match a fresh render.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

from . import article, edition, storyboard
from .catalog import Template
from .kit import Kit
from .schema import validate

# Jinja resolves data.items to dict.items(), not data["items"].
DICT_METHODS = {"items", "keys", "values", "get", "pop", "update", "copy", "clear"}
# Anything that would make the page load from the network.
_EXTERNAL = re.compile(r"<(script|link|img|iframe)\b|url\((?!#)|@import")


def field_names(schema: dict):
    for key, sub in schema.get("properties", {}).items():
        yield key
        yield from field_names(sub)
    if "items" in schema:
        yield from field_names(schema["items"])


def text_fields(schema: dict, path: str):
    """Every free-text field, as (path, schema). Enums aren't free text."""
    if schema.get("type") == "string" and "enum" not in schema:
        yield path, schema
    for key, sub in schema.get("properties", {}).items():
        yield from text_fields(sub, f"{path}.{key}")
    if "items" in schema:
        yield from text_fields(schema["items"], f"{path}[]")


def external_loads(html: str) -> list[str]:
    return [m.group(0) for m in _EXTERNAL.finditer(html)]


class KitTests:
    """The catalog, schemas, examples and markup agree. Set `kit`."""

    kit: Kit

    @property
    def templates(self) -> dict[str, Template]:
        return self.kit.load_templates()

    @property
    def catalog(self) -> str:
        return (self.kit.agent_dir / "catalog.md").read_text(encoding="utf-8")

    def test_every_template_is_in_the_catalog_table(self):
        table = set(re.findall(r"^\|[^|]+\| `([a-z-]+)` \|", self.catalog, re.M))
        self.assertEqual(table, set(self.templates))

    def test_every_template_has_a_catalog_note(self):
        for name in self.templates:
            self.assertIn(f"**`{name}`**", self.catalog, name)

    def test_each_template_has_its_files(self):
        for template in self.templates.values():
            for name in ("schema.json", "template.html.j2", "example.json", "style.css"):
                self.assertTrue((template.dir / name).is_file(), f"{template.id}/{name}")

    def test_each_schema_names_and_describes_itself(self):
        for template in self.templates.values():
            schema = template.schema
            self.assertTrue(schema.get("title"), template.id)
            self.assertTrue(schema.get("x-icon"), template.id)
            self.assertTrue(schema.get("description"), template.id)
            self.assertEqual(schema.get("type"), "object", template.id)
            self.assertIs(schema.get("additionalProperties"), False, template.id)

    def test_every_text_field_has_a_word_budget(self):
        for template in self.templates.values():
            for path, schema in text_fields(template.schema, template.id):
                self.assertIn("maxLength", schema, path)

    def test_no_field_shadows_a_dict_method(self):
        for template in self.templates.values():
            clash = DICT_METHODS & set(field_names(template.schema))
            self.assertFalse(clash, f"{template.id}: {clash}")

    def test_each_example_is_valid_and_renders(self):
        scene_schema = self.kit.storyboard_schema()["properties"]["scenes"]["items"]
        question_limit = scene_schema["properties"]["question"]["maxLength"]
        env = self.kit.environment()
        for template in self.templates.values():
            example = template.example
            self.assertLessEqual(len(example["question"]), question_limit, template.id)
            self.assertEqual(validate(example["data"], template.schema), [], template.id)
            sb = {"headline": {"title": "T", "dek": "D", "topic": "world"},
                  "scenes": [{"template": template.id, **example}]}
            view = self.kit.story_view(env, self.templates, sb, article.Article(body=""),
                                       self.kit.labels())
            html = view["scenes"][0]["html"]
            self.assertIn("<", html, template.id)
            self.assertNotIn("{{", html, template.id)

    def test_styles_use_tokens_not_raw_colours(self):
        # Raw colours would break dark mode; base.css is where tokens are defined.
        sheets = [*self.kit.templates_dir.glob("*/style.css")]
        edition_css = self.kit.templates_dir / "edition.css"
        if edition_css.is_file():
            sheets.append(edition_css)
        for path in sheets:
            css = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", css), path)

    def test_keyframes_do_not_collide(self):
        names = re.findall(r"@keyframes ([\w-]+)",
                           "".join(t.css for t in self.templates.values()))
        self.assertEqual(len(names), len(set(names)), names)

    def test_gallery_loads_nothing_from_elsewhere(self):
        html = self.kit.render_gallery()
        self.assertEqual(external_loads(html), [])
        self.assertNotIn("checked against the article", html)
        self.assertIn("made-up example data", html)


class ExampleTests:
    """The sample articles check clean and their committed pages are fresh.

    Set `kit` and `examples`, the folder that holds <name>.md beside
    <name>.storyboard.json and <name>.html, and optionally edition.json
    beside edition.html.
    """

    kit: Kit
    examples: Path

    def pairs(self) -> list[tuple[Path, Path]]:
        return sorted((md, md.with_suffix(".storyboard.json"))
                      for md in self.examples.glob("*.md"))

    def load(self, md: Path, sb: Path):
        return article.load(md), storyboard.load(sb)

    def test_there_are_examples(self):
        self.assertGreaterEqual(len(self.pairs()), 2)

    def test_examples_are_marked_fictional(self):
        for md, _ in self.pairs():
            self.assertTrue(article.load(md).fictional, md.name)

    def test_examples_pass_the_check(self):
        for md, sb in self.pairs():
            a, s = self.load(md, sb)
            self.assertEqual(self.kit.check(s, a), [], md.name)

    def test_rendering_is_deterministic(self):
        for md, sb in self.pairs():
            a, s = self.load(md, sb)
            self.assertEqual(self.kit.render_page(s, a),
                             self.kit.render_page(copy.deepcopy(s), a), md.name)

    def test_committed_pages_match_a_fresh_render(self):
        for md, sb in self.pairs():
            page = md.with_suffix(".html")
            a, s = self.load(md, sb)
            self.assertTrue(page.is_file(), f"{page.name} is missing: render it (see AGENTS.md)")
            self.assertEqual(page.read_text(encoding="utf-8"), self.kit.render_page(s, a),
                             f"{page.name} is stale: render it again (see AGENTS.md)")

    def test_pages_load_nothing_from_elsewhere(self):
        for md, sb in self.pairs():
            a, s = self.load(md, sb)
            self.assertEqual(external_loads(self.kit.render_page(s, a)), [], md.name)

    def test_example_edition(self):
        manifest = self.examples / "edition.json"
        if not manifest.is_file():
            self.skipTest("no example edition")
        issue = edition.load(manifest)
        self.assertEqual(self.kit.check_edition(issue), [])
        html = self.kit.render_edition(issue)
        self.assertEqual(external_loads(html), [])
        ids = re.findall(r'\bid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)), ids)
        for section in issue.sections:
            self.assertIn(f'href="#{section.id}"', html)
        page = manifest.with_suffix(".html")
        self.assertTrue(page.is_file(), f"{page.name} is missing: render it (see AGENTS.md)")
        self.assertEqual(page.read_text(encoding="utf-8"), html,
                         f"{page.name} is stale: render it again (see AGENTS.md)")
