"""The template kit: catalog, schemas, examples and markup must agree.

The checks every kit shares are in itsnews_common.testing; the ones below
are this approach's own.
"""
from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
