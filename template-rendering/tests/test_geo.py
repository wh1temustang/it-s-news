"""Map geometry: framing, clipping, path data and the scale bar."""
from __future__ import annotations

import re
import unittest

from template_rendering import geo
from template_rendering.article import parse

VIENNA, BARCELONA = (48.21, 16.37), (41.39, 2.17)


class FitTests(unittest.TestCase):
    def test_every_place_is_inside_the_frame(self):
        drawn = geo.draw([VIENNA, BARCELONA, (47.38, 8.54)])
        for pin in drawn["pins"]:
            self.assertTrue(5 < pin["left"] < 95, pin)
            self.assertTrue(5 < pin["top"] < 95, pin)

    def test_one_place_sits_in_the_middle_with_room_around_it(self):
        view = geo.fit([VIENNA])
        self.assertAlmostEqual(view.project(VIENNA[1], VIENNA[0])[0], geo.WIDTH / 2)
        self.assertAlmostEqual(2 * view.half_h, geo.DEFAULT_SPAN_ONE_PLACE)

    def test_scope_sets_the_minimum_zoom(self):
        city = geo.fit([VIENNA], "city")
        country = geo.fit([VIENNA], "country")
        self.assertLess(city.half_h, country.half_h)
        self.assertAlmostEqual(2 * country.half_h, geo.MIN_SPAN["country"])

    def test_world_scope_shows_every_longitude(self):
        west, _, east, _ = geo.fit([VIENNA], "world").bounds()
        self.assertEqual((west, east), (-180.0, 180.0))
        self.assertIsNone(geo.draw([VIENNA], "world")["scale"])

    def test_the_main_place_is_the_first(self):
        pins = geo.draw([VIENNA, BARCELONA])["pins"]
        self.assertEqual([p["main"] for p in pins], [True, False])
        self.assertEqual([p["n"] for p in pins], [1, 2])


class DrawTests(unittest.TestCase):
    def test_coastline_and_borders_are_drawn_as_compact_paths(self):
        drawn = geo.draw([VIENNA, BARCELONA])
        for key in ("land", "borders"):
            self.assertTrue(drawn[key], key)
            self.assertRegex(drawn[key], r"^[Mlz0-9. -]+$")
        # Clipping keeps a regional map small.
        self.assertLess(len(drawn["land"]) + len(drawn["borders"]), 60_000)

    def test_open_ocean_has_no_land(self):
        self.assertEqual(geo.draw([(-40.0, -130.0)], "city")["land"], "")

    def test_scale_bar_is_a_round_distance(self):
        scale = geo.draw([VIENNA, BARCELONA])["scale"]
        self.assertRegex(scale["label"], r"^(1|2|5)0* km$")
        self.assertTrue(5 < scale["pct"] < 25, scale)

    def test_clip_polygon_to_rectangle(self):
        square = [(-5, -5), (5, -5), (5, 5), (-5, 5)]
        clipped = geo._clip_polygon(square, 0, 0, 10, 10)
        self.assertEqual(sorted(set(clipped)), [(0, 0), (0, 5), (5, 0), (5, 5)])

    def test_clip_line_splits_where_it_leaves(self):
        line = [(-5, 5), (5, 5), (15, 5), (15, 8), (5, 8)]
        runs = geo._clip_line(line, 0, 0, 10, 10)
        self.assertEqual(runs, [[(0, 5), (5, 5), (10, 5)], [(10, 8), (5, 8)]])


class ArticleTests(unittest.TestCase):
    def test_front_matter_and_title(self):
        a = parse("---\ntitle: \"Quoted\"\nfictional: yes\n---\n# Heading\nBody\n")
        self.assertEqual(a.title, "Quoted")
        self.assertTrue(a.fictional)
        self.assertEqual(a.body, "# Heading\nBody\n")

    def test_title_falls_back_to_first_heading(self):
        self.assertEqual(parse("Intro\n\n# The heading\n").title, "The heading")

    def test_only_http_urls_are_kept(self):
        self.assertIsNone(parse("---\nurl: javascript:x\n---\n").url)
        self.assertEqual(parse("---\nurl: https://a.example\n---\n").url, "https://a.example")

    def test_no_front_matter(self):
        a = parse("Just text\n")
        self.assertEqual((a.meta, a.fictional, a.url), ({}, False, None))
        self.assertTrue(re.match("Just text", a.body))


if __name__ == "__main__":
    unittest.main()
