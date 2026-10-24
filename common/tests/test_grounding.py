"""Grounding: a storyboard may only show figures and quotes from its article."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from itsnews_common import article, grounding

ARTICLE = article.parse("""---
title: Test story
url: https://example.com/2031/archive/777
published: 2026-03-14
---
# Test story

The council voted 7-4 on Tuesday. The lanes cost $2.3 million and carry
3,400 trips a day, three times the old count. Spending fell 3% at restaurants.

"The numbers made the decision for us," said the mayor. "Fewer people are
getting hurt, and *more* people are coming downtown."

Read [the report](https://example.com/report-555) for details.
""")
TEXT = {"type": "string"}
# Grounding reads only each template's schema; these mirror the shapes the
# approaches use: free text, chart values, general knowledge, quotes.
TEMPLATES = {
    "info-board": SimpleNamespace(schema={"properties": {"tiles": {"items": {"properties": {
        "label": TEXT, "value": TEXT}}}}}),
    "bar-chart": SimpleNamespace(schema={"properties": {"bars": {"items": {"properties": {
        "label": TEXT, "value": {"type": "number"}}}}}}),
    "map": SimpleNamespace(schema={"properties": {
        "places": {"items": {"properties": {
            "name": TEXT,
            "lat": {"type": "number", "x-ungrounded": True},
            "lng": {"type": "number", "x-ungrounded": True}}}},
        "scope": {"type": "string", "x-ungrounded": True}}}),
    "quote": SimpleNamespace(schema={"properties": {
        "text": {"type": "string", "x-verbatim": True}, "speaker": TEXT}}),
}


def board(*values: str) -> dict:
    return {
        "headline": {"title": "t", "dek": "d", "topic": "local"},
        "scenes": [{
            "template": "info-board",
            "question": "What happened?",
            "data": {"tiles": [{"label": "L", "value": v} for v in values]},
        }],
    }


def check(storyboard: dict) -> list[str]:
    return grounding.check(storyboard, ARTICLE, TEMPLATES)


class NumberTests(unittest.TestCase):
    def test_numbers_from_the_article_pass(self):
        self.assertEqual(check(board("7-4", "$2.3 million", "3,400 a day", "-3%")), [])

    def test_thousands_separators_do_not_matter(self):
        self.assertEqual(check(board("3400 trips")), [])

    def test_spelled_out_numbers_count(self):
        # The article says "three times"; 3 is grounded by the word.
        self.assertEqual(check(board("3 times the old count")), [])

    def test_invented_number_is_reported(self):
        errors = check(board("Up 183%"))
        self.assertEqual(len(errors), 1)
        self.assertIn("$.scenes[0].data.tiles[0].value: the number 183", errors[0])

    def test_digits_inside_urls_do_not_ground_anything(self):
        self.assertEqual(len(check(board("777 riders"))), 1)
        self.assertEqual(len(check(board("555 riders"))), 1)

    def test_front_matter_counts_as_source(self):
        self.assertEqual(check(board("2026-03-14")), [])

    def test_headline_and_question_are_checked_too(self):
        sb = board("7-4")
        sb["headline"]["dek"] = "A 12-hour debate"
        sb["scenes"][0]["question"] = "Why 99 lanes?"
        paths = [e.split(":")[0] for e in check(sb)]
        self.assertEqual(paths, ["$.headline.dek", "$.scenes[0].question"])

    def test_chart_values_must_be_in_the_article(self):
        sb = board("x")
        sb["scenes"][0] = {"template": "bar-chart", "question": "Q", "data": {"bars": [
            {"label": "Restaurants", "value": -3},
            {"label": "Made up", "value": 4.5},
        ]}}
        errors = check(sb)
        self.assertEqual(len(errors), 1)
        self.assertIn("bars[1].value: 4.5 is not in the article", errors[0])

    def test_map_coordinates_are_exempt(self):
        sb = board("x")
        sb["scenes"][0] = {"template": "map", "question": "Where?", "data": {
            "places": [{"name": "Somewhere", "lat": 48.21, "lng": 16.37}], "scope": "city",
        }}
        self.assertEqual(check(sb), [])


class QuoteTests(unittest.TestCase):
    def quote(self, text: str) -> list[str]:
        sb = board("x")
        sb["scenes"][0] = {"template": "quote", "question": "Q",
                           "data": {"text": text, "speaker": "The mayor"}}
        return check(sb)

    def test_exact_quote_passes_despite_markdown_and_curly_quotes(self):
        self.assertEqual(self.quote("“Fewer people are getting hurt, and more people "
                                    "are coming downtown.”"), [])

    def test_cuts_marked_with_ellipsis_pass_in_order(self):
        self.assertEqual(self.quote("The numbers made the decision for us... Fewer "
                                    "people are getting hurt"), [])
        self.assertEqual(len(self.quote("Fewer people are getting hurt... The numbers "
                                        "made the decision for us")), 1)

    def test_paraphrase_fails(self):
        errors = self.quote("The data made the choice for us")
        self.assertEqual(len(errors), 1)
        self.assertIn("word for word", errors[0])


if __name__ == "__main__":
    unittest.main()
