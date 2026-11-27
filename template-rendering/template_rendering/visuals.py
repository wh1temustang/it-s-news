"""Turn a scene's validated data into what its template draws.

Most templates take their data as is. The ones that draw (charts, maps) need
geometry first; that maths lives here, in plain Python, so the same data
always produces the same picture.
"""
from __future__ import annotations

import math
from typing import Callable

from . import geo


def format_number(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,}"


def bar_chart(data: dict) -> dict:
    values = [bar["value"] for bar in data["bars"]]
    top = max(abs(v) for v in values) or 1
    rows = [
        {
            "label": bar["label"],
            "display": bar.get("display") or format_number(bar["value"]),
            "pct": round(abs(bar["value"]) / top * 100, 2),
            "negative": bar["value"] < 0,
        }
        for bar in data["bars"]
    ]
    return {**data, "rows": rows, "diverging": any(v < 0 for v in values)}


# Line chart canvas, in SVG units. The SVG scales to the page width.
LC_W, LC_H = 600, 280
LC_PAD = {"left": 24, "right": 24, "top": 34, "bottom": 36}


def line_chart(data: dict) -> dict:
    points = data["points"]
    ys = [p["y"] for p in points]
    lo, hi = min(ys), max(ys)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    # Extra room below so the low point's label clears the x-axis labels.
    span = hi - lo
    lo, hi = lo - span * 0.45, hi + span * 0.2

    left, right = LC_PAD["left"], LC_W - LC_PAD["right"]
    top, bottom = LC_PAD["top"], LC_H - LC_PAD["bottom"]
    step = (right - left) / (len(points) - 1)

    def xy(i: int, y: float) -> tuple[float, float]:
        return round(left + i * step, 1), round(top + (hi - y) / (hi - lo) * (bottom - top), 1)

    coords = [xy(i, p["y"]) for i, p in enumerate(points)]
    line = "M" + " L".join(f"{x} {y}" for x, y in coords)
    area = f"{line} L{coords[-1][0]} {bottom} L{coords[0][0]} {bottom} Z"

    # Label the ends and the extremes; labelling every point turns to noise.
    i_max, i_min = ys.index(max(ys)), ys.index(min(ys))
    labelled = sorted({0, len(points) - 1, i_max, i_min})
    dots = []
    for i, (x, y) in enumerate(coords):
        dot = {"x": x, "y": y, "label": None, "below": False, "anchor": "middle"}
        if i in labelled:
            dot["label"] = points[i].get("display") or format_number(points[i]["y"])
            dot["below"] = i == i_min and i != i_max and len(set(ys)) > 1
            dot["anchor"] = "start" if i == 0 else "end" if i == len(points) - 1 else "middle"
        dots.append(dot)

    # Show every x label when they fit, otherwise every nth plus the last.
    every = 1 if len(points) <= 7 else -(-len(points) // 6)
    ticks = [
        {"x": coords[i][0], "text": p["x"],
         "anchor": "start" if i == 0 else "end" if i == len(points) - 1 else "middle"}
        for i, p in enumerate(points)
        if i % every == 0 or i == len(points) - 1
    ]
    return {**data, "w": LC_W, "h": LC_H, "line": line, "area": area,
            "dots": dots, "ticks": ticks, "baseline": bottom,
            "left": left, "right": right}


def _floor_tenth(value: float) -> float:
    """Round down to one decimal place; _ceil_tenth rounds up.

    The round(..., 9) first clears binary float dust, so a computed end
    of 42.4 stays 42.4 instead of slipping to 42.3.
    """
    return math.floor(round(value, 9) * 10) / 10


def _ceil_tenth(value: float) -> float:
    return math.ceil(round(value, 9) * 10) / 10


def scale(data: dict) -> dict:
    """Place one number on an axis with its reference marks.

    The axis ends are display choices: use min/max when given, otherwise
    fit the value and the marks with room at both ends. Mark labels are
    centred on their ticks, clamped so a label near either end stays on
    the page — the tick keeps the exact position, only the label shifts.

    A computed end is rounded to one decimal place — floored on the
    left, ceiled on the right — so the axis never shows an artefact
    like 107.854, and still brackets the value and every mark. An
    explicit min/max is the author's own display choice and is kept
    exact.
    """
    value = data["value"]
    marks = data.get("marks") or []
    points = [value, *[m["value"] for m in marks]]
    lo = data.get("min")
    hi = data.get("max")
    if lo is None or hi is None:
        span = max(points) - min(points)
        pad = span * 0.15 if span > 0 else max(abs(value), 1) * 0.15
        if lo is None:
            lo = _floor_tenth(min(points) - pad)
        if hi is None:
            hi = _ceil_tenth(max(points) + pad)
    if hi <= lo:
        hi = lo + 1

    def pct(v: float) -> float:
        return round((v - lo) / (hi - lo) * 100, 2)

    return {**data,
            "lo_display": format_number(lo),
            "hi_display": format_number(hi),
            "value_pct": pct(value),
            "value_display": format_number(value),
            "marks": [{**m,
                       "pct": pct(m["value"]),
                       "label_pct": min(max(pct(m["value"]), 18), 82),
                       "display": format_number(m["value"])}
                      for m in marks]}


def breakdown(data: dict) -> dict:
    """Size each part against the stated total.

    The parts are shares of the total, so a part's bar is its fraction
    of it — never of the largest part. Articles round figures, so no
    check here that the parts sum exactly to the total.
    """
    total = data["total"]["value"]
    rows = [
        {
            "name": part["name"],
            "display": format_number(part["value"]),
            "pct": round(part["value"] / total * 100, 2) if total else 0,
        }
        for part in data["parts"]
    ]
    return {**data,
            "total_display": format_number(total),
            "rows": rows}


def map_view(data: dict) -> dict:
    places = [(p["lat"], p["lng"]) for p in data["places"]]
    return {**data, **geo.draw(places, data.get("scope"))}


def quote(data: dict) -> dict:
    # The template adds its own quotation mark; drop any the agent copied.
    return {**data, "text": data["text"].strip().strip("\"'“”‘’").strip()}


PREPARE: dict[str, Callable[[dict], dict]] = {
    "bar-chart": bar_chart,
    "line-chart": line_chart,
    "map": map_view,
    "quote": quote,
    "scale": scale,
    "breakdown": breakdown,
}


def prepare(template_id: str, data: dict) -> dict:
    return PREPARE.get(template_id, dict)(data)
