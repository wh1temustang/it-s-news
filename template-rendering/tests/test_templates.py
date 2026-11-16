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

    def test_every_game_class_the_template_emits_has_a_css_rule(self):
        # The game template emits gm-* classes in its markup and adds
        # a few more from its scripts (gm-right, gm-wrong, gm-good).
        # A class with no CSS rule silently does nothing: the scene
        # template did exactly this once — it emitted sc-fall while the
        # sheet only defined .sc-drop, so the rain never fell.
        game = TEMPLATES["game"]
        template_text = (game.dir / "template.html.j2").read_text(encoding="utf-8")
        css = (game.dir / "style.css").read_text(encoding="utf-8")
        emitted = set(re.findall(r"gm-[a-z-]+", template_text))
        self.assertTrue(emitted)
        for name in sorted(emitted):
            self.assertIn(f".{name}", css, name)


if __name__ == "__main__":
    unittest.main()
