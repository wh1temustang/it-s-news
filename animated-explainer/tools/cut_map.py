#!/usr/bin/env python3
"""Cut the map behind a route out of template rendering's world.json.

The example explainer embeds the coastlines and borders around its route in a
<script type="application/json" id="europe"> block. This prints that block's
contents. Rerun it only to change the area or the precision, then paste the
output into the page.

Usage (from the repo root):
    python3 animated-explainer/tools/cut_map.py \\
        template-rendering/template_rendering/data/world.json > map.json

The default box (west, south, east, north) covers western and central Europe.
Pass another as four numbers after the input file.

Natural Earth is public domain (https://www.naturalearthdata.com/).

Output: {"land": [ring, ...], "borders": [line, ...]}, in world.json's own
encoding: longitude and latitude in hundredths of a degree, with every point
after the first stored as a delta from the one before.
"""
from __future__ import annotations

import json
import math
import sys

SCALE = 100           # hundredths of a degree, as in world.json
TOLERANCE = 0.04      # Douglas-Peucker tolerance, in degrees
MIN_AREA = 0.15       # drop islands smaller than this, in square degrees
BOX = (-20.0, 30.0, 40.0, 64.0)

Point = tuple[float, float]


def decode(encoded: list[int], scale: int) -> list[Point]:
    x, y = encoded[0], encoded[1]
    points = [(x / scale, y / scale)]
    for i in range(2, len(encoded), 2):
        x += encoded[i]
        y += encoded[i + 1]
        points.append((x / scale, y / scale))
    return points


def encode(points: list[Point]) -> list[int]:
    q = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
    out = [q[0][0], q[0][1]]
    for (ax, ay), (bx, by) in zip(q, q[1:]):
        if (bx, by) != (ax, ay):
            out += [bx - ax, by - ay]
    return out


def simplify(points: list[Point], tol: float) -> list[Point]:
    """Douglas-Peucker, iterative so long coastlines don't hit the recursion limit."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (x1, y1), (x2, y2) = points[start], points[end]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy)
        best, index = 0.0, start
        for i in range(start + 1, end):
            px, py = points[i]
            if norm:
                d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
            else:
                d = math.hypot(px - x1, py - y1)
            if d > best:
                best, index = d, i
        if best > tol:
            keep[index] = True
            stack += [(start, index), (index, end)]
    return [p for p, k in zip(points, keep) if k]


def area(ring: list[Point]) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


def cut(world: dict, box: tuple[float, float, float, float]) -> dict:
    west, south, east, north = box
    inside = lambda p: west <= p[0] <= east and south <= p[1] <= north
    land, borders = [], []
    for encoded in world["land"]:
        ring = decode(encoded, world["scale"])
        lngs, lats = [p[0] for p in ring], [p[1] for p in ring]
        if max(lngs) < west or min(lngs) > east or max(lats) < south or min(lats) > north:
            continue
        # Clamping keeps a ring closed; the page never shows the box's edges.
        clamped = [(min(max(x, west), east), min(max(y, south), north)) for x, y in ring]
        ring = simplify(clamped + [clamped[0]], TOLERANCE)[:-1]
        if len(ring) >= 3 and area(ring) > MIN_AREA:
            land.append(encode(ring))
    for encoded in world["borders"]:
        run: list[Point] = []
        for p in decode(encoded, world["scale"]) + [None]:
            if p is not None and inside(p):
                run.append(p)
                continue
            if len(run) >= 2:
                borders.append(encode(simplify(run, TOLERANCE)))
            run = []
    return {"land": land, "borders": borders}


def main(argv: list[str]) -> None:
    if len(argv) not in (2, 6):
        sys.exit(__doc__)
    world = json.loads(open(argv[1], encoding="utf-8").read())
    box = tuple(float(v) for v in argv[2:]) if len(argv) == 6 else BOX
    print(json.dumps(cut(world, box), separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv)
