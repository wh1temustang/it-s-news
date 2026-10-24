"""The template kit, editions, labels and the command line, on a one-template fixture kit."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from itsnews_common import article, cli, edition, labels, storyboard, testing
from itsnews_common.kit import Kit

FIXTURE = Path(__file__).resolve().parent / "fixture"
ARTICLE = article.parse("""---
title: Pier reopens
source: Example Daily
url: https://example.com/pier
fictional: true
---
# Pier reopens

The pier reopened on Friday after 18 months of repairs. "It feels like summer
again," said the harbour master.
""")
GOOD = {
    "headline": {"title": "Pier reopens", "dek": "After 18 months of repairs.", "topic": "local"},
    "scenes": [{"template": "note", "question": "What happened?",
                "data": {"fact": "Reopened on Friday", "quote": "It feels like summer again",
                         "emoji": "🎡"}}],
}


class FixtureLabels(labels.Labels):
    DEFAULTS = {**labels.DEFAULTS, "topic.local": "Around here", "note.extra": "Extra"}


def shout(template_id: str, data: dict) -> dict:
    return {**data, "shout": True}


def no_fridays(storyboard: dict, art: article.Article, templates: dict) -> list[str]:
    title = storyboard.get("headline", {}).get("title", "")
    return ["$.headline.title: no piers"] if "Pier" in title else []


KIT = Kit("fixture", FIXTURE / "kit", labels=FixtureLabels)


class FixtureKitTests(testing.KitTests, unittest.TestCase):
    """The shared conformance checks pass on a minimal kit."""

    kit = KIT


class CheckTests(unittest.TestCase):
    def test_a_grounded_storyboard_is_ready(self):
        self.assertEqual(KIT.check(GOOD, ARTICLE), [])

    def test_shape_grounding_and_patterns_are_all_reported(self):
        bad = json.loads(json.dumps(GOOD))
        bad["scenes"][0]["data"].update(fact="Closed for 19 months", emoji="1")
        bad["scenes"].append({"template": "chart", "question": "Q", "data": {}})
        errors = " | ".join(KIT.check(bad, ARTICLE))
        self.assertIn("unknown template 'chart'", errors)
        self.assertIn("doesn't match the pattern", errors)
        self.assertIn("the number 19 is not in the article", errors)

    def test_a_kits_own_rules_run_after_the_shared_checks(self):
        kit = Kit("fixture", FIXTURE / "kit", rules=no_fridays)
        self.assertEqual(kit.check(GOOD, ARTICLE), ["$.headline.title: no piers"])

    def test_storyboard_check_needs_no_kit(self):
        schema = KIT.storyboard_schema()
        self.assertEqual(storyboard.check(GOOD, ARTICLE, schema, KIT.load_templates()), [])


class RenderTests(unittest.TestCase):
    def test_page_uses_the_kits_labels_and_marks_fiction(self):
        html = KIT.render_page(GOOD, ARTICLE)
        self.assertIn('<p class="kicker">Around here</p>', html)
        self.assertIn(labels.DEFAULTS["fictional"], html)
        self.assertIn("checked against the article", html)
        self.assertIn(".note-fact", html)

    def test_prepare_hook_shapes_what_the_template_draws(self):
        kit = Kit("fixture", FIXTURE / "kit", prepare=shout)
        self.assertIn("Reopened on Friday!</p>", kit.render_page(GOOD, ARTICLE))
        self.assertIn("Reopened on Friday</p>", KIT.render_page(GOOD, ARTICLE))

    def test_edition_ids_and_host_markup(self):
        story = edition.Story(ARTICLE, GOOD, extra='<form id="fb"></form>')
        issue = edition.Edition("Today", [edition.Section("local", "Local", [story, story])])
        self.assertEqual(KIT.check_edition(issue), [])
        html = KIT.render_edition(issue, head="<style>.h{}</style>", document=False)
        self.assertIn('id="story-2-q1"', html)
        self.assertIn('<form id="fb"></form>', html)
        self.assertIn("<style>.h{}</style>", html)
        self.assertNotIn("<html", html)


class EditionTests(unittest.TestCase):
    def test_section_problems_and_story_problems_are_located(self):
        story = edition.Story(ARTICLE, GOOD)
        issue = edition.Edition("T", [edition.Section("Bad Id", "B", [story]),
                                      edition.Section("x", "X", [story]),
                                      edition.Section("x", "X again", [story]),
                                      edition.Section("empty", "E")])
        errors = " | ".join(edition.check(issue, lambda sb, a: ["$.headline: nope"]))
        self.assertIn("'Bad Id': use lowercase letters", errors)
        self.assertIn("'x': another section has the same id", errors)
        self.assertIn("'empty' has no stories", errors)
        self.assertIn("x, story 1: $.headline: nope", errors)

    def test_manifest_loads_its_files_relative_to_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.md").write_text("# A\n")
            (tmp / "a.json").write_text("```json\n" + json.dumps(GOOD) + "\n```")
            (tmp / "e.json").write_text(json.dumps({"title": "T", "sections": [
                {"id": "a", "title": "A", "stories": [{"article": "a.md", "storyboard": "a.json"}]},
                {"id": "b", "title": "B", "stories": [{"article": "gone.md", "storyboard": "a.json"}]},
            ]}))
            with self.assertRaises(edition.EditionError) as caught:
                edition.load(tmp / "e.json")
            self.assertEqual(len(caught.exception.errors), 1)
            self.assertIn("b, story 1 (gone.md): can't read", caught.exception.errors[0])


class LabelTests(unittest.TestCase):
    def test_a_kits_labels_extend_the_shared_ones(self):
        t = FixtureLabels({"lang": "fr", "note.extra": "En plus"})
        self.assertEqual(t("note.extra"), "En plus")
        self.assertEqual(t("bottom_line"), "Bottom line")
        with self.assertRaisesRegex(labels.LabelsError, "unknown label 'note.extra'"):
            labels.Labels({"note.extra": "x"})

    def test_load_labels_builds_the_kits_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "l.json"
            path.write_text('{"note.extra": "Mehr"}')
            self.assertEqual(labels.load_labels(path, FixtureLabels)("note.extra"), "Mehr")


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(KIT, list(args))
        return code, out.getvalue(), err.getvalue()

    def test_prompt_check_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            md, sb = tmp / "pier.md", tmp / "pier.storyboard.json"
            md.write_text("---\nfictional: true\n---\n" + ARTICLE.body)
            sb.write_text(json.dumps(GOOD))
            code, out, _ = self.run_cli("prompt", str(md))
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("# Fixture prompt"))
            self.assertIn("Template `note`", out)
            self.assertEqual(self.run_cli("check", str(md), str(sb))[0], 0)
            code, _, _ = self.run_cli("render", str(md), str(sb), "-o", str(tmp / "p.html"))
            self.assertEqual(code, 0)
            self.assertIn("Pier reopens", (tmp / "p.html").read_text(encoding="utf-8"))

    def test_a_failed_check_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            md, sb = tmp / "pier.md", tmp / "bad.json"
            md.write_text(ARTICLE.body)
            sb.write_text(json.dumps({**GOOD, "bottom_line": "Up 99%"}))
            code, _, err = self.run_cli("render", str(md), str(sb), "-o", str(tmp / "p.html"))
            self.assertEqual(code, 1)
            self.assertIn("the number 99 is not in the article", err)
            self.assertFalse((tmp / "p.html").exists())


if __name__ == "__main__":
    unittest.main()
