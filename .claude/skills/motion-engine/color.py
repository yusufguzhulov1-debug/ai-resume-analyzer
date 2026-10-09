"""Color utilities: hex parsing, RGBA, gradients, interpolation."""

from __future__ import annotations
import math
from typing import Tuple, Union

RGBA = Tuple[int, int, int, int]
RGB = Tuple[int, int, int]
ColorLike = Union[str, RGB, RGBA, "Color"]


class Color:
    """Immutable RGBA color."""

    __slots__ = ("r", "g", "b", "a")

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        object.__setattr__(self, "r", max(0, min(255, int(r))))
        object.__setattr__(self, "g", max(0, min(255, int(g))))
        object.__setattr__(self, "b", max(0, min(255, int(b))))
        object.__setattr__(self, "a", max(0, min(255, int(a))))

    def __setattr__(self, *_):
        raise AttributeError("Color is immutable")

    @property
    def rgb(self) -> RGB:
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> RGBA:
        return (self.r, self.g, self.b, self.a)

    @property
    def hex(self) -> str:
        if self.a == 255:
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"

    @property
    def pil(self) -> RGBA:
        """Return tuple suitable for PIL (RGBA)."""
        return self.rgba

    def with_alpha(self, a: int) -> "Color":
        return Color(self.r, self.g, self.b, a)

    def __repr__(self):
        return f"Color({self.hex})"

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.rgba == other.rgba
        return NotImplemented

    def __hash__(self):
        return hash(self.rgba)


def parse_color(c: ColorLike) -> Color:
    """Parse any color-like value into a Color object."""
    if isinstance(c, Color):
        return c
    if isinstance(c, str):
        return _parse_hex(c)
    if isinstance(c, (tuple, list)):
        if len(c) == 3:
            return Color(c[0], c[1], c[2], 255)
        if len(c) == 4:
            return Color(c[0], c[1], c[2], c[3])
    raise ValueError(f"Cannot parse color: {c!r}")


def _parse_hex(s: str) -> Color:
    """Parse hex color string (#RGB, #RRGGBB, #RRGGBBAA)."""
    s = s.strip().lstrip("#")
    if len(s) == 3:
        r, g, b = (int(c * 2, 16) for c in s)
        return Color(r, g, b)
    if len(s) == 6:
        return Color(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    if len(s) == 8:
        return Color(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
    raise ValueError(f"Invalid hex color: #{s}")


def lerp_color(a: ColorLike, b: ColorLike, t: float) -> Color:
    """Linear interpolation between two colors."""
    c1 = parse_color(a)
    c2 = parse_color(b)
    t = max(0.0, min(1.0, t))
    return Color(
        int(c1.r + (c2.r - c1.r) * t),
        int(c1.g + (c2.g - c1.g) * t),
        int(c1.b + (c2.b - c1.b) * t),
        int(c1.a + (c2.a - c1.a) * t),
    )


def gradient_colors(start: ColorLike, end: ColorLike, steps: int) -> list[Color]:
    """Generate a list of colors forming a gradient."""
    if steps < 2:
        return [parse_color(start)]
    return [lerp_color(start, end, i / (steps - 1)) for i in range(steps)]


def multi_gradient(colors: list[ColorLike], steps: int) -> list[Color]:
    """Generate a gradient through multiple color stops."""
    parsed = [parse_color(c) for c in colors]
    if len(parsed) < 2:
        return [parsed[0]] * steps if parsed else []
    segments = len(parsed) - 1
    per_seg = max(1, steps // segments)
    result = []
    for i in range(segments):
        n = per_seg if i < segments - 1 else steps - len(result)
        for j in range(n):
            t = j / max(1, n - 1) if n > 1 else 0
            result.append(lerp_color(parsed[i], parsed[i + 1], t))
    return result


# Common colors
WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
TRANSPARENT = Color(0, 0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
