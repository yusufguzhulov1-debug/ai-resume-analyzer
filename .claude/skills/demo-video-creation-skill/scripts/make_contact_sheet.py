#!/usr/bin/env python3
"""Create a contact sheet from a video using FFmpeg."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} was not found in PATH")
    return path


def duration_seconds(ffprobe: str, video: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-of", "json", str(video)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration") or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a tiled contact sheet for video review.")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("--output", default="contact-sheet.jpg", help="Output image path")
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=480)
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists() or video.stat().st_size == 0:
        raise SystemExit(f"Input video missing or empty: {video}")

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    duration = max(duration_seconds(ffprobe, video), 1)
    frames = max(args.cols * args.rows, 1)
    interval = max(duration / (frames + 1), 0.5)
    fps_expr = f"fps=1/{math.ceil(interval)}"
    vf = f"{fps_expr},scale={args.thumb_width}:-1,tile={args.cols}x{args.rows}"

    subprocess.run(
        [ffmpeg, "-y", "-i", str(video), "-vf", vf, "-frames:v", "1", "-update", "1", str(args.output)],
        check=True,
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
