#!/usr/bin/env python3
from __future__ import annotations
"""Lipnardo -- Photo-to-Avatar Pipeline

Full pipeline: upload photo → create avatar group → train → generate video.
Also supports checking training status and listing available avatars.

Usage:
    # Create avatar from photo (full pipeline):
    photo_avatar.py create --photo /path/to/photo.jpg --name "My Avatar"

    # Check training status:
    photo_avatar.py status --group-id GROUP_ID

    # List all avatars:
    photo_avatar.py list

    # List voices:
    photo_avatar.py voices [--language en]

    # Generate video with trained avatar:
    photo_avatar.py generate --avatar-id AVATAR_ID --script "Hello, welcome!"
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
    api_upload,
    poll_video_status,
    download_file,
    ensure_output_dir,
    output_json,
    log_json,
    error_exit,
    add_common_args,
    sanitize_id,
    HeyGenAPIError,
)


def cmd_create(args):
    """Full photo-to-avatar pipeline: upload → group → train → wait."""
    api_key = resolve_api_key(args.api_key)
    photo_path = Path(args.photo)

    if not photo_path.exists():
        error_exit(f"Photo not found: {args.photo}")

    # Validate photo extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    if photo_path.suffix.lower() not in valid_extensions:
        error_exit(f"Invalid photo format: {photo_path.suffix}. Use: {', '.join(valid_extensions)}")

    name = args.name or photo_path.stem

    try:
        # Step 1: Upload photo as asset
        log_json({"action": "uploading_photo", "file": str(photo_path)})
        upload_resp = api_upload("/v1/asset", api_key, str(photo_path))
        upload_data = upload_resp.get("data", upload_resp)
        asset_id = upload_data.get("asset_id") or upload_data.get("id")

        if not asset_id:
            error_exit(f"Upload failed — no asset_id returned: {json.dumps(upload_resp)}")

        log_json({"action": "photo_uploaded", "asset_id": asset_id})

        # Step 2: Create avatar group
        log_json({"action": "creating_avatar_group", "name": name})
        group_body = {
            "name": name,
            "image_key": asset_id,
        }
        group_resp = api_request("POST", "/v2/photo_avatar/group", api_key, body=group_body)
        group_data = group_resp.get("data", group_resp)
        group_id = group_data.get("group_id") or group_data.get("id")

        if not group_id:
            error_exit(f"Group creation failed: {json.dumps(group_resp)}")

        log_json({"action": "group_created", "group_id": group_id})

        # Step 3: Poll training status
        if args.no_wait:
            output_json({
                "success": True,
                "status": "training",
                "group_id": group_id,
                "asset_id": asset_id,
                "name": name,
                "message": "Avatar training started. Use 'status --group-id' to check progress.",
            })
            return

        log_json({"action": "waiting_for_training", "group_id": group_id})
        avatar_id = _poll_training(api_key, group_id, max_wait=args.max_wait or 3600)

        output_json({
            "success": True,
            "status": "completed",
            "group_id": group_id,
            "avatar_id": avatar_id,
            "asset_id": asset_id,
            "name": name,
            "message": f"Avatar ready! Use --avatar-id {avatar_id} in generate commands.",
        })

    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def _poll_training(api_key: str, group_id: str, max_wait: int = 3600) -> str:
    """Poll avatar training status until complete.

    Returns:
        avatar_id of the trained avatar
    """
    interval = 30  # Training takes minutes, not seconds
    elapsed = 0
    attempt = 0

    while elapsed < max_wait:
        attempt += 1
        resp = api_request("GET", f"/v2/photo_avatar/group/{group_id}", api_key)
        data = resp.get("data", resp)
        status = data.get("status", "unknown")

        log_json({
            "polling_training": True,
            "group_id": group_id,
            "attempt": attempt,
            "elapsed_seconds": elapsed,
            "training_status": status,
        })

        if status == "completed":
            avatars = data.get("avatars", [])
            if avatars:
                return avatars[0].get("avatar_id", "")
            error_exit("Training completed but no avatars returned")

        if status == "failed":
            error_msg = data.get("error", "Avatar training failed")
            raise HeyGenAPIError(200, "TRAINING_FAILED", str(error_msg),
                                 f"/v2/photo_avatar/group/{group_id}")

        time.sleep(interval)
        elapsed += interval

    raise HeyGenAPIError(0, "TRAINING_TIMEOUT",
                         f"Avatar training did not complete within {max_wait}s",
                         f"/v2/photo_avatar/group/{group_id}")


def cmd_status(args):
    """Check training status of an avatar group."""
    api_key = resolve_api_key(args.api_key)

    try:
        resp = api_request("GET", f"/v2/photo_avatar/group/{args.group_id}", api_key)
        data = resp.get("data", resp)

        output_json({
            "success": True,
            "group_id": args.group_id,
            "status": data.get("status", "unknown"),
            "avatars": data.get("avatars", []),
        })
    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def cmd_list(args):
    """List all available avatars."""
    api_key = resolve_api_key(args.api_key)

    try:
        resp = api_request("GET", "/v2/avatars", api_key)
        data = resp.get("data", resp)
        avatars = data.get("avatars", [])

        output_json({
            "success": True,
            "total": len(avatars),
            "avatars": [
                {
                    "avatar_id": a.get("avatar_id", ""),
                    "avatar_name": a.get("avatar_name", ""),
                    "gender": a.get("gender", ""),
                    "preview_image_url": a.get("preview_image_url", ""),
                }
                for a in avatars
            ],
        })
    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def cmd_voices(args):
    """List available voices."""
    api_key = resolve_api_key(args.api_key)

    try:
        resp = api_request("GET", "/v2/voices", api_key)
        data = resp.get("data", resp)
        voices = data.get("voices", [])

        # Filter by language if specified
        if args.language:
            voices = [v for v in voices
                      if args.language.lower() in v.get("language", "").lower()]

        output_json({
            "success": True,
            "total": len(voices),
            "voices": [
                {
                    "voice_id": v.get("voice_id", ""),
                    "name": v.get("name", ""),
                    "language": v.get("language", ""),
                    "gender": v.get("gender", ""),
                }
                for v in voices
            ],
        })
    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def cmd_generate(args):
    """Generate a video with a trained photo avatar."""
    api_key = resolve_api_key(args.api_key)
    output_dir = ensure_output_dir(args.output_dir)

    body = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": args.avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": args.script,
                    "voice_id": args.voice_id or "",
                },
            }
        ],
        "aspect_ratio": args.aspect_ratio or "16:9",
        "dimension": {"width": 1920, "height": 1080},
        "use_avatar_iv_model": True,  # Photo avatars use Avatar IV
    }

    if args.aspect_ratio == "9:16":
        body["dimension"] = {"width": 1080, "height": 1920}

    try:
        start_time = time.time()
        log_json({"action": "submit_photo_avatar", "avatar_id": args.avatar_id})

        resp = api_request("POST", "/v2/video/generate", api_key, body=body)
        data = resp.get("data", resp)
        video_id = data.get("video_id")

        if not video_id:
            error_exit(f"No video_id in response: {json.dumps(resp)}")

        if args.no_download:
            output_json({
                "success": True,
                "video_id": video_id,
                "avatar_id": args.avatar_id,
            })
            return

        # Poll and download
        result = poll_video_status(video_id, api_key)
        video_url = result.get("video_url", "")
        duration = result.get("duration", 0)
        elapsed = round(time.time() - start_time, 1)

        if video_url:
            filename = f"{sanitize_id(video_id, 'video_id')}.mp4"
            saved_path = download_file(video_url, str(output_dir / filename))
            file_size = os.path.getsize(saved_path)
        else:
            saved_path = ""
            file_size = 0

        output_json({
            "success": True,
            "video_id": video_id,
            "avatar_id": args.avatar_id,
            "path": saved_path,
            "duration_seconds": duration,
            "elapsed_seconds": elapsed,
            "size_bytes": file_size,
        })

    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="HeyGen photo-to-avatar pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    subparsers.required = True

    # create
    p_create = subparsers.add_parser("create", help="Create avatar from photo")
    p_create.add_argument("--photo", required=True, help="Path to photo file")
    p_create.add_argument("--name", help="Avatar name (default: filename)")
    p_create.add_argument("--no-wait", action="store_true",
                          help="Don't wait for training to complete")
    p_create.add_argument("--max-wait", type=int, default=3600,
                          help="Max training wait in seconds (default: 3600)")
    p_create.add_argument("--api-key", help="HeyGen API key")

    # status
    p_status = subparsers.add_parser("status", help="Check training status")
    p_status.add_argument("--group-id", required=True, help="Avatar group ID")
    p_status.add_argument("--api-key", help="HeyGen API key")

    # list
    p_list = subparsers.add_parser("list", help="List available avatars")
    p_list.add_argument("--api-key", help="HeyGen API key")

    # voices
    p_voices = subparsers.add_parser("voices", help="List available voices")
    p_voices.add_argument("--language", help="Filter by language (e.g., en, es)")
    p_voices.add_argument("--api-key", help="HeyGen API key")

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate video with avatar")
    p_gen.add_argument("--avatar-id", required=True, help="Trained avatar ID")
    p_gen.add_argument("--script", required=True, help="Text for the avatar to speak")
    p_gen.add_argument("--voice-id", help="Voice ID (optional)")
    p_gen.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"])
    p_gen.add_argument("--no-download", action="store_true")
    add_common_args(p_gen)

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "status": cmd_status,
        "list": cmd_list,
        "voices": cmd_voices,
        "generate": cmd_generate,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
