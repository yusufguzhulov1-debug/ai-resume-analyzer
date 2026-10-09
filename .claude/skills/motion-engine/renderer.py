"""Frame-by-frame PIL -> numpy -> OpenCV MP4 writer."""

from __future__ import annotations
import os
from typing import Optional

import cv2
import numpy as np
from PIL import Image


class VideoWriter:
    """Writes PIL Image frames to an MP4 file via OpenCV."""

    def __init__(
        self,
        output_path: str,
        width: int,
        height: int,
        fps: int = 30,
        codec: str = "mp4v",
    ):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = 0

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*codec)
        self._writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not self._writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for {output_path}")

    def write_frame(self, frame: Image.Image):
        """Write a single PIL Image frame."""
        # Convert RGBA -> RGB if needed
        if frame.mode == "RGBA":
            # Composite onto black background
            bg = Image.new("RGB", frame.size, (0, 0, 0))
            bg.paste(frame, mask=frame.split()[3])
            frame = bg
        elif frame.mode != "RGB":
            frame = frame.convert("RGB")

        # Resize if needed
        if frame.size != (self.width, self.height):
            frame = frame.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # PIL (RGB) -> numpy -> OpenCV (BGR)
        arr = np.array(frame)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        self._writer.write(bgr)
        self.frame_count += 1

    def write_numpy_frame(self, arr: np.ndarray):
        """Write a numpy array frame (RGB, shape HxWx3)."""
        if arr.shape[2] == 4:
            # RGBA -> RGB (composite on black)
            alpha = arr[:, :, 3:4].astype(np.float32) / 255
            rgb = arr[:, :, :3].astype(np.float32) * alpha
            arr = rgb.astype(np.uint8)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        self._writer.write(bgr)
        self.frame_count += 1

    def close(self):
        """Finalize and close the video file."""
        self._writer.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def render_frames_to_mp4(
    frames,
    output_path: str,
    width: int,
    height: int,
    fps: int = 30,
):
    """Render an iterable of PIL Images to MP4.

    Args:
        frames: Iterable of PIL Image objects
        output_path: Output MP4 path
        width: Video width
        height: Video height
        fps: Frames per second
    """
    with VideoWriter(output_path, width, height, fps) as writer:
        for frame in frames:
            writer.write_frame(frame)
    return writer.frame_count
