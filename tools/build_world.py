#!/usr/bin/env python3
"""Build itsnews/data/world.json from Natural Earth land and border data.

The map template draws coastlines and country borders from this file. It is
generated once and committed; rerun this only to change the source data or
the precision.

Usage:
    NE=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
    curl -fsSL -O $NE/ne_50m_land.geojson
    curl -fsSL -O $NE/ne_50m_admin_0_boundary_lines_land.geojson
    python3 tools/build_world.py ne_50m_land.geojson \\
        ne_50m_admin_0_boundary_lines_land.geojson itsnews/data/world.json

Natural Earth is public domain (https://www.naturalearthdata.com/).

Output: {"scale": 100, "land": [ring, ...], "borders": [line, ...]} where
each ring or line is [x0, y0, dx1, dy1, ...]: longitude and latitude times
`scale`, rounded, with every point after the first stored as a delta from
the one before.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCALE = 100          # store hundredths of a degree (about 1 km)
TOLERANCE = 0.02     # Douglas-Peucker tolerance, in degrees


def simplify(points: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
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
        norm = (dx * dx + dy * dy) ** 0.5
        best, best_i = -1.0, -1
        for i in range(start + 1, end):
            px, py = points[i]
            if norm == 0:
                d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
            else:
                d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
            if d > best:
                best, best_i = d, i
        if best > tol:
            keep[best_i] = True
            stack.append((start, best_i))
            stack.append((best_i, end))
    return [p for p, k in zip(points, keep) if k]


def encode(points: list[tuple[float, float]], min_points: int) -> list[int] | None:
    quantised: list[tuple[int, int]] = []
    for x, y in points:
        q = (round(x * SCALE), round(y * SCALE))
        if not quantised or quantised[-1] != q:
            quantised.append(q)
    if len(quantised) < min_points:
        return None
    out = [quantised[0][0], quantised[0][1]]
    for (ax, ay), (bx, by) in zip(quantised, quantised[1:]):
        out += [bx - ax, by - ay]
    return out


def parts(geometry: dict) -> list:
    """The coordinate lists of a geometry, whether single or multi."""
    multi = geometry["type"].startswith("Multi")
    return geometry["coordinates"] if multi else [geometry["coordinates"]]


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    land_src, borders_src, dst = (Path(a) for a in argv[1:])

    land = []
    for feature in json.loads(land_src.read_text(encoding="utf-8"))["features"]:
        for polygon in parts(feature["geometry"]):
            # Only the outer ring: lakes are holes we can live without at this scale.
            ring = encode(simplify([tuple(p) for p in polygon[0]], TOLERANCE), 4)
            if ring:
                land.append(ring)

    borders = []
    for feature in json.loads(borders_src.read_text(encoding="utf-8"))["features"]:
        for line in parts(feature["geometry"]):
            encoded = encode(simplify([tuple(p) for p in line], TOLERANCE), 2)
            if encoded:
                borders.append(encoded)

    # Sort so the output is stable whatever order the source lists features in.
    land.sort(key=lambda r: (r[0], r[1], len(r)))
    borders.sort(key=lambda r: (r[0], r[1], len(r)))
    data = {
        "source": "Natural Earth 1:50m land and admin-0 boundary lines, public domain",
        "scale": SCALE,
        "land": land,
        "borders": borders,
    }
    dst.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    points = sum(len(r) // 2 for r in land + borders)
    print(f"{dst}: {len(land)} land rings, {len(borders)} border lines, "
          f"{points} points, {dst.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
