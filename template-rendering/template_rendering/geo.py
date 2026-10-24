"""Draw a locator map as SVG path data, deterministically.

The map is an equirectangular projection centred on the places, with
longitude scaled by cos(centre latitude) so shapes look right at the zoom
the story needs. Land and borders come from data/world.json (Natural Earth,
public domain) and are clipped to the view, so a page carries only the
coastline it shows.

Known limit: views that cross the antimeridian (180°) are not supported.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

WIDTH = 800
ASPECT = 1.6          # width / height of a regional map
WORLD_ASPECT = 2.0    # a world map is wider
PAD = 0.35            # space around the places, as a fraction of their spread
KM_PER_DEGREE = 111.32

# The smallest stretch of latitude (degrees) each scope shows, so one place
# still gets surroundings a reader can recognise.
MIN_SPAN = {"city": 0.5, "region": 4.0, "country": 14.0, "continent": 50.0}
DEFAULT_SPAN_ONE_PLACE = MIN_SPAN["region"]
DEFAULT_SPAN_MANY = 1.5

Ring = list[tuple[float, float]]


@lru_cache(maxsize=1)
def _world() -> tuple[list[tuple[tuple, Ring]], list[tuple[tuple, Ring]]]:
    data = json.loads((DATA_DIR / "world.json").read_text(encoding="utf-8"))
    scale = data["scale"]

    def decode(encoded: list[int]) -> tuple[tuple, Ring]:
        x, y = encoded[0], encoded[1]
        points = [(x / scale, y / scale)]
        for i in range(2, len(encoded), 2):
            x += encoded[i]
            y += encoded[i + 1]
            points.append((x / scale, y / scale))
        lngs = [p[0] for p in points]
        lats = [p[1] for p in points]
        return (min(lngs), min(lats), max(lngs), max(lats)), points

    return [decode(r) for r in data["land"]], [decode(b) for b in data["borders"]]


@dataclass(frozen=True)
class View:
    lng0: float      # centre
    lat0: float
    k: float         # longitude squeeze, cos(lat0)
    half_w: float    # half the view, in squeezed degrees
    half_h: float    # half the view, in degrees of latitude
    height: int      # SVG height in px (width is WIDTH)

    def project(self, lng: float, lat: float) -> tuple[float, float]:
        x = ((lng - self.lng0) * self.k + self.half_w) / (2 * self.half_w) * WIDTH
        y = (self.half_h - (lat - self.lat0)) / (2 * self.half_h) * self.height
        return x, y

    def bounds(self) -> tuple[float, float, float, float]:
        """The view in lng/lat: west, south, east, north."""
        dlng = self.half_w / self.k
        return (self.lng0 - dlng, self.lat0 - self.half_h,
                self.lng0 + dlng, self.lat0 + self.half_h)


def fit(places: list[tuple[float, float]], scope: str | None = None) -> View:
    """Frame `places` ((lat, lng) pairs) for the given scope."""
    if scope == "world":
        height = round(WIDTH / WORLD_ASPECT)
        return View(lng0=0.0, lat0=10.0, k=1.0, half_w=180.0, half_h=90.0, height=height)

    lats = [p[0] for p in places]
    lngs = [p[1] for p in places]
    lat0 = (min(lats) + max(lats)) / 2
    lng0 = (min(lngs) + max(lngs)) / 2
    k = max(math.cos(math.radians(lat0)), 0.2)

    w = (max(lngs) - min(lngs)) * k * (1 + 2 * PAD)
    h = (max(lats) - min(lats)) * (1 + 2 * PAD)
    if scope in MIN_SPAN:
        min_h = MIN_SPAN[scope]
    else:
        min_h = DEFAULT_SPAN_ONE_PLACE if len(places) == 1 else DEFAULT_SPAN_MANY
    h = max(h, min_h)
    if w / h < ASPECT:
        w = h * ASPECT
    else:
        h = w / ASPECT
    return View(lng0=lng0, lat0=lat0, k=k, half_w=w / 2, half_h=h / 2,
                height=round(WIDTH / ASPECT))


# --- clipping -------------------------------------------------------------

def _clip_polygon(points: Ring, x0: float, y0: float, x1: float, y1: float) -> Ring:
    """Sutherland-Hodgman against an axis-aligned rectangle."""
    edges = (
        (lambda p: p[0] >= x0, lambda a, b: _at_x(a, b, x0)),
        (lambda p: p[0] <= x1, lambda a, b: _at_x(a, b, x1)),
        (lambda p: p[1] >= y0, lambda a, b: _at_y(a, b, y0)),
        (lambda p: p[1] <= y1, lambda a, b: _at_y(a, b, y1)),
    )
    out = points
    for inside, cross in edges:
        if not out:
            break
        src, out = out, []
        prev = src[-1]
        for cur in src:
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
    return out


def _at_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return (x, a[1] + t * (b[1] - a[1]))


def _at_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return (a[0] + t * (b[0] - a[0]), y)


def _clip_line(points: Ring, x0, y0, x1, y1) -> list[Ring]:
    """Split a polyline into the runs that fall inside the rectangle."""
    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    runs: list[Ring] = []
    run: Ring = []
    for a, b in zip(points, points[1:]):
        seg = _clip_segment(a, b, x0, y0, x1, y1)
        if seg is None:
            if run:
                runs.append(run)
                run = []
            continue
        p, q = seg
        if not run:
            run = [p]
        run.append(q)
        if not inside(b):
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) >= 2]


def _clip_segment(a, b, x0, y0, x1, y1):
    """Liang-Barsky. Returns the visible part of segment a-b, or None."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


