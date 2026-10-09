#!/usr/bin/env python3
"""Lipnardo -- Video Translation with Lip-Sync

Purpose:
    Translate HeyGen videos into other languages with automatic lip-sync
    using HeyGen's video translation API.

Usage:
    # Translate by video ID (fetches URL from API):
    python3 translate_video.py --video-id VIDEO_ID --target-lang es [--mode fast] [--output-dir DIR] [--api-key KEY]

    # Translate by direct video URL:
    python3 translate_video.py --video-url URL --target-lang fr [--mode quality] [--api-key KEY]

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import (
    resolve_api_key,
    api_request,
    poll_video_status,
    download_file,
    ensure_output_dir,
    timestamp_filename,
    output_json,
    log_json,
    error_exit,
    sanitize_id,
    HeyGenAPIError,
)

SUPPORTED_LANGUAGES = [
    "en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko", "ar",
    "hi", "ru", "nl", "pl", "sv", "tr", "id", "th", "vi", "cs",
]


def fetch_video_url(video_id: str, api_key: str) -> str:
    """Fetch the video URL from a HeyGen video ID."""
    log_json({"action": "fetch_video_url", "video_id": video_id})

    try:
        resp = api_request("GET", f"/v2/videos/{video_id}", api_key)
    except HeyGenAPIError as e:
        error_exit(
            f"Failed to fetch video {video_id}: {e.message}",
            status_code=e.status_code,
            video_id=video_id,
        )

    data = resp.get("data", resp)
    status = data.get("status", "unknown")

    if status != "completed":
        error_exit(
            f"Video is not ready for translation. Current status: {status}",
            video_id=video_id,
            status=status,
        )

    video_url = data.get("video_url", "")
    if not video_url:
        error_exit(
            "Video is completed but no video_url was returned by the API.",
            video_id=video_id,
        )

    return video_url


def submit_translation(api_key: str, video_url: str, target_lang: str,
                        mode: str = "fast") -> str:
    """Submit a video translation request via the v3 API.

    Args:
        api_key: HeyGen API key
        video_url: URL of the source video
        target_lang: ISO language code for the target language
        mode: Translation mode — 'fast'/'speed' or 'quality'/'precision'

    Returns:
        Translated video ID
    """
    # Map user-friendly mode names to v3 API values
    mode_map = {"fast": "speed", "quality": "precision", "speed": "speed", "precision": "precision"}
    api_mode = mode_map.get(mode, "speed")

    body = {
        "video_url": video_url,
        "output_language": target_lang,
        "mode": api_mode,
    }

    log_json({
        "action": "submit_translation",
        "target_lang": target_lang,
        "mode": api_mode,
        "video_url": video_url[:80],
    })

    try:
        resp = api_request("POST", "/v3/video-translations", api_key, body=body)
    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
        })
        sys.exit(1)

    data = resp.get("data", resp)
    video_id = data.get("video_id")

    if not video_id:
        error_exit(f"No video_id in translation response: {json.dumps(resp)}")

    log_json({"action": "translation_submitted", "video_id": video_id})
    return video_id


def main():
    parser = argparse.ArgumentParser(
        description="Lipnardo -- Video Translation with Lip-Sync"
    )
    parser.add_argument("--video-id",
                        help="Source HeyGen video ID (will fetch URL from API)")
    parser.add_argument("--video-url",
                        help="Direct source video URL (alternative to --video-id)")
    parser.add_argument("--target-lang", required=True,
                        help="Target language ISO code (e.g., es, fr, de, ja, zh, ko, pt, ar)")
    parser.add_argument("--mode", default="fast",
                        choices=["fast", "quality", "speed", "precision"],
                        help="Translation mode: fast/speed ($0.033/s) or quality/precision ($0.067/s)")
    parser.add_argument("--output-dir",
                        help="Output directory (default: ~/Documents/lipnardo_videos/)")
    parser.add_argument("--api-key",
                        help="HeyGen API key (or set HEYGEN_API_KEY env)")

    args = parser.parse_args()

    # Validate: must provide exactly one of --video-id or --video-url
    if args.video_id and args.video_url:
        error_exit("Provide either --video-id or --video-url, not both.")
    if not args.video_id and not args.video_url:
        error_exit("Provide either --video-id or --video-url.")

    api_key = resolve_api_key(args.api_key)
    start_time = time.time()
    original_video_id = args.video_id
    translated_video_id = None

    try:
        # Resolve video URL
        if args.video_id:
            video_url = fetch_video_url(args.video_id, api_key)
        else:
            video_url = args.video_url

        # Submit translation
        translated_video_id = submit_translation(
            api_key=api_key,
            video_url=video_url,
            target_lang=args.target_lang,
            mode=args.mode,
        )

        # Poll for completion
        log_json({"action": "polling_translation", "video_id": translated_video_id})
        result = poll_video_status(translated_video_id, api_key)

        elapsed = round(time.time() - start_time, 1)
        translated_url = result.get("video_url", "")
        duration = result.get("duration", 0)

        if not translated_url:
            error_exit(
                f"Translation completed but no video_url in response: {json.dumps(result)}",
                video_id=translated_video_id,
            )

        # Download translated video
        output_dir = ensure_output_dir(args.output_dir)
        filename = f"{sanitize_id(translated_video_id, 'video_id')}_{sanitize_id(args.target_lang, 'target_lang')}.mp4"
        output_path = str(output_dir / filename)

        log_json({
            "action": "downloading_translation",
            "video_id": translated_video_id,
            "url": translated_url[:80],
        })
        saved_path = download_file(translated_url, output_path)

        output_json({
            "success": True,
            "video_id": translated_video_id,
            "original_video_id": original_video_id,
            "target_language": args.target_lang,
            "mode": args.mode,
            "path": saved_path,
            "duration_seconds": duration,
            "elapsed_seconds": elapsed,
        })

    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "video_id": translated_video_id,
            "original_video_id": original_video_id,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
            "elapsed_seconds": round(time.time() - start_time, 1),
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
