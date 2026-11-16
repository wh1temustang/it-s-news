"""The template kit: catalog, schemas, examples and markup must agree.

The checks every kit shares are in itsnews_common.testing; the ones below
are this approach's own.
"""
from __future__ import annotations

import re
import unittest

from itsnews_common import testing
from template_rendering.kit import KIT

TEMPLATES = KIT.load_templates()


class KitTests(testing.KitTests, unittest.TestCase):
    kit = KIT

    def test_the_templates_the_user_asked_for_exist(self):
        for name in ("timeline", "info-board", "map"):
            self.assertIn(name, TEMPLATES)

    def test_map_coordinates_are_general_knowledge_and_quotes_are_verbatim(self):
        place = TEMPLATES["map"].schema["properties"]["places"]["items"]["properties"]
        self.assertTrue(place["lat"].get("x-ungrounded"))
        self.assertTrue(place["lng"].get("x-ungrounded"))
        self.assertTrue(TEMPLATES["quote"].schema["properties"]["text"].get("x-verbatim"))

    def test_every_scene_anim_kind_has_a_css_rule(self):
        # The scene template emits class="sc-<anim>" for every anim the
        # schema allows. A kind with no CSS rule silently does not move:
        # fall did exactly this — the template emitted sc-fall while the
        # sheet only defined .sc-drop. Every kind needs its rule, and a
        # place in the reduced-motion list.
        scene = TEMPLATES["scene"]
        css = (scene.dir / "style.css").read_text(encoding="utf-8")
        shapes = scene.schema["properties"]["shapes"]["items"]["properties"]
        anims = shapes["anim"]["enum"]
        children_anims = shapes["children"]["items"]["properties"]["anim"]["enum"]
        self.assertEqual(children_anims, anims)
        reduced = css.split("@media (prefers-reduced-motion")[1]
        for anim in anims:
            self.assertIn(f".sc-{anim}", css, anim)
            self.assertIn(f".sc-{anim}", reduced, anim)

    def test_every_scene_class_the_template_emits_has_a_css_rule(self):
        scene = TEMPLATES["scene"]
        template_text = (scene.dir / "template.html.j2").read_text(encoding="utf-8")
        css = (scene.dir / "style.css").read_text(encoding="utf-8")
        emitted = set()
        for attrs in re.findall(r'class="([^"]+)"', template_text):
            emitted.update(t for t in attrs.split() if re.fullmatch(r"sc-[a-z]+", t))
        self.assertTrue(emitted)
        for name in sorted(emitted):
            self.assertIn(f".{name}", css, name)


if __name__ == "__main__":
    unittest.main()
