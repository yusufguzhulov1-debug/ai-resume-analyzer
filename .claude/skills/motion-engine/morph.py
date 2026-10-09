"""SVG path interpolation and shape morphing."""

from __future__ import annotations
import math
import re
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw


Point = Tuple[float, float]


def parse_svg_path(d: str) -> List[Point]:
    """Parse an SVG path string into a list of points.

    Supports M, L, H, V, Z commands (absolute only).
    For curves (C, Q), samples control points as intermediate points.
    """
    points = []
    tokens = re.findall(r'[MLHVCQZmlhvcqz]|[-+]?\d*\.?\d+', d)
    cx, cy = 0.0, 0.0
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd in ('M', 'm'):
            i += 1
            x, y = float(tokens[i]), float(tokens[i + 1])
            if cmd == 'm':
                x += cx
                y += cy
            cx, cy = x, y
            points.append((cx, cy))
            i += 2
        elif cmd in ('L', 'l'):
            i += 1
            x, y = float(tokens[i]), float(tokens[i + 1])
            if cmd == 'l':
                x += cx
                y += cy
            cx, cy = x, y
            points.append((cx, cy))
            i += 2
        elif cmd in ('H', 'h'):
            i += 1
            x = float(tokens[i])
            if cmd == 'h':
                x += cx
            cx = x
            points.append((cx, cy))
            i += 1
        elif cmd in ('V', 'v'):
            i += 1
            y = float(tokens[i])
            if cmd == 'v':
                y += cy
            cy = y
            points.append((cx, cy))
            i += 1
        elif cmd in ('C', 'c'):
            i += 1
            # Cubic bezier: sample 4 points along the curve
            x1, y1 = float(tokens[i]), float(tokens[i + 1])
            x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
            x3, y3 = float(tokens[i + 4]), float(tokens[i + 5])
            if cmd == 'c':
                x1 += cx; y1 += cy
                x2 += cx; y2 += cy
                x3 += cx; y3 += cy
            for t in [0.25, 0.5, 0.75, 1.0]:
                bx = _cubic_bezier_pt(cx, x1, x2, x3, t)
                by = _cubic_bezier_pt(cy, y1, y2, y3, t)
                points.append((bx, by))
            cx, cy = x3, y3
            i += 6
        elif cmd in ('Q', 'q'):
            i += 1
            x1, y1 = float(tokens[i]), float(tokens[i + 1])
            x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
            if cmd == 'q':
                x1 += cx; y1 += cy
                x2 += cx; y2 += cy
            for t in [0.33, 0.67, 1.0]:
                bx = _quad_bezier_pt(cx, x1, x2, t)
                by = _quad_bezier_pt(cy, y1, y2, t)
                points.append((bx, by))
            cx, cy = x2, y2
            i += 4
        elif cmd in ('Z', 'z'):
            if points:
                points.append(points[0])
            i += 1
        else:
            i += 1
    return points


def _cubic_bezier_pt(p0, p1, p2, p3, t):
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _quad_bezier_pt(p0, p1, p2, t):
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def resample_points(points: List[Point], n: int) -> List[Point]:
    """Resample a polyline to exactly n evenly-spaced points."""
    if len(points) < 2:
        return [points[0]] * n if points else [(0, 0)] * n

    # Compute cumulative arc length
    dists = [0.0]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        dists.append(dists[-1] + math.sqrt(dx * dx + dy * dy))

    total = dists[-1]
    if total == 0:
        return [points[0]] * n

    result = []
    for i in range(n):
        target = (i / max(1, n - 1)) * total
        # Find segment
        for j in range(1, len(dists)):
            if dists[j] >= target:
                seg_len = dists[j] - dists[j - 1]
                if seg_len == 0:
                    t = 0
                else:
                    t = (target - dists[j - 1]) / seg_len
                x = points[j - 1][0] + (points[j][0] - points[j - 1][0]) * t
                y = points[j - 1][1] + (points[j][1] - points[j - 1][1]) * t
                result.append((x, y))
                break
    return result


def interpolate_shapes(
    shape_a: List[Point],
    shape_b: List[Point],
    t: float,
    num_points: int = 100,
) -> List[Point]:
    """Interpolate between two shapes.

    Both shapes are resampled to `num_points` points, then linearly
    interpolated based on t (0 = shape_a, 1 = shape_b).
    """
    a = resample_points(shape_a, num_points)
    b = resample_points(shape_b, num_points)
    t = max(0.0, min(1.0, t))
    return [
        (a[i][0] + (b[i][0] - a[i][0]) * t, a[i][1] + (b[i][1] - a[i][1]) * t)
        for i in range(num_points)
    ]


def draw_shape(
    canvas: Image.Image,
    points: List[Point],
    fill=None,
    outline=None,
    width: int = 2,
) -> Image.Image:
    """Draw a shape defined by points onto a canvas."""
    if len(points) < 2:
        return canvas
    draw = ImageDraw.Draw(canvas)
    if fill:
        draw.polygon(points, fill=fill)
    if outline:
        draw.line(points + [points[0]], fill=outline, width=width)
    return canvas


# --- Preset shapes ---
def circle_points(cx: float, cy: float, r: float, n: int = 64) -> List[Point]:
    """Generate points for a circle."""
    return [
        (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def rect_points(x: float, y: float, w: float, h: float) -> List[Point]:
    """Generate points for a rectangle."""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def star_points(cx: float, cy: float, outer_r: float, inner_r: float, tips: int = 5) -> List[Point]:
    """Generate points for a star shape."""
    points = []
    for i in range(tips * 2):
        r = outer_r if i % 2 == 0 else inner_r
        angle = math.pi / 2 + (2 * math.pi * i) / (tips * 2)
        points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    return points
