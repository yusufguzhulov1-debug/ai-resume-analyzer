"""Easing functions for animation curves.

All functions take t in [0,1] and return a value (usually in [0,1]).
"""

from __future__ import annotations
import math
from typing import Callable

EasingFn = Callable[[float], float]

PI = math.pi
HALF_PI = PI / 2


def linear(t: float) -> float:
    return t


# --- Sine ---
def ease_in_sine(t: float) -> float:
    return 1 - math.cos(t * HALF_PI)


def ease_out_sine(t: float) -> float:
    return math.sin(t * HALF_PI)


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(PI * t) - 1) / 2


# --- Quad ---
def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) ** 2


def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


# --- Cubic ---
def ease_in_cubic(t: float) -> float:
    return t ** 3


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# --- Quart ---
def ease_in_quart(t: float) -> float:
    return t ** 4


def ease_out_quart(t: float) -> float:
    return 1 - (1 - t) ** 4


def ease_in_out_quart(t: float) -> float:
    return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


# --- Quint ---
def ease_in_quint(t: float) -> float:
    return t ** 5


def ease_out_quint(t: float) -> float:
    return 1 - (1 - t) ** 5


def ease_in_out_quint(t: float) -> float:
    return 16 * t ** 5 if t < 0.5 else 1 - (-2 * t + 2) ** 5 / 2


# --- Expo ---
def ease_in_expo(t: float) -> float:
    return 0 if t == 0 else 2 ** (10 * t - 10)


def ease_out_expo(t: float) -> float:
    return 1 if t == 1 else 1 - 2 ** (-10 * t)


def ease_in_out_expo(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return 2 ** (20 * t - 10) / 2
    return (2 - 2 ** (-20 * t + 10)) / 2


# --- Circ ---
def ease_in_circ(t: float) -> float:
    return 1 - math.sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    return math.sqrt(1 - (t - 1) ** 2)


def ease_in_out_circ(t: float) -> float:
    if t < 0.5:
        return (1 - math.sqrt(1 - (2 * t) ** 2)) / 2
    return (math.sqrt(1 - (-2 * t + 2) ** 2) + 1) / 2


# --- Back ---
def ease_in_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return c3 * t ** 3 - c1 * t * t


def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_in_out_back(t: float) -> float:
    c1 = 1.70158
    c2 = c1 * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((c2 + 1) * 2 * t - c2)) / 2
    return ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2


# --- Elastic ---
def ease_in_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    c4 = (2 * PI) / 3
    return -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * c4)


def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    c4 = (2 * PI) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_in_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    c5 = (2 * PI) / 4.5
    if t < 0.5:
        return -(2 ** (20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2
    return (2 ** (-20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1


# --- Bounce ---
def ease_out_bounce(t: float) -> float:
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_in_bounce(t: float) -> float:
    return 1 - ease_out_bounce(1 - t)


def ease_in_out_bounce(t: float) -> float:
    if t < 0.5:
        return (1 - ease_out_bounce(1 - 2 * t)) / 2
    return (1 + ease_out_bounce(2 * t - 1)) / 2


# --- Spring (custom) ---
def spring(t: float, stiffness: float = 100, damping: float = 10) -> float:
    """Spring physics simulation."""
    if t == 0:
        return 0
    if t == 1:
        return 1
    omega = math.sqrt(stiffness)
    zeta = damping / (2 * omega)
    if zeta < 1:
        omega_d = omega * math.sqrt(1 - zeta * zeta)
        return 1 - math.exp(-zeta * omega * t) * (
            math.cos(omega_d * t) + (zeta * omega / omega_d) * math.sin(omega_d * t)
        )
    return 1 - (1 + omega * t) * math.exp(-omega * t)


# --- Cubic Bezier ---
def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> EasingFn:
    """Create a cubic-bezier easing function (like CSS transitions)."""

    def _solve_t(x: float) -> float:
        """Newton-Raphson to find t for given x."""
        t = x
        for _ in range(8):
            cx = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 - x
            if abs(cx) < 1e-7:
                break
            dx = 3 * (1 - t) ** 2 * x1 + 6 * (1 - t) * t * (x2 - x1) + 3 * t ** 2 * (1 - x2)
            if abs(dx) < 1e-7:
                break
            t -= cx / dx
        return max(0.0, min(1.0, t))

    def easing(x: float) -> float:
        if x <= 0:
            return 0
        if x >= 1:
            return 1
        t = _solve_t(x)
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3

    return easing


# --- Registry ---
EASING_MAP: dict[str, EasingFn] = {
    "linear": linear,
    "ease_in_sine": ease_in_sine,
    "ease_out_sine": ease_out_sine,
    "ease_in_out_sine": ease_in_out_sine,
    "ease_in_quad": ease_in_quad,
    "ease_out_quad": ease_out_quad,
    "ease_in_out_quad": ease_in_out_quad,
    "ease_in_cubic": ease_in_cubic,
    "ease_out_cubic": ease_out_cubic,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_in_quart": ease_in_quart,
    "ease_out_quart": ease_out_quart,
    "ease_in_out_quart": ease_in_out_quart,
    "ease_in_quint": ease_in_quint,
    "ease_out_quint": ease_out_quint,
    "ease_in_out_quint": ease_in_out_quint,
    "ease_in_expo": ease_in_expo,
    "ease_out_expo": ease_out_expo,
    "ease_in_out_expo": ease_in_out_expo,
    "ease_in_circ": ease_in_circ,
    "ease_out_circ": ease_out_circ,
    "ease_in_out_circ": ease_in_out_circ,
    "ease_in_back": ease_in_back,
    "ease_out_back": ease_out_back,
    "ease_in_out_back": ease_in_out_back,
    "ease_in_elastic": ease_in_elastic,
    "ease_out_elastic": ease_out_elastic,
    "ease_in_out_elastic": ease_in_out_elastic,
    "ease_in_bounce": ease_in_bounce,
    "ease_out_bounce": ease_out_bounce,
    "ease_in_out_bounce": ease_in_out_bounce,
}


def get_easing(name: str) -> EasingFn:
    """Get an easing function by name. Raises KeyError if not found."""
    if name in EASING_MAP:
        return EASING_MAP[name]
    # Try with/without ease_ prefix
    alt = f"ease_{name}" if not name.startswith("ease_") else name[5:]
    if alt in EASING_MAP:
        return EASING_MAP[alt]
    raise KeyError(f"Unknown easing: {name!r}. Available: {sorted(EASING_MAP.keys())}")
