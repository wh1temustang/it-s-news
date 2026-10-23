"""Read a news article in Markdown.

An article is a .md file with optional front matter:

    ---
    title: Night train to link Vienna and Barcelona from April
    source: The Example Times
    url: https://example.com/night-train
    published: 2026-03-14
    fictional: true
    ---
    # Headline
    Body text...

Front matter is plain `key: value` lines (no nesting, no lists), so no YAML
library is needed. Every key is optional. The renderer credits `source`,
links `url` and shows `published`; `fictional: true` puts a "not real news"
banner on the page, which every sample article in this repo uses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_HEADING = re.compile(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class Article:
    body: str
    meta: dict[str, str] = field(default_factory=dict)
    path: Path | None = None

    @property
    def title(self) -> str:
        if self.meta.get("title"):
            return self.meta["title"]
        match = _HEADING.search(self.body)
        return match.group(1) if match else ""

    @property
    def fictional(self) -> bool:
        return self.meta.get("fictional", "").lower() in {"true", "yes", "1"}

    @property
    def url(self) -> str | None:
        url = self.meta.get("url", "")
        return url if url.startswith(("https://", "http://")) else None

    @property
    def source_text(self) -> str:
        """Everything a storyboard is allowed to draw facts from."""
        meta = "\n".join(f"{k}: {v}" for k, v in self.meta.items())
        return f"{meta}\n{self.body}"


def parse(text: str, path: Path | None = None) -> Article:
    text = text.replace("\r\n", "\n").lstrip("﻿")
    meta: dict[str, str] = {}
    match = _FRONT_MATTER.match(text)
    if match:
        for line in match.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip() and not line.startswith((" ", "\t", "#")):
                meta[key.strip().lower()] = value.strip().strip("\"'")
        text = text[match.end():]
    return Article(body=text.strip() + "\n", meta=meta, path=path)


def load(path: str | Path) -> Article:
    path = Path(path)
    return parse(path.read_text(encoding="utf-8"), path)
