#!/usr/bin/env python3
from __future__ import annotations
"""Lipnardo -- Video Generation (Agent + Studio modes)

Generate HeyGen avatar videos using either the AI-driven Video Agent (v3)
or the precise multi-scene Studio API (v2).

Usage:
    # Video Agent mode (AI-driven, prompt-to-video):
    generate_video.py --mode agent --prompt "A woman explaining quarterly results"

    # Video Agent with specific avatar/voice:
    generate_video.py --mode agent --prompt "Welcome to our company" --avatar-id Kristin_public_3_20240108 --voice-id en-US-JennyNeural

    # Studio mode (multi-scene, precise control):
    generate_video.py --mode studio --config scenes.json

    # Skip download, just return video_id:
    generate_video.py --mode agent --prompt "Test video" --no-download

Options:
    --mode {agent,studio}   Generation mode (required)
    --prompt TEXT            Script/prompt text (required for agent mode)
    --config FILE            JSON scene config (required for studio mode)
    --avatar-id ID          Avatar ID (optional, AI selects in agent mode)
    --voice-id ID           Voice ID (optional)
    --aspect-ratio RATIO    16:9 or 9:16 (default: 16:9)
    --resolution RES        720p or 1080p (default: 1080p)
    --test                  Generate watermarked test video (free)
    --no-download           Skip download, return video_id only
    --callback-id ID        Webhook callback correlation ID
    --api-key KEY           HeyGen API key override
    --output-dir DIR        Output directory
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
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


# ---------------------------------------------------------------------------
# Video Agent (v3)
# ---------------------------------------------------------------------------

def submit_agent_video(api_key: str, prompt: str,
                       avatar_id: str | None = None,
                       voice_id: str | None = None,
                       aspect_ratio: str = "16:9",
                       test: bool = False,
                       callback_id: str | None = None) -> str:
    """Submit a video generation request via the Video Agent API (v3).

    Returns:
        video_id string
    """
    body = {"prompt": prompt}

    if avatar_id:
        body["avatar_id"] = avatar_id
    if voice_id:
        body["voice_id"] = voice_id
    if aspect_ratio:
        body["aspect_ratio"] = aspect_ratio
    if test:
        body["test"] = True
    if callback_id:
        body["callback_id"] = callback_id

    log_json({"action": "submit", "mode": "agent", "prompt": prompt[:80]})

    resp = api_request("POST", "/v3/video-agents", api_key, body=body)
    data = resp.get("data", resp)
    video_id = data.get("video_id")

    if not video_id:
        error_exit(f"No video_id in response: {json.dumps(resp)}")

    log_json({"action": "submitted", "video_id": video_id})
    return video_id


# ---------------------------------------------------------------------------
# Studio Video (v2)
# ---------------------------------------------------------------------------

def submit_studio_video(api_key: str, config: dict,
                        dimension: dict | None = None,
                        aspect_ratio: str = "16:9",
                        test: bool = False,
                        callback_id: str | None = None) -> str:
    """Submit a video generation request via the Studio API (v2).

    Config should contain a 'scenes' or 'video_inputs' array with scene
    definitions including character, voice, and background settings.

    Returns:
        video_id string
    """
    # Accept either 'scenes' or 'video_inputs' key
    video_inputs = config.get("video_inputs", config.get("scenes", []))
    if not video_inputs:
        error_exit("Studio config must contain 'scenes' or 'video_inputs' array")

    body = {
        "video_inputs": video_inputs,
        "aspect_ratio": aspect_ratio,
    }

    # Set dimension based on aspect ratio if not specified
    if dimension:
        body["dimension"] = dimension
    elif aspect_ratio == "9:16":
        body["dimension"] = {"width": 1080, "height": 1920}
    else:
        body["dimension"] = {"width": 1920, "height": 1080}

    if test:
        body["test"] = True
    if callback_id:
        body["callback_id"] = callback_id

    # Copy through any additional top-level config keys
    for key in ("title", "caption", "use_avatar_iv_model"):
        if key in config:
            body[key] = config[key]

    log_json({"action": "submit", "mode": "studio", "scenes": len(video_inputs)})

    resp = api_request("POST", "/v2/video/generate", api_key, body=body)
    data = resp.get("data", resp)
    video_id = data.get("video_id")

    if not video_id:
        error_exit(f"No video_id in response: {json.dumps(resp)}")

    log_json({"action": "submitted", "video_id": video_id})
    return video_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate HeyGen avatar videos (Agent or Studio mode)"
    )
    parser.add_argument("--mode", required=True, choices=["agent", "studio"],
                        help="Generation mode: agent (AI-driven) or studio (multi-scene)")
    parser.add_argument("--prompt", help="Script/prompt text (required for agent mode)")
    parser.add_argument("--config", help="JSON scene config file (required for studio mode)")
    parser.add_argument("--avatar-id", help="Avatar ID (optional)")
    parser.add_argument("--voice-id", help="Voice ID (optional)")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", default="1080p", choices=["720p", "1080p"],
                        help="Resolution (default: 1080p)")
    parser.add_argument("--test", action="store_true",
                        help="Generate watermarked test video (free)")
    parser.add_argument("--no-download", action="store_true",
                        help="Skip download, return video_id only")
    parser.add_argument("--callback-id", help="Webhook callback correlation ID")
    parser.add_argument("--api-key", help="HeyGen API key (or set HEYGEN_API_KEY)")
    parser.add_argument("--output-dir",
                        help="Output directory (default: ~/Documents/lipnardo_videos/)")

    args = parser.parse_args()

    # Validate mode-specific requirements
    if args.mode == "agent" and not args.prompt:
        parser.error("--prompt is required for agent mode")
    if args.mode == "studio" and not args.config:
        parser.error("--config is required for studio mode")

    # Resolve API key
    api_key = resolve_api_key(args.api_key)

    # Submit video
    start_time = time.time()
    video_id = None

    try:
        if args.mode == "agent":
            video_id = submit_agent_video(
                api_key=api_key,
                prompt=args.prompt,
                avatar_id=args.avatar_id,
                voice_id=args.voice_id,
                aspect_ratio=args.aspect_ratio,
                test=args.test,
                callback_id=args.callback_id,
            )
        else:
            # Load studio config
            config_path = Path(args.config)
            if not config_path.exists():
                error_exit(f"Config file not found: {args.config}")
            with open(config_path, "r") as f:
                config = json.load(f)

            video_id = submit_studio_video(
                api_key=api_key,
                config=config,
                aspect_ratio=args.aspect_ratio,
                test=args.test,
                callback_id=args.callback_id,
            )

        # If callback_id is set, user wants webhook-based async — don't poll
        if args.callback_id:
            output_json({
                "success": True,
                "video_id": video_id,
                "mode": args.mode,
                "async": True,
                "message": f"Video submitted. Will notify via webhook callback_id={args.callback_id}",
            })
            return

        # If no-download, just return the video_id
        if args.no_download:
            output_json({
                "success": True,
                "video_id": video_id,
                "mode": args.mode,
                "message": "Video submitted. Use --video-id with download_video.py to download later.",
            })
            return

        # Poll for completion
        log_json({"action": "polling", "video_id": video_id})
        result = poll_video_status(video_id, api_key)

        elapsed = round(time.time() - start_time, 1)
        video_url = result.get("video_url", "")
        duration = result.get("duration", 0)

        if not video_url:
            error_exit(f"Video completed but no video_url in response: {json.dumps(result)}")

        # Download
        output_dir = ensure_output_dir(args.output_dir)
        filename = f"{sanitize_id(video_id, 'video_id')}.mp4"
        output_path = str(output_dir / filename)

        log_json({"action": "downloading", "video_id": video_id, "url": video_url[:80]})
        saved_path = download_file(video_url, output_path)

        file_size = os.path.getsize(saved_path)

        output_json({
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "path": saved_path,
            "duration_seconds": duration,
            "elapsed_seconds": elapsed,
            "mode": args.mode,
            "size_bytes": file_size,
            "test": args.test,
        })

    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "video_id": video_id,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
            "elapsed_seconds": round(time.time() - start_time, 1),
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
