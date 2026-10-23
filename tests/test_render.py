"""End to end: examples check clean, render the same every time, and stay self-contained."""
from __future__ import annotations

import copy
import io
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from itsnews import article, cli, storyboard
from itsnews.catalog import PACKAGE_DIR
from itsnews.render import FICTIONAL_BANNER, render_gallery, render_page

EXAMPLES = PACKAGE_DIR.parent / "examples"
PAIRS = sorted(
    (md, md.with_suffix(".storyboard.json")) for md in EXAMPLES.glob("*.md")
)


def load(md: Path, sb: Path):
    return article.load(md), storyboard.load(sb)


class ExampleTests(unittest.TestCase):
    def test_there_are_examples(self):
        self.assertGreaterEqual(len(PAIRS), 2)

    def test_examples_are_marked_fictional(self):
        for md, _ in PAIRS:
            self.assertTrue(article.load(md).fictional, md.name)

    def test_examples_pass_the_check(self):
        for md, sb in PAIRS:
            a, s = load(md, sb)
            self.assertEqual(storyboard.check(s, a), [], md.name)

    def test_rendering_is_deterministic(self):
        for md, sb in PAIRS:
            a, s = load(md, sb)
            self.assertEqual(render_page(s, a), render_page(copy.deepcopy(s), a), md.name)

    def test_committed_pages_match_a_fresh_render(self):
        for md, sb in PAIRS:
            page = md.with_suffix(".html")
            a, s = load(md, sb)
            self.assertTrue(page.is_file(), f"{page.name} is missing: render it (see AGENTS.md)")
            self.assertEqual(page.read_text(encoding="utf-8"), render_page(s, a),
                             f"{page.name} is stale: render it again (see AGENTS.md)")

    def test_pages_load_nothing_from_elsewhere(self):
        pages = [render_page(*reversed(load(md, sb))) for md, sb in PAIRS]
        for html in pages + [render_gallery()]:
            self.assertIsNone(re.search(r"<(script|link|img|iframe)\b", html))
            self.assertIsNone(re.search(r"url\((?!#)", html))
            self.assertNotIn("@import", html)

    def test_fictional_banner_and_scene_headings(self):
        md, sb = PAIRS[0]
        a, s = load(md, sb)
        html = render_page(s, a)
        self.assertIn(FICTIONAL_BANNER, html)
        for scene in s["scenes"]:
            self.assertIn(scene["question"].replace("'", "&#39;"), html)


class SafetyTests(unittest.TestCase):
    def test_article_and_storyboard_text_is_escaped(self):
        a = article.parse("---\nsource: <b>Src</b>\nurl: javascript:alert(1)\n---\nBody\n")
        s = {
            "headline": {"title": "<script>alert(1)</script>", "dek": "d", "topic": "world"},
            "scenes": [{"template": "quote", "question": "Q",
                        "data": {"text": "</p><img src=x onerror=alert(1)>", "speaker": "S"}}],
        }
        html = render_page(s, a)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;b&gt;Src&lt;/b&gt;", html)
        self.assertNotIn("javascript:", html)

    def test_gallery_does_not_claim_its_examples_were_checked(self):
        html = render_gallery()
        self.assertNotIn("checked against the article", html)
        self.assertIn("made-up example data", html)


class StoryboardTests(unittest.TestCase):
    def setUp(self):
        md, sb = PAIRS[0]
        self.article, self.sb = load(md, sb)

    def test_json_inside_a_code_fence_is_accepted(self):
        text = "Here you go:\n```json\n{\"headline\": {}, \"scenes\": []}\n```\n"
        self.assertEqual(storyboard.parse(text), {"headline": {}, "scenes": []})

    def test_not_json_is_a_clear_error(self):
        with self.assertRaisesRegex(storyboard.StoryboardError, "not valid JSON"):
            storyboard.parse("I picked a timeline.")

    def test_unknown_template(self):
        self.sb["scenes"][0]["template"] = "pie-chart"
        errors = storyboard.check(self.sb, self.article)
        self.assertTrue(any("unknown template 'pie-chart'" in e for e in errors), errors)

    def test_two_scenes_may_not_answer_the_same_question(self):
        self.sb["scenes"][1]["question"] = self.sb["scenes"][0]["question"].upper()
        errors = storyboard.check(self.sb, self.article)
        self.assertTrue(any("already answers this question" in e for e in errors), errors)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_prompt_contains_everything_the_agent_needs(self):
        md, _ = PAIRS[0]
        code, out, _ = self.run_cli("prompt", str(md))
        self.assertEqual(code, 0)
        self.assertIn("# Storyboard prompt", out)
        self.assertIn("# Template catalog", out)
        self.assertIn("Template `timeline`", out)
        self.assertIn('"title": "Storyboard"', out)
        self.assertTrue(out.rstrip().endswith("````"))
        self.assertIn(md.read_text(encoding="utf-8").strip(), out)

    def test_check_and_render(self):
        md, sb = PAIRS[0]
        self.assertEqual(self.run_cli("check", str(md), str(sb))[0], 0)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "page.html"
            code, _, _ = self.run_cli("render", str(md), str(sb), "-o", str(target))
            self.assertEqual(code, 0)
            self.assertTrue(target.read_text(encoding="utf-8").startswith("<!doctype html>"))

    def test_render_refuses_a_storyboard_that_fails_the_check(self):
        md, _ = PAIRS[0]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text('{"headline": {"title": "t", "dek": "d", "topic": "world"},'
                           ' "scenes": [{"template": "big-number", "question": "Q",'
                           ' "data": {"numbers": [{"value": "999", "label": "x"}]}}]}')
            target = Path(tmp) / "page.html"
            code, _, err = self.run_cli("render", str(md), str(bad), "-o", str(target))
            self.assertEqual(code, 1)
            self.assertIn("the number 999 is not in the article", err)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
