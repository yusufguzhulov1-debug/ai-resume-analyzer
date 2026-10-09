"""Slide transition effects — wipe, dissolve, zoom, parallax."""

from __future__ import annotations
import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from motion_engine.scene import Scene
from motion_engine.elements import Element, Rect
from motion_engine.color import ColorLike, parse_color
from motion_engine.easing import get_easing


def wipe_transition(
    scene: Scene,
    start: float,
    dur: float = 0.6,
    direction: str = "left",
    color: ColorLike = "#000000",
    easing: str = "ease_in_out_cubic",
) -> float:
    """Wipe transition: a solid color bar sweeps across the screen.

    Directions: left, right, up, down.
    Returns end time.
    """
    w, h = scene.width, scene.height
    wipe = Rect(w * 2, h * 2, color=color, pos=(w // 2, h // 2))
    easing_fn = get_easing(easing)

    offsets = {
        "left": ((-w, 0), (w * 2, 0)),
        "right": ((w * 2, 0), (-w, 0)),
        "up": ((0, -h), (0, h * 2)),
        "down": ((0, h * 2), (0, -h)),
    }
    start_pos, end_pos = offsets.get(direction, offsets["left"])

    def update_wipe(canvas, t, frame_num):
        if start <= t < start + dur:
            progress = easing_fn((t - start) / dur)
            wipe.x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress + w // 2
            wipe.y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress + h // 2
        return canvas

    scene.add(wipe, enter=start, dur=dur, exit=start + dur,
              enter_anim="none", exit_anim="none", enter_dur=0.01, exit_dur=0.01, z_index=100)
    scene.on_frame(update_wipe)
    return start + dur


def dissolve_transition(
    scene: Scene,
    start: float,
    dur: float = 0.8,
    color: ColorLike = "#000000",
) -> float:
    """Simple dissolve (fade through black).

    Returns end time.
    """
    overlay = Rect(scene.width, scene.height, color=color, pos=(scene.width // 2, scene.height // 2))
    half = dur / 2

    scene.add(overlay, enter=start, dur=dur, exit=start + dur,
              enter_anim="fade_in", exit_anim="fade_out",
              enter_dur=half, exit_dur=half, z_index=100)
    return start + dur


def zoom_transition(
    scene: Scene,
    start: float,
    dur: float = 0.6,
    zoom_target: Tuple[float, float] = (0.5, 0.5),
    max_zoom: float = 3.0,
    color: ColorLike = "#000000",
) -> float:
    """Zoom-in transition that zooms into a point then zooms out.

    Returns end time.
    """
    overlay = Rect(scene.width, scene.height, color=color, pos=(scene.width // 2, scene.height // 2))

    scene.add(overlay, enter=start, dur=dur, exit=start + dur,
              enter_anim="scale_in", exit_anim="scale_out",
              enter_dur=dur / 2, exit_dur=dur / 2,
              enter_easing="ease_in_expo", exit_easing="ease_out_expo",
              z_index=100)
    return start + dur


def slide_transition(
    scene: Scene,
    start: float,
    dur: float = 0.5,
    direction: str = "left",
    easing: str = "ease_in_out_cubic",
) -> float:
    """Slide transition effect — content slides in from one direction.

    This is a visual indicator; actual content timing should align separately.
    Returns end time.
    """
    return wipe_transition(scene, start, dur, direction, "#0a0a12", easing)
