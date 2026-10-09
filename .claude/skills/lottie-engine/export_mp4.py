"""Export Animation to MP4 via motion_engine renderer."""

from __future__ import annotations
import sys
from typing import TYPE_CHECKING

from PIL import Image

from motion_engine.color import parse_color
from motion_engine.renderer import VideoWriter

if TYPE_CHECKING:
    from .schema import Animation


def export_animation_mp4(
    anim: "Animation",
    output_path: str,
    show_progress: bool = True,
) -> str:
    """Render an Animation to MP4.

    Each frame:
    1. Create background canvas
    2. For each layer (sorted by z_index), apply keyframed properties to element
    3. Render element onto canvas
    4. Write frame to video
    """
    total_frames = int(anim.duration * anim.fps)
    if total_frames <= 0:
        raise ValueError("Animation has no duration")

    bg = parse_color(anim.bg)
    writer = VideoWriter(output_path, anim.width, anim.height, anim.fps)

    try:
        sorted_layers = sorted(anim.layers, key=lambda l: l.z_index)

        for frame_num in range(total_frames):
            t = frame_num / anim.fps
            canvas = Image.new("RGBA", (anim.width, anim.height), bg.rgba)

            for layer in sorted_layers:
                if layer.element is not None:
                    layer.apply_to_element(t)
                    canvas = layer.element.render(canvas)

            writer.write_frame(canvas)

            if show_progress and frame_num % anim.fps == 0:
                pct = int(100 * frame_num / total_frames)
                sys.stdout.write(f"\rRendering: {pct}% ({frame_num}/{total_frames})")
                sys.stdout.flush()

        if show_progress:
            sys.stdout.write(f"\rRendering: 100% ({total_frames}/{total_frames})\n")
            sys.stdout.flush()
    finally:
        writer.close()

    return output_path
