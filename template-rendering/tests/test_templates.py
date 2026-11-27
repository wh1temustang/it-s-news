"""The template kit: catalog, schemas, examples and markup must agree.

The checks every kit shares are in itsnews_common.testing; the ones below
are this approach's own.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from itsnews_common import testing
from itsnews_common.article import Article
from itsnews_common.article import load as load_article
from itsnews_common.schema import validate
from itsnews_common.storyboard import load as load_storyboard
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


class VoicesRules(unittest.TestCase):
    """rules.py: each voice says exactly one thing — a verbatim quote or
    one grounded line. The shared checker grounds both; these rules are
    the either/or the generic walk cannot see."""

    BUS = (Path(__file__).resolve().parent.parent
           / "examples" / "fallowfield-bus")

    def _storyboard(self, voices):
        return {"headline": {"title": "T", "dek": "D", "topic": "local"},
                "scenes": [{"template": "voices",
                            "question": "Who is saying what?",
                            "why": "W", "data": {"voices": voices}}]}

    def _bus(self):
        return (load_article(self.BUS.with_suffix(".md")),
                load_storyboard(self.BUS.with_suffix(".storyboard.json")))

    def test_voices_needs_exactly_one_of_quote_and_stance(self):
        both = self._storyboard([
            {"name": "A", "character": "worker",
             "quote": "Q.", "stance": "S."},
            {"name": "B", "character": "official", "quote": "R."}])
        errors = rules.check(both, Article(body=""), TEMPLATES)
        self.assertTrue(any("both a quote and a stance" in e
                            for e in errors), errors)
        neither = self._storyboard([
            {"name": "A", "character": "worker"},
            {"name": "B", "character": "official", "quote": "R."}])
        errors = rules.check(neither, Article(body=""), TEMPLATES)
        self.assertTrue(any("neither a quote nor a stance" in e
                            for e in errors), errors)

    def test_voices_quote_must_be_verbatim(self):
        article, _ = self._bus()
        sb = self._storyboard([
            {"name": "Councillor Priya Nair", "character": "official",
             "quote": "We have heard the night shift for years, and "
                      "this trial is our reply."},
            {"name": "Tom Okafor", "character": "worker",
             "quote": "The last run ends at 3 am, and I am the one "
                      "driving it home."}])
        errors = KIT.check(sb, article, TEMPLATES)
        self.assertTrue(errors, errors)
        self.assertTrue(any("quote" in e for e in errors), errors)

    def test_voices_stance_numbers_must_be_grounded(self):
        article, _ = self._bus()
        sb = self._storyboard([
            {"name": "June Park", "character": "resident",
             "stance": "Would take the bus 12 nights a week."},
            {"name": "Tom Okafor", "character": "worker",
             "quote": "The last run ends at 3 am, and I am the one "
                      "driving it home."}])
        errors = KIT.check(sb, article, TEMPLATES)
        self.assertTrue(errors, errors)

    def test_voices_with_quote_and_stance_passes(self):
        article, sb = self._bus()
        self.assertEqual(KIT.check(sb, article, TEMPLATES), [])

    def test_voices_schema_rejects_unknown_character(self):
        data = {"voices": [
            {"name": "A", "character": "wizard", "quote": "Q."},
            {"name": "B", "character": "worker", "quote": "R."}]}
        self.assertTrue(validate(data, TEMPLATES["voices"].schema))

    def test_voices_schema_requires_two_to_four(self):
        one = {"voices": [{"name": "A", "character": "worker",
                           "quote": "Q."}]}
        self.assertTrue(validate(one, TEMPLATES["voices"].schema))
        five = {"voices": [{"name": f"V{i}", "character": "worker",
                            "quote": "Q."} for i in range(5)]}
        self.assertTrue(validate(five, TEMPLATES["voices"].schema))

    def test_every_voices_character_renders(self):
        characters = ["worker", "executive", "official", "judge",
                      "scientist", "resident", "activist", "farmer"]
        scenes = []
        for i in range(0, len(characters), 4):
            voices = [{"name": f"Voice {c}", "character": c,
                       "stance": "Standing by."}
                      for c in characters[i:i + 4]]
            scenes.append({"template": "voices",
                           "question": "Who is saying what?",
                           "why": "W", "data": {"voices": voices}})
        sb = {"headline": {"title": "T", "dek": "D", "topic": "local"},
              "scenes": scenes}
        env = KIT.environment()
        view = KIT.story_view(env, TEMPLATES, sb, Article(body=""),
                              KIT.labels())
        html = "".join(scene["html"] for scene in view["scenes"])
        for character in characters:
            self.assertIn(f"vc-{character}", html, character)
        self.assertNotIn("{{", html)

    def test_every_voices_class_the_template_emits_has_a_css_rule(self):
        # A class with no CSS rule silently does nothing: the scene
        # template did exactly this once — it emitted sc-fall while the
        # sheet only defined .sc-drop, so the rain never fell.
        voices = TEMPLATES["voices"]
        template_text = (voices.dir / "template.html.j2").read_text(encoding="utf-8")
        css = (voices.dir / "style.css").read_text(encoding="utf-8")
        emitted = set(re.findall(r"vc-[a-z-]+", template_text))
        self.assertTrue(emitted)
        for name in sorted(emitted):
            self.assertIn(f".{name}", css, name)


if __name__ == "__main__":
    unittest.main()
