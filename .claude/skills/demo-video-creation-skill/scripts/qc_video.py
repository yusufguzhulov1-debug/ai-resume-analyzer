#!/usr/bin/env python3
"""Inspect a rendered demo video with ffprobe and report delivery risks."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_ffprobe(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe was not found in PATH")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def first_stream(data: dict, codec_type: str) -> dict | None:
    for stream in data.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="QC a demo video render.")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--min-width", type=int, default=1920)
    parser.add_argument("--min-height", type=int, default=1080)
    parser.add_argument("--min-duration", type=float, default=45)
    parser.add_argument("--max-duration", type=float, default=95)
    parser.add_argument("--require-audio", action="store_true")
    args = parser.parse_args()

    path = Path(args.video)
    failures: list[str] = []
    warnings: list[str] = []

    if not path.exists() or path.stat().st_size == 0:
        print(f"FAIL: {path} does not exist or is empty")
        return 2

    try:
        data = run_ffprobe(path)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 2

    video = first_stream(data, "video")
    audio = first_stream(data, "audio")
    if not video:
        failures.append("No video stream found")
    else:
        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
        codec = video.get("codec_name", "unknown")
        if width < args.min_width or height < args.min_height:
            failures.append(f"Resolution {width}x{height} is below target {args.min_width}x{args.min_height}")
        if codec not in {"h264", "hevc", "prores", "vp9", "av1"}:
            warnings.append(f"Unusual video codec: {codec}")

    duration = float(data.get("format", {}).get("duration") or 0)
    if duration < args.min_duration or duration > args.max_duration:
        warnings.append(f"Duration {duration:.2f}s is outside expected range {args.min_duration}-{args.max_duration}s")

    if args.require_audio and not audio:
        failures.append("Audio was required but no audio stream was found")

    print(json.dumps(
        {
            "file": str(path),
            "size_bytes": path.stat().st_size,
            "duration_seconds": duration,
            "video": video,
            "audio": audio,
            "warnings": warnings,
            "failures": failures,
        },
        indent=2,
    ))

    if failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
