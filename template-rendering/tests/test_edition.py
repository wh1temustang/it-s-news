"""Editions, labels in other languages, and multi-outlet credits."""
from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from template_rendering import article, cli, edition, storyboard
from template_rendering.catalog import PACKAGE_DIR, load_templates
from template_rendering.labels import Labels, LabelsError
from template_rendering.render import render_page

EXAMPLES = PACKAGE_DIR.parent / "examples"
MANIFEST = EXAMPLES / "edition.json"
NIGHT_TRAIN = (article.load(EXAMPLES / "night-train.md"),
               storyboard.load(EXAMPLES / "night-train.storyboard.json"))


def one_story_edition(**story) -> edition.Edition:
    a, sb = NIGHT_TRAIN
    return edition.Edition("Today", [edition.Section("travel", "Travel",
                                                    [edition.Story(a, sb, **story)])])


class ExampleEditionTests(unittest.TestCase):
    def setUp(self):
        self.edition = edition.load(MANIFEST)

    def test_it_loads_and_passes_the_check(self):
        self.assertEqual([s.id for s in self.edition.sections], ["travel", "cities"])
        self.assertEqual(edition.check(self.edition), [])

    def test_committed_page_matches_a_fresh_render(self):
        page = MANIFEST.with_suffix(".html")
        self.assertTrue(page.is_file(), f"{page.name} is missing: render it (see AGENTS.md)")
        self.assertEqual(page.read_text(encoding="utf-8"), edition.render(self.edition),
                         f"{page.name} is stale: render it again (see AGENTS.md)")

    def test_page_loads_nothing_from_elsewhere(self):
        html = edition.render(self.edition)
        self.assertIsNone(re.search(r"<(script|link|img|iframe)\b", html))
        self.assertIsNone(re.search(r"url\((?!#)", html))

    def test_ids_are_unique_and_every_section_is_linked(self):
        html = edition.render(self.edition)
        ids = re.findall(r'\bid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)), ids)
        for section in self.edition.sections:
            self.assertIn(f'href="#{section.id}"', html)
            self.assertIn(f'id="{section.id}"', html)
        self.assertIn('id="story-2-q1"', html)
        # The line chart's gradient is referenced by id, so it must be unique too.
        self.assertEqual(len(re.findall(r'id="lc-fill-', html)), 1)

    def test_each_story_keeps_its_own_topic_and_template_css_appears_once(self):
        html = edition.render(self.edition)
        self.assertIn('class="story-card" id="story-1" data-topic="world"', html)
        self.assertIn('class="story-card" id="story-2" data-topic="local"', html)
        self.assertEqual(html.count(load_templates()["info-board"].css), 1)


class CheckTests(unittest.TestCase):
    def test_story_problems_name_the_section_story_and_file(self):
        a, sb = NIGHT_TRAIN
        bad = {**sb, "scenes": [{"template": "big-number", "question": "Q",
                                 "data": {"numbers": [{"value": "999", "label": "x"}]}}]}
        ed = edition.Edition("T", [edition.Section("travel", "Travel", [edition.Story(a, bad)])])
        errors = edition.check(ed)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].startswith("travel, story 1 (night-train.md): $.scenes[0]"))

    def test_section_ids_must_be_usable_and_unique(self):
        a, sb = NIGHT_TRAIN
        story = edition.Story(a, sb)
        ed = edition.Edition("T", [edition.Section("World News", "W", [story]),
                                   edition.Section("x", "X", [story]),
                                   edition.Section("x", "X again", [story]),
                                   edition.Section("empty", "E")])
        errors = " | ".join(edition.check(ed))
        self.assertIn("'World News': use lowercase letters", errors)
        self.assertIn("'x': another section has the same id", errors)
        self.assertIn("'empty' has no stories", errors)

    def test_manifest_problems_are_reported_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "e.json"
            path.write_text(json.dumps({"title": "T", "sections": [{"id": "a", "title": "A",
                "stories": [{"article": "missing.md", "storyboard": "missing.json"}]}]}))
            with self.assertRaises(edition.EditionError) as caught:
                edition.load(path)
            self.assertIn("a, story 1 (missing.md): can't read", caught.exception.errors[0])

            path.write_text(json.dumps({"title": "T", "sections": [], "colour": "red"}))
            with self.assertRaises(edition.EditionError) as caught:
                edition.load(path)
            errors = " | ".join(caught.exception.errors)
            self.assertIn("needs at least 1", errors)
            self.assertIn("unknown field 'colour'", errors)


