"""End to end: examples check clean, render the same every time, and stay self-contained."""
from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from itsnews_common import testing
from template_rendering import article, cli, storyboard
from template_rendering.kit import KIT, PACKAGE_DIR
from template_rendering.render import FICTIONAL_BANNER, render_gallery, render_page

EXAMPLES = PACKAGE_DIR.parent / "examples"
PAIRS = sorted(
    (md, md.with_suffix(".storyboard.json")) for md in EXAMPLES.glob("*.md")
)


def load(md: Path, sb: Path):
    return article.load(md), storyboard.load(sb)


class ExampleTests(testing.ExampleTests, unittest.TestCase):
    kit = KIT
    examples = EXAMPLES

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

    def test_gallery_renders_every_template(self):
        html = render_gallery()
        for template in KIT.load_templates().values():
            self.assertIn(f"scene--{template.id}", html)


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


class SceneTests(unittest.TestCase):
    def article(self):
        return article.parse("---\nsource: Test\n---\nBody\n")

    def board(self, data):
        return {"headline": {"title": "T", "dek": "D", "topic": "world"},
                "scenes": [{"template": "scene", "question": "What happens?",
                            "data": data}]}

    def render(self, data):
        return render_page(self.board(data), self.article())

    def test_stream_shape_emits_class_speed_and_delay(self):
        html = self.render({"character": "robot", "label": "Test", "shapes": [
            {"kind": "circle", "cx": 50, "cy": 50, "r": 3, "fill": "#7fd4ff",
             "anim": "stream", "speed": 1.5, "delay": -0.5}]})
        self.assertIn('class="sc-stream"', html)
        self.assertIn("--m:1.5;", html)
        self.assertIn("animation-delay:-0.5s;", html)
        self.assertIn("figure.style.setProperty('--stream'", html)

    def test_pulse_shape_emits_class(self):
        html = self.render({"character": "robot", "label": "Test", "shapes": [
            {"kind": "circle", "cx": 50, "cy": 50, "r": 3, "fill": "#ff6b6b",
             "anim": "pulse"}]})
        self.assertIn('class="sc-pulse"', html)

    def test_anim_and_moves_compose_on_one_shape(self):
        # The looping motion and the slider keyframes must not fight: the
        # stream rides on a wrapper around the shape, the keyframes on the
        # shape itself, so both survive in the output.
        html = self.render({"character": "robot", "label": "Test", "shapes": [
            {"kind": "circle", "cx": 50, "cy": 50, "r": 3, "fill": "#7fd4ff",
             "anim": "stream", "speed": 1.2, "delay": -0.3,
             "moves": [{"t": 0, "y": 0}, {"t": 0.5, "y": 10}, {"t": 1, "y": 0}]}]})
        self.assertIn('<g class="sc-stream"', html)
        self.assertIn("data-moves=", html)
        self.assertIn('"y": 10', html)

    def test_fill_keyframe_rides_in_data_moves_and_is_not_grounded(self):
        # A light that turns red as the slider rises: the fill lives in the
        # keyframes, the script applies it, and the checker never asks the
        # article for a colour — the board passes with no red in the text.
        data = {"character": "robot", "label": "Test", "shapes": [
            {"kind": "circle", "cx": 50, "cy": 50, "r": 3, "fill": "#7fd4ff",
             "moves": [{"t": 0}, {"t": 0.5, "fill": "#ff6b6b"}]}]}
        self.assertEqual(storyboard.check(self.board(data), self.article()), [])
        html = self.render(data)
        self.assertIn('"fill": "#ff6b6b"', html)
        self.assertIn("a.el.style.fill", html)

    def test_no_shape_cap(self):
        shapes = [{"kind": "circle", "cx": i, "cy": 10, "r": 2,
                   "fill": "#7fd4ff"} for i in range(60)]
        self.assertEqual(
            storyboard.check(self.board({"character": "robot", "label": "Test",
                                         "shapes": shapes}), self.article()), [])

    def test_group_anim_rides_on_an_inner_group(self):
        # The animation must not replace the group's placement transform:
        # it rides on an inner group while the outer group keeps the
        # translate, so a wobbling router stays where it was drawn.
        html = self.render({"character": "robot", "label": "Test", "shapes": [
            {"kind": "group", "x": 310, "y": 110, "anim": "wobble",
             "children": [{"kind": "rect", "x": 0, "y": 0, "width": 10,
                           "height": 10, "fill": "#2b313c"}]}]})
        self.assertIn('<g class="sc-wobble">', html)
        self.assertIn("transform:translate(310px, 110px)", html)

    def test_group_anim_and_moves_compose(self):
        html = self.render({"character": "robot", "label": "Test", "shapes": [
            {"kind": "group", "x": 10, "y": 10, "anim": "wobble",
             "moves": [{"t": 0}, {"t": 1, "x": 20}],
             "children": [{"kind": "rect", "x": 0, "y": 0, "width": 10,
                           "height": 10, "fill": "#2b313c"}]}]})
        self.assertIn("data-moves", html)
        self.assertIn('<g class="sc-wobble">', html)


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
