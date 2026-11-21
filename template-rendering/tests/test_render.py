"""End to end: examples check clean, render the same every time, and stay self-contained."""
from __future__ import annotations

import io
import re
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


class GameTests(unittest.TestCase):
    def article(self, body=None):
        if body is None:
            body = ("Fallowfield saw 42 cm of snow in 24 hours. "
                    "The old record was 31 cm.")
        return article.parse(f"---\nsource: Test\n---\n{body}\n")

    def board(self, data, title="T", dek="D", question="What happens?"):
        return {"headline": {"title": title, "dek": dek, "topic": "world"},
                "scenes": [{"template": "game", "question": question,
                            "data": data}]}

    def render(self, data, body=None):
        return render_page(self.board(data), self.article(body))

    def guess(self, **over):
        data = {"kind": "guess-number", "label": "Snow in 24 hours",
                "unit": " cm", "unit_after": True,
                "answer": 42, "min": 0, "max": 60}
        data.update(over)
        return data

    def quiz(self, **over):
        data = {"kind": "quiz", "label": "The IPO price", "unit": "$",
                "unit_after": False,
                "options": [70, 78, 85], "correct": [70, 78]}
        data.update(over)
        return data

    def test_guess_number_renders_slider_reveal_and_retry(self):
        html = self.render(self.guess())
        self.assertIn('type="range"', html)
        self.assertIn('data-answer="42"', html)
        self.assertIn('data-msg-exact="Exact! The answer is {answer}."', html)
        self.assertIn(">Reveal<", html)
        self.assertIn('data-retry="Try again"', html)

    def test_guess_number_wiring_states_answer_and_closeness(self):
        # The reveal states the answer and how close the guess was: exact,
        # near (within 5% of the answer), or far, with the difference.
        # Then the slider locks and the button becomes a retry.
        html = self.render(self.guess())
        self.assertIn("Math.abs(ANSWER) * 0.05", html)
        self.assertIn("msgNearOver", html)
        self.assertIn("msgFarUnder", html)
        self.assertIn("slider.disabled = true", html)
        self.assertIn("btn.textContent = btn.dataset.retry", html)

    def test_quiz_renders_options_and_no_reset_button(self):
        # Three option buttons and nothing else clickable: once answered
        # the quiz stays answered, so no reset or replay button exists.
        html = self.render(self.quiz())
        self.assertEqual(html.count("<button"), 3)
        self.assertIn('data-correct="70,78"', html)
        self.assertIn('data-v="85"', html)
        self.assertNotIn("Try again", html)
        self.assertNotIn("Play again", html)
        self.assertNotIn('class="gm-reveal"', html)

    def test_quiz_wiring_marks_every_right_answer(self):
        # A question may have more than one right answer: a right pick
        # lights up every right option, a wrong pick marks itself red.
        html = self.render(self.quiz())
        self.assertIn("o.classList.add('gm-right')", html)
        self.assertIn("b.classList.add('gm-wrong')", html)
        self.assertIn("correct.indexOf", html)

    def test_anthropic_case_passes_the_checker(self):
        # The article states only the $70-78 range, so $70 and $78 are
        # both right answers and $85 is a distractor the article never
        # states — close enough to be a plausible guess.
        art = self.article("Anthropic priced its IPO at $70 to $78 a "
                           "share, pricing on Wednesday.")
        self.assertEqual(storyboard.check(self.board(self.quiz()), art), [])

    def test_distractor_in_the_article_fails(self):
        # A wrong option the article states is not a guess — it is a
        # fact the reader was told, so it cannot be the wrong answer.
        art = self.article("Anthropic priced its IPO at $70 to $78 a "
                           "share. Rivals had hoped for $85.")
        errors = storyboard.check(self.board(self.quiz()), art)
        self.assertTrue(any("85 is in the article" in e for e in errors),
                        errors)

    def test_distractor_too_far_fails(self):
        art = self.article("Anthropic priced its IPO at $70 to $78 a share.")
        errors = storyboard.check(
            self.board(self.quiz(options=[70, 78, 200])), art)
        self.assertTrue(any("200 is too far" in e for e in errors), errors)

    def test_correct_must_be_among_the_options(self):
        art = self.article("Anthropic priced its IPO at $70 to $78 a share.")
        errors = storyboard.check(
            self.board(self.quiz(options=[70, 85, 90], correct=[70, 78])),
            art)
        self.assertTrue(any("must also be an option" in e for e in errors),
                        errors)

    def test_correct_must_be_in_the_article(self):
        # The right answers are facts, so the grounding check applies to
        # them even though the options as a whole are exempt.
        art = self.article("Anthropic priced its IPO at $70 to $78 a share.")
        errors = storyboard.check(
            self.board(self.quiz(options=[70, 78, 99], correct=[70, 99])),
            art)
        self.assertTrue(any("99" in e for e in errors), errors)

    def test_guess_number_answer_must_be_in_the_article(self):
        errors = storyboard.check(self.board(self.guess(answer=50)),
                                  self.article())
        self.assertTrue(any("50" in e for e in errors), errors)

    def test_guess_number_range_must_bracket_the_answer(self):
        errors = storyboard.check(self.board(self.guess(max=30)),
                                  self.article())
        self.assertTrue(any("outside the slider's range" in e for e in errors),
                        errors)

    def test_missing_unit_after_fails_the_check(self):
        # The unit's place is data, not a guess: a game without
        # unit_after rendered "億美元750" instead of "750億美元".
        # The schema now requires it on both kinds, so the checker
        # must catch a missing flag.
        for data in (self.guess(), self.quiz()):
            del data["unit_after"]
            errors = storyboard.check(self.board(data), self.article())
            self.assertTrue(any("missing required field 'unit_after'" in e
                                for e in errors), errors)

    def test_chinese_unit_renders_after_the_number(self):
        # 億美元 goes after the number: the readout, the buttons and
        # the result all read "750億美元", never "億美元750".
        html = self.render(self.quiz(options=[1.2, 1.4, 1.5, 1.8],
                                     correct=[1.4, 1.5],
                                     unit="萬億美元", unit_after=True))
        self.assertIn("1.4萬億美元", html)
        self.assertNotIn("萬億美元1.4", html)
        html = self.render(self.guess(unit="億美元", unit_after=True))
        self.assertIn('data-unit-after="1"', html)
        self.assertIn('data-unit="億美元"', html)

    def test_dollar_renders_before_the_number(self):
        # $ goes before the number: "$78", not "78$".
        html = self.render(self.quiz())
        self.assertIn(">$78<", html)
        html = self.render(self.guess(unit="$", unit_after=False))
        self.assertIn('data-unit-after="0"', html)

    def test_large_numbers_get_thousands_separators(self):
        # The result reads "1,087億美元", like the scale after it shows —
        # not "1087億美元".
        html = self.render(self.quiz(options=[900, 1087, 1200],
                                     correct=[1087], unit="億美元",
                                     unit_after=True))
        self.assertIn("1,087億美元", html)
        self.assertIn('data-v="1087"', html)
        html = self.render(self.guess(unit="億美元", unit_after=True))
        self.assertIn("parts.join('.')", html)

    def test_guess_number_needs_answer_and_max(self):
        data = self.guess()
        del data["answer"], data["max"]
        errors = storyboard.check(self.board(data), self.article())
        self.assertTrue(any("answer: missing" in e for e in errors), errors)
        self.assertTrue(any("max: missing" in e for e in errors), errors)

    def test_quiz_needs_options_and_correct(self):
        data = self.quiz()
        del data["options"], data["correct"]
        errors = storyboard.check(self.board(data), self.article())
        self.assertTrue(any("options: missing" in e for e in errors), errors)
        self.assertTrue(any("correct: missing" in e for e in errors), errors)

    def test_spoiler_headline_fails(self):
        # The game is where the answer is first revealed: the headline
        # must not state it.
        errors = storyboard.check(
            self.board(self.guess(), title="Fallowfield gets 42 cm"),
            self.article())
        self.assertTrue(any("states the game's answer (42)" in e
                            for e in errors), errors)

    def test_two_games_on_one_page_fail(self):
        board = self.board(self.guess())
        board["scenes"].append({"template": "game",
                                "question": "What else?",
                                "data": self.quiz()})
        errors = storyboard.check(board, self.article())
        self.assertTrue(any("a second game" in e for e in errors), errors)


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
                           ' "scenes": [{"template": "list", "question": "Q",'
                           ' "data": {"rows": [{"label": "x", "value": "999"}]}}]}')
            target = Path(tmp) / "page.html"
            code, _, err = self.run_cli("render", str(md), str(bad), "-o", str(target))
            self.assertEqual(code, 1)
            self.assertIn("the number 999 is not in the article", err)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