class HostMarkupTests(unittest.TestCase):
    def test_host_markup_goes_in_as_is_and_story_text_is_still_escaped(self):
        a, sb = NIGHT_TRAIN
        sb = {**sb, "headline": {**sb["headline"], "title": "<b>Night</b> train"}}
        ed = edition.Edition("T", [edition.Section("travel", "Travel",
                                                   [edition.Story(a, sb, extra='<form id="fb-1"></form>')])])
        html = edition.render(ed, head="<style>.fb{}</style>", foot="<script>boot()</script>")
        self.assertIn('<form id="fb-1"></form>\n</article>', html)
        self.assertIn("<style>.fb{}</style>\n</head>", html)
        self.assertIn("<script>boot()</script>\n</body>", html)
        self.assertIn("&lt;b&gt;Night&lt;/b&gt; train", html)


class LabelTests(unittest.TestCase):
    T = Labels({"lang": "fr", "bottom_line": "L'essentiel", "topic.world": "Monde",
                "template.timeline": "Chronologie", "timeline.now": "Aujourd'hui",
                "sources": "Sources", "label_sep": " : "})

    def test_labels_replace_the_page_words(self):
        a, sb = NIGHT_TRAIN
        html = render_page({**sb, "bottom_line": "Book early."}, a, labels=self.T)
        self.assertIn('<html lang="fr">', html)
        self.assertIn('<p class="kicker">Monde</p>', html)
        self.assertIn("</span> Chronologie</p>", html)
        self.assertIn('<span class="tl-tag">Aujourd&#39;hui</span>', html)
        self.assertIn("<h2>L&#39;essentiel</h2>", html)
        # Keys left out stay English.
        self.assertIn("Map data: Natural Earth", html)

    def test_labels_reach_editions(self):
        html = edition.render(one_story_edition(), labels=self.T)
        self.assertIn('<html lang="fr">', html)
        self.assertIn("<h3>Night train", html)
        self.assertIn('<h4 id="story-1-q1">', html)

    def test_unknown_or_non_text_labels_are_rejected(self):
        with self.assertRaisesRegex(LabelsError, "unknown label 'bottomline'"):
            Labels({"bottomline": "x"})
        with self.assertRaisesRegex(LabelsError, "must be a string"):
            Labels({"lang": 3})

    def test_label_placeholders_escape_their_values(self):
        self.assertEqual(Labels()("read_more_at", source="<A&B>"),
                         "Read the full article at &lt;A&amp;B&gt;")


class SourcesTests(unittest.TestCase):
    def test_sources_credit_every_outlet(self):
        a = article.parse(
            "---\nsources: [Daily Example / Ana Ruiz](https://example.com/a)、"
            "[Wire](javascript:alert(1)), [Radio](https://example.com/b)\n"
            "published: 2026-03-14\n---\nBody\n")
        self.assertEqual(a.sources, [("Daily Example / Ana Ruiz", "https://example.com/a"),
                                     ("Wire", None), ("Radio", "https://example.com/b")])
        _, sb = NIGHT_TRAIN
        html = render_page(sb, a)
        self.assertIn('<p class="byline">Sources: <a href="https://example.com/a" '
                      'rel="noopener noreferrer">Daily Example / Ana Ruiz</a>, Wire, '
                      '<a href="https://example.com/b" rel="noopener noreferrer">Radio</a>'
                      ' · <span>2026-03-14</span></p>', html)
        self.assertNotIn("javascript:", html)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_edition_command_writes_the_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            labels.write_text('{"lang": "fr"}')
            target = Path(tmp) / "edition.html"
            code, out, _ = self.run_cli("edition", str(MANIFEST), "-o", str(target),
                                        "--labels", str(labels))
            self.assertEqual(code, 0, out)
            self.assertIn('<html lang="fr">', target.read_text(encoding="utf-8"))

    def test_a_bad_labels_file_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels = Path(tmp) / "labels.json"
            labels.write_text('{"lang": "fr", "colour": "red"}')
            code, _, err = self.run_cli("edition", str(MANIFEST), "-o", str(Path(tmp) / "e.html"),
                                        "--labels", str(labels))
            self.assertEqual(code, 1)
            self.assertIn("unknown label 'colour'", err)


if __name__ == "__main__":
    unittest.main()
