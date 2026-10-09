"""Scene — timeline-based composition and rendering.

The Scene is the main entry point for creating animations.
Add elements with timing, enter/exit animations, and render to MP4.
"""

from __future__ import annotations
import math
import sys
from typing import Optional, List, Tuple, Callable

from PIL import Image

from .color import parse_color, ColorLike, Color
from .easing import get_easing, EasingFn, EASING_MAP
from .elements import Element
from .renderer import VideoWriter


# Built-in enter/exit animation presets
def _anim_fade_in(el: Element, t: float):
    el.opacity = t

def _anim_fade_out(el: Element, t: float):
    el.opacity = 1 - t

def _anim_fade_up(el: Element, t: float):
    el.opacity = t
    el._anim_y_offset = (1 - t) * 50

def _anim_fade_down(el: Element, t: float):
    el.opacity = t
    el._anim_y_offset = -(1 - t) * 50

def _anim_fade_left(el: Element, t: float):
    el.opacity = t
    el._anim_x_offset = (1 - t) * 50

def _anim_fade_right(el: Element, t: float):
    el.opacity = t
    el._anim_x_offset = -(1 - t) * 50

def _anim_scale_in(el: Element, t: float):
    el.scale = t
    el.opacity = t

def _anim_scale_out(el: Element, t: float):
    el.scale = 1 - t
    el.opacity = 1 - t

def _anim_scale_up(el: Element, t: float):
    el.scale = 0.5 + 0.5 * t
    el.opacity = t

def _anim_bounce_in(el: Element, t: float):
    el.scale = t
    el.opacity = min(1, t * 2)

def _anim_slide_up(el: Element, t: float):
    el._anim_y_offset = (1 - t) * 200

def _anim_slide_down(el: Element, t: float):
    el._anim_y_offset = -(1 - t) * 200

def _anim_slide_left(el: Element, t: float):
    el._anim_x_offset = (1 - t) * 200

def _anim_slide_right(el: Element, t: float):
    el._anim_x_offset = -(1 - t) * 200

def _anim_none(el: Element, t: float):
    pass


ENTER_ANIMS = {
    "fade_in": _anim_fade_in,
    "fade_up": _anim_fade_up,
    "fade_down": _anim_fade_down,
    "fade_left": _anim_fade_left,
    "fade_right": _anim_fade_right,
    "scale_in": _anim_scale_in,
    "scale_up": _anim_scale_up,
    "bounce_in": _anim_bounce_in,
    "slide_up": _anim_slide_up,
    "slide_down": _anim_slide_down,
    "slide_left": _anim_slide_left,
    "slide_right": _anim_slide_right,
    "none": _anim_none,
}

EXIT_ANIMS = {
    "fade_out": _anim_fade_out,
    "scale_out": _anim_scale_out,
    "slide_up": lambda el, t: _anim_slide_up(el, 1 - t),
    "slide_down": lambda el, t: _anim_slide_down(el, 1 - t),
    "fade_up": lambda el, t: (setattr(el, 'opacity', 1 - t), setattr(el, '_anim_y_offset', -t * 50)),
    "fade_down": lambda el, t: (setattr(el, 'opacity', 1 - t), setattr(el, '_anim_y_offset', t * 50)),
    "none": _anim_none,
}


class LayerEntry:
    """An element placed on the timeline."""

    def __init__(
        self,
        element: Element,
        enter: float,
        dur: float,
        exit_time: Optional[float] = None,
        enter_anim: str = "fade_in",
        exit_anim: str = "fade_out",
        enter_dur: float = 0.4,
        exit_dur: float = 0.4,
        enter_easing: str = "ease_out_cubic",
        exit_easing: str = "ease_in_cubic",
        z_index: int = 0,
    ):
        self.element = element
        self.enter = enter  # seconds when element appears
        self.dur = dur  # how long it's visible
        self.exit_time = exit_time if exit_time is not None else enter + dur
        self.enter_anim_name = enter_anim
        self.exit_anim_name = exit_anim
        self.enter_dur = enter_dur
        self.exit_dur = exit_dur
        self.enter_easing = enter_easing
        self.exit_easing = exit_easing
        self.z_index = z_index
        self._orig_x = element.x
        self._orig_y = element.y
        self._orig_opacity = element.opacity
        self._orig_scale = element.scale
        self._orig_rotation = element.rotation

    def is_visible(self, t: float) -> bool:
        return self.enter <= t < self.exit_time + self.exit_dur

    def apply(self, t: float):
        """Apply animations for the current time."""
        el = self.element
        # Reset to original values
        el.x = self._orig_x
        el.y = self._orig_y
        el.opacity = self._orig_opacity
        el.scale = self._orig_scale
        el.rotation = self._orig_rotation
        el._anim_x_offset = 0
        el._anim_y_offset = 0

        # Enter animation
        if t < self.enter + self.enter_dur:
            raw_t = (t - self.enter) / self.enter_dur if self.enter_dur > 0 else 1.0
            raw_t = max(0, min(1, raw_t))
            easing_fn = get_easing(self.enter_easing)
            eased_t = easing_fn(raw_t)
            anim_fn = ENTER_ANIMS.get(self.enter_anim_name, _anim_fade_in)
            anim_fn(el, eased_t)

        # Exit animation
        elif t >= self.exit_time:
            raw_t = (t - self.exit_time) / self.exit_dur if self.exit_dur > 0 else 1.0
            raw_t = max(0, min(1, raw_t))
            easing_fn = get_easing(self.exit_easing)
            eased_t = easing_fn(raw_t)
            anim_fn = EXIT_ANIMS.get(self.exit_anim_name, _anim_fade_out)
            anim_fn(el, eased_t)

        # Apply offsets
        el.x += getattr(el, '_anim_x_offset', 0)
        el.y += getattr(el, '_anim_y_offset', 0)


