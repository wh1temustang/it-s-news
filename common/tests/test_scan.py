"""The network scan: a page that would phone home is not a page.

network_references is the guarantee behind the CLI's refusal to write a
page that loads anything (see cli.py's _write and the `scan` command).
"""
from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from itsnews_common import cli, scan
from itsnews_common.kit import Kit

FIXTURE = Path(__file__).resolve().parent / "fixture"
KIT = Kit("fixture", FIXTURE / "kit")

CLEAN = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Pier reopens</title>
<style>
  body { background: url(#fade); }
  .photo { background-image: url("data:image/png;base64,iVBORw0KGgo="); }
</style></head>
<body>
  <svg xmlns="http://www.w3.org/2000/svg"><use href="#icon"/></svg>
  <img src="data:image/gif;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=" alt="">
  <p>Source: <a href="https://example.com/pier">Example Daily</a></p>
  <script>let n = 0; document.title = "Pier " + ++n;</script>
</body>
</html>
"""


def found(html: str) -> list[str]:
    return scan.network_references(html)


class CleanPageTests(unittest.TestCase):
    def test_a_self_contained_page_passes(self):
        self.assertEqual(found(CLEAN), [])

    def test_an_empty_page_passes(self):
        self.assertEqual(found(""), [])


class LoadTests(unittest.TestCase):
    def assert_flagged(self, html: str, needle: str):
        findings = found(html)
        self.assertTrue(any(needle in f for f in findings),
                        f"{needle!r} not in {findings}")

    def test_external_script(self):
        self.assert_flagged('<script src="https://cdn.example/x.js"></script>', "script")

    def test_relative_and_protocol_relative_loads(self):
        self.assert_flagged('<img src="pixel.png">', "img")
        self.assert_flagged('<img src="//tracker.example/p.png">', "img")

    def test_stylesheet_image_iframe_and_form(self):
        self.assert_flagged('<link rel="stylesheet" href="theme.css">', "link")
        self.assert_flagged('<iframe src="https://example.com/embed"></iframe>', "iframe")
        self.assert_flagged('<form action="https://example.com/collect"></form>', "form")

    def test_svg_and_media_loads(self):
        self.assert_flagged('<svg><image href="https://example.com/x.png"/></svg>', "image")
        self.assert_flagged('<video poster="https://example.com/p.jpg"></video>', "video")
        self.assert_flagged('<img srcset="a.png 1x, b.png 2x">', "img")

    def test_meta_refresh_to_a_url(self):
        self.assert_flagged('<meta http-equiv="refresh" content="0; url=https://example.com">',
                            "refresh")

    def test_findings_name_the_line(self):
        findings = found("<p>one</p>\n<p>two</p>\n<img src=\"x.png\">")
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0].startswith("line 3:"), findings)


class ScriptAndCssTests(unittest.TestCase):
    def assert_flagged(self, html: str, needle: str):
        findings = found(html)
        self.assertTrue(any(needle in f for f in findings),
                        f"{needle!r} not in {findings}")

    def test_network_apis_in_a_script(self):
        for api in ("fetch('https://example.com')", "new XMLHttpRequest()",
                    "new WebSocket('wss://example.com')",
                    "navigator.sendBeacon('/log')", "import('https://example.com/m.js')"):
            with self.subTest(api=api):
                self.assert_flagged(f"<script>{api}</script>", "script")

    def test_network_api_in_an_event_handler(self):
        self.assert_flagged('<body onload="fetch(\'https://example.com\')">', "fetch")

    def test_css_imports_and_urls(self):
        self.assert_flagged("<style>@import 'theme.css';</style>", "@import")
        self.assert_flagged('<style>a { background: url("https://example.com/x.png") }</style>',
                            "url(")
        self.assert_flagged('<p style="background: url(bg.png)">x</p>', "url(")

    def test_fragment_and_data_urls_in_css_pass(self):
        self.assertEqual(found('<style>a { fill: url(#grad) }</style>'), [])
        self.assertEqual(found('<style>a { background: url("data:image/png;base64,AA==") }</style>'),
                         [])


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(KIT, list(args))
        return code, out.getvalue(), err.getvalue()

    def test_scan_command_accepts_a_clean_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(CLEAN, encoding="utf-8")
            code, out, _ = self.run_cli("scan", str(page))
            self.assertEqual(code, 0)
            self.assertIn("self-contained", out)

    def test_scan_command_rejects_a_beacon(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text('<img src="https://tracker.example/p.png">', encoding="utf-8")
            code, _, err = self.run_cli("scan", str(page))
            self.assertEqual(code, 1)
            self.assertIn("img", err)

    def test_write_refuses_a_page_that_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "page.html"
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = cli._write(out, '<script src="https://cdn.example/x.js"></script>')
            self.assertEqual(code, 1)
            self.assertIn("not written", err.getvalue())
            self.assertFalse(out.exists())

    def test_write_writes_a_clean_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "page.html"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = cli._write(out, CLEAN)
            self.assertEqual(code, 0)
            self.assertEqual(out.read_text(encoding="utf-8"), CLEAN)


if __name__ == "__main__":
    unittest.main()
