"""A rendered page must not reach the network: the scan that proves it.

Kit pages are self-contained by design (see kit.py): inline CSS, no
external fonts, scripts or images, so a page works offline and leaks
nothing about its readers. Until now that was a convention, spot-checked
on the example pages by a regex in testing.py. This module makes it a
guarantee the command line enforces on every page it writes (see cli.py),
so a template change — or a compromised dependency slipping markup into
the output — fails the render instead of shipping a page that phones
home. `python -m <package> scan PAGE` checks a page from anywhere.

What counts as reaching the network:

- a resource a browser loads on its own: `src`, `srcset`, `poster`,
  `data`, form `action` and friends, on any element, plus `href` on the
  elements that load through it (`link`, `base`, SVG `image` and `use`).
  Fragment references (`#id`) and `data:` URIs are self-contained, so
  they pass; anything else — absolute, protocol-relative or relative —
  is a load from somewhere else.
- a `<meta http-equiv="refresh">` that sends the reader to a URL.
- script that calls a network API: `fetch()`, `XMLHttpRequest`,
  `WebSocket`, `EventSource`, `navigator.sendBeacon`, dynamic `import()`.
- CSS that loads: `@import`, or `url(...)` that isn't a fragment or
  `data:` URI, in a style element or a `style` attribute.

Links a reader may choose to follow (`<a href>`) are not loads, and
neither is an `xmlns` identifier: a namespace name is never fetched.

Standard library only, like the rest of this package.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

# Attributes that make a browser fetch a resource, on any element.
_LOAD_ATTRS = {"src", "srcset", "poster", "data", "action", "formaction", "background"}
# Elements that load through href rather than navigate with it.
_HREF_LOADERS = {"link", "base", "image", "use"}
# Script that reaches the network, wherever it sits on the page.
_NETWORK_APIS = ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
                 "sendBeacon", "import(")
_CSS_URL = re.compile(r"url\(\s*['\"]?([^)'\"]*)")
_REFRESH_URL = re.compile(r"url\s*=", re.IGNORECASE)


def _loads(value: str) -> bool:
    """Would this attribute value make the browser go somewhere else?"""
    value = value.strip()
    return bool(value) and not value.startswith(("#", "data:"))


class _Scanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.findings: list[str] = []
        self._text_tag: str | None = None  # inside <script> or <style>

    def _add(self, what: str) -> None:
        line = self.getpos()[0]
        self.findings.append(
            f"line {line}: {what} reaches the network; a page must be "
            "self-contained, so inline it or remove it")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._text_tag = tag
        values = dict(attrs)
        for name, value in attrs:
            if value is None:
                continue
            if name in _LOAD_ATTRS and _loads(value):
                self._add(f"<{tag} {name}=\"{value}\">")
            elif name == "href" and tag in _HREF_LOADERS and _loads(value):
                self._add(f"<{tag} href=\"{value}\">")
            elif name == "style":
                self._css(value)
            elif name.startswith("on"):
                self._script(value)
        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            if _REFRESH_URL.search(values.get("content", "")):
                self._add("<meta http-equiv=\"refresh\"> redirecting to a URL")

    def handle_endtag(self, tag: str) -> None:
        if tag == self._text_tag:
            self._text_tag = None

    def handle_data(self, data: str) -> None:
        if self._text_tag == "script":
            self._script(data)
        elif self._text_tag == "style":
            self._css(data)

    def _script(self, text: str) -> None:
        for api in _NETWORK_APIS:
            if api in text:
                self._add(f"script using {api[:-1] if api.endswith('(') else api}()")

    def _css(self, text: str) -> None:
        if "@import" in text:
            self._add("CSS with @import")
        for match in _CSS_URL.finditer(text):
            if _loads(match.group(1)):
                self._add(f"CSS url({match.group(1)})")


def network_references(html: str) -> list[str]:
    """One message per way the page would reach the network; [] if none."""
    scanner = _Scanner()
    scanner.feed(html)
    scanner.close()
    return scanner.findings
