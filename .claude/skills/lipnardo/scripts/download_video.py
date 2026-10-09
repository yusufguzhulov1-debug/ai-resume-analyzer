#!/usr/bin/env python3
from __future__ import annotations
"""Lipnardo -- Download HeyGen Video

Purpose:
    Download generated HeyGen videos before their 7-day URL expiry.
    Supports downloading by video ID (fetches URL from API) or by direct URL.

Usage:
    # Download by video ID (fetches video_url from API):
    python3 download_video.py --video-id VIDEO_ID [--output-dir DIR] [--api-key KEY]

    # Download by direct URL:
    python3 download_video.py --url URL --output /path/to/file.mp4

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import (
    resolve_api_key,
    api_request,
    download_file,
    ensure_output_dir,
    timestamp_filename,
    output_json,
    log_json,
    error_exit,
    sanitize_id,
    HeyGenAPIError,
)


def download_by_video_id(video_id: str, api_key: str | None, output_dir: str | None) -> None:
    """Fetch video metadata from the API and download the completed video."""
    api_key = resolve_api_key(api_key)

    log_json({"action": "fetch_video_status", "video_id": video_id})

    try:
        resp = api_request("GET", f"/v2/videos/{video_id}", api_key)
    except HeyGenAPIError as e:
        error_exit(e.message, status_code=e.status_code, video_id=video_id)

    data = resp.get("data", resp)
    status = data.get("status", "unknown")

    if status != "completed":
        error_exit(
            f"Video is not ready for download. Current status: {status}",
            video_id=video_id,
            status=status,
        )

    video_url = data.get("video_url", "")
    if not video_url:
        error_exit(
            "Video is completed but no video_url was returned by the API.",
            video_id=video_id,
        )

    out_dir = ensure_output_dir(output_dir)
    output_path = str(out_dir / f"{sanitize_id(video_id, 'video_id')}.mp4")

    log_json({"action": "downloading", "video_id": video_id, "output": output_path})

    try:
        saved_path = download_file(video_url, output_path)
    except Exception as e:
        msg = str(e)
        if "404" in msg or "410" in msg:
            error_exit(
                f"Download failed (URL may have expired): {msg}. "
                f"Try re-fetching the URL with: --video-id {video_id}",
                video_id=video_id,
                url=video_url,
            )
        error_exit(
            f"Download failed: {msg}",
            video_id=video_id,
            url=video_url,
        )

    size_bytes = os.path.getsize(saved_path)
    output_json({
        "success": True,
        "path": saved_path,
        "size_bytes": size_bytes,
        "video_id": video_id,
    })


def download_by_url(url: str, output_path: str) -> None:
    """Download a video directly from a URL to a specified path."""
    log_json({"action": "downloading", "url": url, "output": output_path})

    try:
        saved_path = download_file(url, output_path)
    except Exception as e:
        msg = str(e)
        if "404" in msg or "410" in msg:
            error_exit(
                f"Download failed (URL may have expired): {msg}. "
                "If this is a HeyGen video, try re-fetching via --video-id instead.",
                url=url,
            )
        error_exit(
            f"Download failed: {msg}",
            url=url,
        )

    size_bytes = os.path.getsize(saved_path)
    output_json({
        "success": True,
        "path": saved_path,
        "size_bytes": size_bytes,
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download HeyGen videos before their 7-day URL expiry.",
    )
    parser.add_argument(
        "--video-id",
        help="HeyGen video ID to fetch and download",
    )
    parser.add_argument(
        "--url",
        help="Direct download URL",
    )
    parser.add_argument(
        "--output",
        help="Exact output file path (required with --url)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (used with --video-id, default: ~/Documents/lipnardo_videos/)",
    )
    parser.add_argument(
        "--api-key",
        help="HeyGen API key override (or set HEYGEN_API_KEY env)",
    )

    args = parser.parse_args()

    # Validation: must provide exactly one of --video-id or --url
    if args.video_id and args.url:
        error_exit("Provide either --video-id or --url, not both.")
    if not args.video_id and not args.url:
        error_exit("Provide either --video-id or --url.")

    # Validation: --url requires --output
    if args.url and not args.output:
        error_exit("--output is required when using --url.")

    if args.video_id:
        download_by_video_id(args.video_id, args.api_key, args.output_dir)
    else:
        download_by_url(args.url, args.output)


if __name__ == "__main__":
    main()