class Scene:
    """Timeline-based scene composition.

    Usage:
        scene = Scene(1080, 1920, fps=30, bg="#0a0a12")
        title = Text("Hello", font_size=96, color="#7c6aff", pos=(540, 960))
        scene.add(title, enter=0.0, dur=3.0, exit=4.0,
                  enter_anim="fade_up", exit_anim="fade_out")
        scene.render("output.mp4")
    """

    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        duration: Optional[float] = None,
        bg: ColorLike = "#000000",
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self._duration = duration
        self.bg = parse_color(bg)
        self._layers: List[LayerEntry] = []
        self._frame_callbacks: List[Callable] = []

    @property
    def duration(self) -> float:
        if self._duration is not None:
            return self._duration
        if not self._layers:
            return 0
        return max(l.exit_time + l.exit_dur for l in self._layers)

    @duration.setter
    def duration(self, val: float):
        self._duration = val

    def add(
        self,
        element: Element,
        enter: float = 0.0,
        dur: float = 3.0,
        exit: Optional[float] = None,
        enter_anim: str = "fade_in",
        exit_anim: str = "fade_out",
        enter_dur: float = 0.4,
        exit_dur: float = 0.4,
        enter_easing: str = "ease_out_cubic",
        exit_easing: str = "ease_in_cubic",
        z_index: int = 0,
    ) -> LayerEntry:
        """Add an element to the scene timeline."""
        exit_time = exit if exit is not None else enter + dur
        layer = LayerEntry(
            element=element,
            enter=enter,
            dur=dur,
            exit_time=exit_time,
            enter_anim=enter_anim,
            exit_anim=exit_anim,
            enter_dur=enter_dur,
            exit_dur=exit_dur,
            enter_easing=enter_easing,
            exit_easing=exit_easing,
            z_index=z_index,
        )
        self._layers.append(layer)
        return layer

    def on_frame(self, callback: Callable[[Image.Image, float, int], Image.Image]):
        """Register a per-frame callback: fn(canvas, time_sec, frame_num) -> canvas."""
        self._frame_callbacks.append(callback)

    def render_frame(self, t: float) -> Image.Image:
        """Render a single frame at time t."""
        canvas = Image.new("RGBA", (self.width, self.height), self.bg.rgba)

        # Sort by z_index
        visible = [l for l in self._layers if l.is_visible(t)]
        visible.sort(key=lambda l: l.z_index)

        for layer in visible:
            layer.apply(t)
            canvas = layer.element.render(canvas)

        return canvas

    def render(
        self,
        output_path: str,
        show_progress: bool = True,
    ) -> str:
        """Render the full scene to MP4.

        Returns the output path.
        """
        total_frames = int(self.duration * self.fps)
        if total_frames <= 0:
            raise ValueError("Scene has no duration")

        writer = VideoWriter(output_path, self.width, self.height, self.fps)

        try:
            for frame_num in range(total_frames):
                t = frame_num / self.fps
                canvas = self.render_frame(t)

                # Apply per-frame callbacks
                for cb in self._frame_callbacks:
                    canvas = cb(canvas, t, frame_num)

                writer.write_frame(canvas)

                if show_progress and frame_num % self.fps == 0:
                    pct = int(100 * frame_num / total_frames)
                    sys.stdout.write(f"\rRendering: {pct}% ({frame_num}/{total_frames})")
                    sys.stdout.flush()

            if show_progress:
                sys.stdout.write(f"\rRendering: 100% ({total_frames}/{total_frames})\n")
                sys.stdout.flush()
        finally:
            writer.close()

        return output_path

    def preview_frame(self, t: float, save_path: Optional[str] = None) -> Image.Image:
        """Render and optionally save a single frame for preview."""
        frame = self.render_frame(t)
        if save_path:
            frame.save(save_path)
        return frame
