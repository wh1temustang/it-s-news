"""The schema validator: what it accepts, and that its messages say what to fix."""
from __future__ import annotations

import unittest

from itsnews_common.schema import validate

TILE = {
    "type": "object",
    "required": ["label"],
    "additionalProperties": False,
    "properties": {
        "label": {"type": "string", "minLength": 1, "maxLength": 10},
        "tone": {"type": "string", "enum": ["good", "bad"]},
        "count": {"type": "number", "minimum": 0, "maximum": 5},
        "link": {"type": "string", "format": "uri"},
        "emoji": {"type": "string", "pattern": "^\\W+$"},
    },
}
BOARD = {"type": "object", "properties": {
    "tiles": {"type": "array", "minItems": 2, "maxItems": 3, "items": TILE},
}}


class ValidateTests(unittest.TestCase):
    def test_valid_data_has_no_errors(self):
        data = {"tiles": [{"label": "Cost", "tone": "good", "count": 2}, {"label": "Date"}]}
        self.assertEqual(validate(data, BOARD), [])

    def test_wrong_type_names_the_path(self):
        errors = validate({"tiles": [{"label": 3}, {"label": "x"}]}, BOARD)
        self.assertEqual(errors, ["$.tiles[0].label: expected string, got number"])

    def test_too_long_says_by_how_much(self):
        errors = validate({"label": "x" * 12}, TILE)
        self.assertEqual(errors, ["$.label: 12 characters, the limit is 10. Shorten it."])

    def test_blank_string_counts_as_empty(self):
        self.assertEqual(validate({"label": "   "}, TILE), ["$.label: must not be empty"])

    def test_missing_and_unknown_fields(self):
        errors = validate({"colour": "red"}, TILE)
        self.assertIn("$: missing required field 'label'", errors)
        self.assertIn("$: unknown field 'colour'. Allowed: label, tone, count, link, emoji",
                      errors)

    def test_enum_lists_the_allowed_values(self):
        errors = validate({"label": "x", "tone": "great"}, TILE)
        self.assertEqual(errors, ["$.tone: 'great' is not allowed. Use one of: good, bad"])

    def test_item_counts(self):
        self.assertIn("needs at least 2", validate({"tiles": [{"label": "a"}]}, BOARD)[0])
        too_many = validate({"tiles": [{"label": "a"}] * 4}, BOARD)
        self.assertIn("the limit is 3", too_many[0])

    def test_number_bounds_and_booleans_are_not_numbers(self):
        self.assertIn("above the maximum", validate({"label": "x", "count": 9}, TILE)[0])
        self.assertEqual(validate({"label": "x", "count": True}, TILE),
                         ["$.count: expected number, got boolean"])

    def test_uri_must_be_http(self):
        self.assertEqual(validate({"label": "x", "link": "javascript:alert(1)"}, TILE),
                         ["$.link: must be an http(s) URL"])
        self.assertEqual(validate({"label": "x", "link": "https://example.com"}, TILE), [])

    def test_pattern_is_searched_for(self):
        self.assertEqual(validate({"label": "x", "emoji": "🚆✨"}, TILE), [])
        self.assertEqual(validate({"label": "x", "emoji": "42"}, TILE),
                         ["$.emoji: '42' doesn't match the pattern ^\\W+$"])


if __name__ == "__main__":
    unittest.main()
