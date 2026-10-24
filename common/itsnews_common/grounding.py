"""Check that a storyboard only says what its article says.

The agent picks templates and rewrites for brevity, so wording may change,
but facts may not. Two things are checked mechanically, because they are
where invented content hurts most and where a check can be exact:

- Numbers. Every number a reader will see (in text or as a chart value)
  must appear in the article. "3,200" matches "3200"; spelled-out numbers
  up to twenty, the tens, "hundred", "thousand" and "dozen" count too.
- Quotes. A field marked "x-verbatim" in its template schema must appear in
  the article word for word. "..." marks a cut; each piece must match, in order.

Fields marked "x-ungrounded" (map coordinates, zoom scope) are general
knowledge, not news facts, and are skipped.
"""
from __future__ import annotations

import re
from typing import Any

from .article import Article

NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_URL = re.compile(r"https?://\S+")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_EMPHASIS = re.compile(r"[*_`]+")
_DASHES = re.compile(r"[‐-―−]")
_SPACE = re.compile(r"\s+")
_QUOTES = str.maketrans({
    "“": '"', "”": '"', "„": '"', "‟": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
})
_CUT = re.compile(r"\.\.\.|…|\[[^\]]*\]")

_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "dozen": 12,
}
_WORD = re.compile(r"\b(" + "|".join(_WORDS) + r")\b", re.IGNORECASE)


def plain(text: str) -> str:
    """Markdown to comparable plain text: no URLs or markup, one kind of quote and dash."""
    text = _LINK.sub(r"\1", text)
    text = _URL.sub(" ", text)
    text = _EMPHASIS.sub("", text)
    text = _DASHES.sub("-", text.translate(_QUOTES))
    return _SPACE.sub(" ", text).strip()


def numbers_in(text: str) -> list[str]:
    return NUMBER.findall(text)


def _value(token: str) -> float:
    return round(float(token.replace(",", "")), 9)


class Source:
    """The article, prepared for lookups."""

    def __init__(self, article: Article):
        self.text = plain(article.source_text)
        self.lower = self.text.lower()
        self.numbers = {_value(t) for t in numbers_in(self.text)}
        self.numbers |= {float(_WORDS[w.lower()]) for w in _WORD.findall(self.text)}

    def has_number(self, value: float) -> bool:
        return round(abs(value), 9) in self.numbers

    def has_quote(self, quote: str) -> bool:
        text = plain(quote).strip("\"' ")
        pos = 0
        for piece in _CUT.split(text):
            piece = piece.strip(" ,.;:!?\"'").lower()
            if not piece:
                continue
            found = self.lower.find(piece, pos)
            if found < 0:
                return False
            pos = found + len(piece)
        return True


def check(storyboard: dict, article: Article, templates: dict) -> list[str]:
    """Return one message per unsupported number or misquote."""
    source = Source(article)
    errors: list[str] = []

    def text(value: Any, path: str) -> None:
        if not isinstance(value, str):
            return
        for token in numbers_in(plain(value)):
            if not source.has_number(_value(token)):
                errors.append(
                    f"{path}: the number {token} is not in the article. "
                    "Show only numbers the article states, written the way it writes them."
                )

    def walk(value: Any, schema: dict, path: str) -> None:
        if schema.get("x-ungrounded"):
            return
        if schema.get("x-verbatim") and isinstance(value, str):
            if not source.has_quote(value):
                errors.append(
                    f"{path}: not found word for word in the article. Copy the quote "
                    "exactly; mark any cut with '...'."
                )
            return
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            if not source.has_number(value):
                errors.append(
                    f"{path}: {value} is not in the article. Chart values must be numbers "
                    "the article states (for \"3.2 million\", use 3.2 and put \"million\" in the unit)."
                )
        elif isinstance(value, str):
            text(value, path)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, schema.get("items", {}), f"{path}[{i}]")
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(item, schema.get("properties", {}).get(key, {}), f"{path}.{key}")

    headline = storyboard.get("headline")
    if isinstance(headline, dict):
        for key in ("title", "dek"):
            text(headline.get(key), f"$.headline.{key}")
    text(storyboard.get("bottom_line"), "$.bottom_line")

    scenes = storyboard.get("scenes")
    for i, scene in enumerate(scenes if isinstance(scenes, list) else []):
        if not isinstance(scene, dict):
            continue
        text(scene.get("question"), f"$.scenes[{i}].question")
        template = templates.get(scene.get("template"))
        if template is not None:
            walk(scene.get("data"), template.schema, f"$.scenes[{i}].data")
    return errors
