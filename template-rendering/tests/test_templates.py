"""The template kit: catalog, schemas, examples and markup must agree.

The checks every kit shares are in itsnews_common.testing; the ones below
are this approach's own.
"""
from __future__ import annotations

import re
import unittest

from itsnews_common import testing
from itsnews_common.article import Article
from template_rendering import rules
from template_rendering.kit import KIT

TEMPLATES = KIT.load_templates()


class KitTests(testing.KitTests, unittest.TestCase):
    kit = KIT

    def test_the_templates_the_user_asked_for_exist(self):
        for name in ("timeline", "list", "map"):
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


class ScaleAndBreakdownRules(unittest.TestCase):
    """rules.py: explicit scale bounds must bracket, breakdown totals
    must be positive. The shared checker grounds the numbers; these
    rules are the cross-field checks it cannot see."""

    def _storyboard(self, template, data):
        return {"headline": {"title": "T", "dek": "D", "topic": "world"},
                "scenes": [{"template": template, "question": "Q?",
                            "why": "W", "data": data}]}

    def test_scale_min_must_not_exclude_the_value(self):
        article = Article(body="The gauge read 4.2 m, above the 4.0 m "
                               "threshold and below the 4.6 m record.")
        sb = self._storyboard("scale", {
            "value": 4.2,
            "marks": [{"value": 4.0, "label": "Threshold"},
                      {"value": 4.6, "label": "Record"}],
            "min": 4.3, "max": 5.0})
        errors = rules.check(sb, article, TEMPLATES)
        self.assertTrue(any("axis floor" in e for e in errors), errors)

    def test_scale_max_must_be_above_min(self):
        sb = self._storyboard("scale", {
            "value": 4.2,
            "marks": [{"value": 4.0, "label": "Threshold"}],
            "min": 5.0, "max": 4.0})
        errors = rules.check(sb, Article(body=""), TEMPLATES)
        self.assertTrue(any("not above the axis floor" in e
                            for e in errors), errors)

    def test_scale_with_bracketing_bounds_passes(self):
        sb = self._storyboard("scale", {
            "value": 4.2,
            "marks": [{"value": 4.0, "label": "Threshold"},
                      {"value": 4.6, "label": "Record"}],
            "min": 3.5, "max": 5.0})
        self.assertEqual(rules.check(sb, Article(body=""), TEMPLATES), [])

    def test_breakdown_total_must_be_above_zero(self):
        sb = self._storyboard("breakdown", {
            "total": {"value": 0, "label": "Budget"},
            "parts": [{"name": "Grant", "value": 60000}]})
        errors = rules.check(sb, Article(body=""), TEMPLATES)
        self.assertTrue(any("not above 0" in e for e in errors), errors)

    def test_breakdown_part_must_not_be_negative(self):
        sb = self._storyboard("breakdown", {
            "total": {"value": 120000, "label": "Budget"},
            "parts": [{"name": "Grant", "value": -1}]})
        errors = rules.check(sb, Article(body=""), TEMPLATES)
        self.assertTrue(any("below 0" in e for e in errors), errors)

    def test_breakdown_with_positive_total_passes(self):
        sb = self._storyboard("breakdown", {
            "total": {"value": 120000, "label": "Budget"},
            "parts": [{"name": "Grant", "value": 60000}]})
        self.assertEqual(rules.check(sb, Article(body=""), TEMPLATES), [])


if __name__ == "__main__":
    unittest.main()
