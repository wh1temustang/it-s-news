"""The meme kit: the shared checks, the mood rules, and the post around the memes."""
from __future__ import annotations

import copy
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from itsnews_common import article, edition, storyboard, testing
from meme_rendering import cli, mood
from meme_rendering.kit import KIT, PACKAGE_DIR
from meme_rendering.labels import Labels

EXAMPLES = PACKAGE_DIR.parent / "examples"
TEMPLATES = KIT.load_templates()
LIGHT = (article.load(EXAMPLES / "self-checkout.md"),
         storyboard.load(EXAMPLES / "self-checkout.storyboard.json"))
SERIOUS = (article.load(EXAMPLES / "river-flood.md"),
           storyboard.load(EXAMPLES / "river-flood.storyboard.json"))
STONKS = {"template": "stonks", "question": "How high?",
          "data": {"numbers": [{"value": "4.2 metres", "label": "Peak", "trend": "up"}]}}


class KitTests(testing.KitTests, unittest.TestCase):
    kit = KIT

    def test_every_format_says_whether_it_is_a_joke(self):
        for template in TEMPLATES.values():
            self.assertIsInstance(template.schema.get("x-joke"), bool, template.id)

    def test_serious_stories_have_straight_formats(self):
        straight = {t.id for t in TEMPLATES.values() if not mood.joke(t)}
        self.assertEqual(straight, {"megathread", "thread", "remindme"})

    def test_quotes_are_verbatim_and_emoji_carry_no_text(self):
        self.assertTrue(TEMPLATES["change-my-mind"].schema["properties"]["text"]["x-verbatim"])
        comment = TEMPLATES["thread"].schema["properties"]["comments"]["items"]
        self.assertTrue(comment["properties"]["text"]["x-verbatim"])
        a, sb = LIGHT
        sb = copy.deepcopy(sb)
        sb["scenes"][0] = {"template": "starter-pack", "question": "What's new?", "data": {
            "subject": "Staffed till", "pieces": [
                {"emoji": "🛒", "text": "Staffed tills"},
                {"emoji": "99", "text": "About 900 cashiers"},
                {"emoji": "🧾", "text": "At least two self-checkouts"}]}}
        errors = KIT.check(sb, a)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("pieces[1].emoji: '99' doesn't match the pattern", errors[0])


class Examples(testing.ExampleTests, unittest.TestCase):
    kit = KIT
    examples = EXAMPLES

    def test_the_examples_show_both_moods(self):
        self.assertEqual(LIGHT[1]["headline"]["mood"], "light")
        self.assertEqual(SERIOUS[1]["headline"]["mood"], "serious")
        self.assertTrue(any(mood.joke(TEMPLATES[s["template"]]) for s in LIGHT[1]["scenes"]))


class MoodTests(unittest.TestCase):
    def test_a_serious_story_refuses_joke_formats(self):
        a, sb = SERIOUS
        sb = copy.deepcopy(sb)
        sb["scenes"].append(STONKS)
        errors = KIT.check(sb, a)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("$.scenes[3].template: 'stonks' is a joke format", errors[0])
        self.assertIn("(megathread, remindme, thread)", errors[0])

    def test_an_article_about_harm_is_serious_whatever_the_storyboard_says(self):
        a, sb = SERIOUS
        sb = copy.deepcopy(sb)
        sb["headline"]["mood"] = "light"
        sb["scenes"].append(STONKS)
        errors = " | ".join(KIT.check(sb, a))
        self.assertIn("$.headline.mood: the article mentions 'Flooding'", errors)
        self.assertIn("'stonks' is a joke format", errors)

    def test_a_light_story_may_go_straight(self):
        a, sb = LIGHT
        sb = copy.deepcopy(sb)
        sb["headline"]["mood"] = "serious"
        sb["scenes"] = [sb["scenes"][-1]]
        self.assertEqual(KIT.check(sb, a), [])

    def test_harm_words(self):
        for text in ("Two people were killed", "an earthquake struck", "three were injured",
                     "the WAR in the north", "after the shooting"):
            self.assertIsNotNone(mood.HARM.search(text), text)
        for text in ("the deadline moved", "Star Wars returns", "a skilled team",
                     "shares fell 3%", "theft losses"):
            self.assertIsNone(mood.HARM.search(text), text)


class PageTests(unittest.TestCase):
    def test_a_post_shows_no_made_up_numbers(self):
        a, sb = LIGHT
        html = KIT.render_page(sb, a)
        rail = re.search(r'<div class="vote".*?</div>', html).group(0)
        self.assertIsNone(re.search(r"\d", rail), rail)
        self.assertNotIn("u/", html)
        self.assertIn("Not affiliated with Reddit.", html)
        self.assertIn('<span class="sub">r/business</span>', html)
        self.assertIn("<h2>TL;DR</h2>", html)

    def test_serious_stories_carry_the_flair(self):
        flair = '<span class="flair">Serious</span>'
        self.assertIn(flair, KIT.render_page(SERIOUS[1], SERIOUS[0]))
        self.assertNotIn(flair, KIT.render_page(LIGHT[1], LIGHT[0]))

    def test_story_text_is_escaped(self):
        a = article.parse("---\nsource: <b>Src</b>\nurl: javascript:alert(1)\n---\nBody\n")
        sb = {"headline": {"title": "<script>alert(1)</script>", "dek": "d",
                           "topic": "world", "mood": "light"},
              "scenes": [{"template": "distracted", "question": "Q",
                          "data": {"who": "<img src=x>", "old": "a", "new": "b"}}]}
        html = KIT.render_page(sb, a)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("javascript:", html)
        self.assertIn("&lt;img src=x&gt; turns away from a, toward b.", html)

    def test_only_a_later_comment_can_be_a_reply(self):
        a, sb = LIGHT
        sb = copy.deepcopy(sb)
        thread = sb["scenes"][-1]["data"]["comments"]
        thread[0]["reply"] = True
        html = KIT.render_page(sb, a)
        self.assertEqual(html.count('class="th-c th-c--reply"'), 1)

    def test_labels_in_another_language(self):
        a, sb = LIGHT
        t = Labels({"lang": "fr", "topic.business": "r/economie", "bottom_line": "En bref",
                    "stonks.caption": "Stonks"})
        html = KIT.render_page(sb, a, labels=t)
        self.assertIn('<html lang="fr">', html)
        self.assertIn("r/economie", html)
        self.assertIn("<h2>En bref</h2>", html)

    def test_edition_is_a_feed_of_posts(self):
        issue = edition.load(EXAMPLES / "edition.json")
        html = KIT.render_edition(issue)
        self.assertEqual(html.count('<article class="post story-card"'), 2)
        self.assertIn('<h4 id="story-2-q1">', html)
        self.assertEqual(html.count(TEMPLATES["thread"].css), 1)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_prompt_contains_everything_the_agent_needs(self):
        md = EXAMPLES / "self-checkout.md"
        code, out, _ = self.run_cli("prompt", str(md))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("# Meme storyboard prompt"))
        self.assertIn("# Meme catalog", out)
        self.assertIn("Template `distracted`", out)
        self.assertIn('"mood"', out)
        self.assertIn(md.read_text(encoding="utf-8").strip(), out)

    def test_check_refuses_a_joke_in_a_serious_story(self):
        _, sb = SERIOUS
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({**sb, "scenes": sb["scenes"] + [STONKS]}))
            code, _, err = self.run_cli("check", str(EXAMPLES / "river-flood.md"), str(bad))
        self.assertEqual(code, 1)
        self.assertIn("'stonks' is a joke format", err)


if __name__ == "__main__":
    unittest.main()