# --- path data --------------------------------------------------------------

def _path(points: Ring, close: bool) -> str:
    """SVG path data at 0.1 px precision, relative moves after the first point."""
    q = []
    for x, y in points:
        p = (round(x * 10), round(y * 10))
        if not q or q[-1] != p:
            q.append(p)
    if len(q) < (3 if close else 2):
        return ""
    parts = [f"M{_n(q[0][0])} {_n(q[0][1])}"]
    parts += [f"l{_n(bx - ax)} {_n(by - ay)}" for (ax, ay), (bx, by) in zip(q, q[1:])]
    return "".join(parts) + ("z" if close else "")


def _n(tenths: int) -> str:
    whole, frac = divmod(abs(tenths), 10)
    sign = "-" if tenths < 0 else ""
    return f"{sign}{whole}.{frac}" if frac else f"{sign}{whole}"


def _overlaps(bbox, bounds) -> bool:
    w, s, e, n = bounds
    return not (bbox[2] < w or bbox[0] > e or bbox[3] < s or bbox[1] > n)


def _scale_bar(view: View) -> dict:
    """A round-numbered distance about a fifth of the map wide."""
    km_per_px = (2 * view.half_h * KM_PER_DEGREE) / view.height
    target = km_per_px * WIDTH / 5
    magnitude = 10 ** math.floor(math.log10(target))
    km = max(m * magnitude for m in (1, 2, 5, 10) if m * magnitude <= target)
    label = f"{km:,.0f} km" if km >= 1 else f"{km * 1000:,.0f} m"
    return {"pct": round(km / km_per_px / WIDTH * 100, 2), "label": label}


def draw(places: list[tuple[float, float]], scope: str | None = None) -> dict:
    """Everything the map template needs: size, land, borders, pins, scale.

    Pins and the scale bar are positioned in percent of the map so the page
    can draw them as HTML at a fixed, readable size on any screen; the SVG
    underneath scales freely.
    """
    view = fit(places, scope)
    margin = 8
    rect = (-margin, -margin, WIDTH + margin, view.height + margin)
    west, south, east, north = view.bounds()
    # Grow the lng/lat box by the same margin so the coarse test never drops a
    # shape the clip would keep.
    pad_lng = margin / WIDTH * (east - west)
    pad_lat = margin / view.height * (north - south)
    bounds = (west - pad_lng, south - pad_lat, east + pad_lng, north + pad_lat)

    land_rings, border_lines = _world()
    land = []
    for bbox, ring in land_rings:
        if _overlaps(bbox, bounds):
            clipped = _clip_polygon([view.project(*p) for p in ring], *rect)
            land.append(_path(clipped, close=True))
    borders = []
    for bbox, line in border_lines:
        if _overlaps(bbox, bounds):
            for run in _clip_line([view.project(*p) for p in line], *rect):
                borders.append(_path(run, close=False))

    pins = []
    for i, (lat, lng) in enumerate(places):
        x, y = view.project(lng, lat)
        pins.append({
            "n": i + 1,
            "left": round(x / WIDTH * 100, 2),
            "top": round(y / view.height * 100, 2),
            "main": i == 0,
        })

    return {
        "width": WIDTH,
        "height": view.height,
        "land": "".join(land),
        "borders": "".join(borders),
        "pins": pins,
        "scale": None if scope == "world" else _scale_bar(view),
    }
