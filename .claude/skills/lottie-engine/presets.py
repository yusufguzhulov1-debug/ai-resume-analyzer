"""Common animation presets — quick ways to animate layers."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Layer


def fade_in(layer: "Layer", start: float = 0.0, dur: float = 0.5, easing: str = "ease_out_cubic"):
    """Fade in from transparent."""
    layer.keyframe(start, opacity=0)
    layer.keyframe(start + dur, opacity=1, easing=easing)


def fade_out(layer: "Layer", start: float = 0.0, dur: float = 0.5, easing: str = "ease_in_cubic"):
    """Fade out to transparent."""
    layer.keyframe(start, opacity=1)
    layer.keyframe(start + dur, opacity=0, easing=easing)


def slide_up(layer: "Layer", start: float = 0.0, dur: float = 0.5,
             from_y: float = 200, to_y: float = 0, easing: str = "ease_out_cubic"):
    """Slide element up into position."""
    layer.keyframe(start, y=from_y, opacity=0)
    layer.keyframe(start + dur, y=to_y, opacity=1, easing=easing)


def slide_down(layer: "Layer", start: float = 0.0, dur: float = 0.5,
               from_y: float = -200, to_y: float = 0, easing: str = "ease_out_cubic"):
    """Slide element down into position."""
    layer.keyframe(start, y=from_y, opacity=0)
    layer.keyframe(start + dur, y=to_y, opacity=1, easing=easing)


def slide_left(layer: "Layer", start: float = 0.0, dur: float = 0.5,
               from_x: float = 200, to_x: float = 0, easing: str = "ease_out_cubic"):
    """Slide element from right to left into position."""
    layer.keyframe(start, x=from_x, opacity=0)
    layer.keyframe(start + dur, x=to_x, opacity=1, easing=easing)


def slide_right(layer: "Layer", start: float = 0.0, dur: float = 0.5,
                from_x: float = -200, to_x: float = 0, easing: str = "ease_out_cubic"):
    """Slide element from left to right into position."""
    layer.keyframe(start, x=from_x, opacity=0)
    layer.keyframe(start + dur, x=to_x, opacity=1, easing=easing)


def bounce_in(layer: "Layer", start: float = 0.0, dur: float = 0.6, easing: str = "ease_out_back"):
    """Scale-bounce into view."""
    layer.keyframe(start, scale=0, opacity=0)
    layer.keyframe(start + dur, scale=1, opacity=1, easing=easing)


def bounce_out(layer: "Layer", start: float = 0.0, dur: float = 0.4, easing: str = "ease_in_back"):
    """Scale-bounce out of view."""
    layer.keyframe(start, scale=1, opacity=1)
    layer.keyframe(start + dur, scale=0, opacity=0, easing=easing)


def pop_in(layer: "Layer", start: float = 0.0, dur: float = 0.5, easing: str = "ease_out_elastic"):
    """Elastic pop-in effect."""
    layer.keyframe(start, scale=0, opacity=0)
    layer.keyframe(start + dur, scale=1, opacity=1, easing=easing)


def scale_pulse(layer: "Layer", start: float = 0.0, dur: float = 1.0,
                min_scale: float = 0.95, max_scale: float = 1.05):
    """Gentle pulsing scale animation."""
    half = dur / 2
    layer.keyframe(start, scale=min_scale)
    layer.keyframe(start + half, scale=max_scale, easing="ease_in_out_sine")
    layer.keyframe(start + dur, scale=min_scale, easing="ease_in_out_sine")


def rotate_in(layer: "Layer", start: float = 0.0, dur: float = 0.6,
              from_angle: float = -90, easing: str = "ease_out_cubic"):
    """Rotate into view."""
    layer.keyframe(start, rotation=from_angle, opacity=0, scale=0.5)
    layer.keyframe(start + dur, rotation=0, opacity=1, scale=1, easing=easing)


def typewriter_opacity(layer: "Layer", start: float = 0.0, char_delay: float = 0.05):
    """Simple appear effect (opacity snap)."""
    layer.keyframe(start, opacity=0)
    layer.keyframe(start + char_delay, opacity=1, easing="linear")


def stagger_in(layers: list["Layer"], start: float = 0.0, stagger: float = 0.1,
               preset: str = "slide_up", **kwargs):
    """Apply a preset to multiple layers with staggered timing."""
    preset_fn = {
        "fade_in": fade_in,
        "slide_up": slide_up,
        "slide_down": slide_down,
        "slide_left": slide_left,
        "slide_right": slide_right,
        "bounce_in": bounce_in,
        "pop_in": pop_in,
        "rotate_in": rotate_in,
    }.get(preset, slide_up)

    for i, layer in enumerate(layers):
        preset_fn(layer, start=start + i * stagger, **kwargs)
