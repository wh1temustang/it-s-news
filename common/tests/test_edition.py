"""Editions: the manifest, and the animated page a story may carry."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from itsnews_common import article, edition
from itsnews_common.testing import external_loads

ARTICLE = """---
source: Example Wire
published: 2026-03-14
fictional: true
---

The ferry carried 1,200 passengers in June. "We sail at dawn," the captain said.
"""

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Ferry</title></head><body>
<script type="application/json" id="explainer">
{"headline": {"title": "The ferry", "topic": "local"},
 "scenes": [
   {"kind": "title", "rank": 1, "why": "Opens on the figure.",
    "beats": [{"do": "show", "title": "1,200 passengers in June"}]},
   {"kind": "end", "rank": 2,
    "beats": [{"do": "quote", "text": "We sail at dawn", "who": "the captain"}]}
 ]}
</script>
<script>/* the engine */</script>
</body></html>
"""

STORYBOARD = {"headline": {"title": "The ferry", "dek": "A busy June.", "topic": "local"},
              "scenes": []}


def no_story_problems(storyboard, article):
    return []


class AnimatedCheckTests(unittest.TestCase):
    def setUp(self):
        self.article = article.parse(ARTICLE)

    def test_a_grounded_page_passes(self):
        self.assertEqual(edition.check_animated(PAGE, self.article), [])

    def test_an_invented_number_is_caught(self):
        errors = edition.check_animated(PAGE.replace("1,200", "999"), self.article)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("999 is not in the article", errors[0])

    def test_a_misquote_is_caught(self):
        errors = edition.check_animated(PAGE.replace("We sail at dawn", "We sail at noon"),
                                        self.article)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("word for word", errors[0])

    def test_a_page_that_loads_from_the_network_is_refused(self):
        page = PAGE.replace("</head>", '<script src="https://example.com/x.js"></script></head>')
        errors = edition.check_animated(page, self.article)
        self.assertTrue(any("self-contained" in e for e in errors), errors)

    def test_a_page_without_a_script_is_refused(self):
        errors = edition.check_animated("<html><body>No script.</body></html>", self.article)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn('id="explainer"', errors[0])


class EmbedTests(unittest.TestCase):
    def test_a_srcdoc_iframe_loads_nothing_but_a_src_iframe_does(self):
        self.assertEqual(external_loads('<iframe srcdoc="<p>Story</p>"></iframe>'), [])
        self.assertNotEqual(external_loads('<iframe src="https://example.com/x"></iframe>'), [])


class ManifestTests(unittest.TestCase):
    def write_edition(self, tmp: str, story: dict) -> Path:
        root = Path(tmp)
        (root / "ferry.md").write_text(ARTICLE, encoding="utf-8")
        (root / "ferry.storyboard.json").write_text(json.dumps(STORYBOARD), encoding="utf-8")
        (root / "ferry.animated.html").write_text(PAGE, encoding="utf-8")
        manifest = {"title": "T", "sections": [{"id": "local", "title": "Local",
                                                 "stories": [story]}]}
        path = root / "edition.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_the_manifest_loads_the_animated_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_edition(tmp, {"article": "ferry.md",
                                            "storyboard": "ferry.storyboard.json",
                                            "animated": "ferry.animated.html"})
            ed = edition.load(path)
            self.assertEqual(ed.stories[0].animated, PAGE)
            self.assertEqual(edition.check(ed, no_story_problems), [])

    def test_a_missing_animated_page_is_a_load_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_edition(tmp, {"article": "ferry.md",
                                            "storyboard": "ferry.storyboard.json",
                                            "animated": "gone.html"})
            with self.assertRaises(edition.EditionError) as caught:
                edition.load(path)
            self.assertIn("can't read", caught.exception.errors[0])

    def test_a_story_without_animated_stays_templates_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_edition(tmp, {"article": "ferry.md",
                                            "storyboard": "ferry.storyboard.json"})
            ed = edition.load(path)
            self.assertEqual(ed.stories[0].animated, "")


if __name__ == "__main__":
    unittest.main()
