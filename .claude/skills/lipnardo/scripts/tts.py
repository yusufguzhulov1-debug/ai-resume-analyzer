#!/usr/bin/env python3
"""Lipnardo -- Text-to-Speech via HeyGen Starfish TTS Engine

Purpose:
    Convert text to speech audio using HeyGen's TTS API. Supports voice
    selection with speed/pitch control, and listing available voices.

Usage:
    # Generate speech audio:
    python3 tts.py synthesize --text "Hello world" --voice-id en-US-JennyNeural [--speed 1.0] [--pitch 0] [--output FILE] [--api-key KEY]

    # List available voices:
    python3 tts.py list-voices [--language en] [--api-key KEY]

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import os
import sys
import time
from pathlib import Path

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
    HeyGenAPIError,
)

DEFAULT_TTS_DIR = Path.home() / "Documents" / "lipnardo_videos" / "tts"


# ---------------------------------------------------------------------------
# Synthesize subcommand
# ---------------------------------------------------------------------------

def cmd_synthesize(args):
    """Generate speech audio from text via HeyGen TTS."""
    api_key = resolve_api_key(args.api_key)

    if not args.text or not args.text.strip():
        error_exit("--text must not be empty.")

    if not args.voice_id or not args.voice_id.strip():
        error_exit("--voice-id is required for synthesis.")

    speed = args.speed if args.speed is not None else 1.0
    pitch = args.pitch if args.pitch is not None else 0

    body = {
        "text": args.text,
        "voice_id": args.voice_id,
        "speed": speed,
        "pitch": pitch,
    }

    log_json({
        "action": "tts_synthesize",
        "voice_id": args.voice_id,
        "text_length": len(args.text),
        "speed": speed,
        "pitch": pitch,
    })

    start_time = time.time()

    try:
        resp = api_request("POST", "/v1/audio/text_to_speech", api_key, body=body)
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
    audio_url = data.get("url", "")
    duration = data.get("duration", 0)

    if not audio_url:
        error_exit(f"No audio URL in response: {resp}")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        out_dir = Path(args.output_dir) if args.output_dir else DEFAULT_TTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = timestamp_filename(prefix="tts", ext=".mp3")
        output_path = str(out_dir / filename)

    log_json({"action": "downloading_audio", "url": audio_url[:80], "output": output_path})

    try:
        saved_path = download_file(audio_url, output_path)
    except Exception as e:
        error_exit(f"Failed to download audio: {e}", url=audio_url)

    elapsed = round(time.time() - start_time, 1)
    text_preview = args.text[:50] + ("..." if len(args.text) > 50 else "")

    output_json({
        "success": True,
        "path": saved_path,
        "duration_seconds": duration,
        "voice_id": args.voice_id,
        "text_preview": text_preview,
        "speed": speed,
        "pitch": pitch,
        "elapsed_seconds": elapsed,
    })


# ---------------------------------------------------------------------------
# List voices subcommand
# ---------------------------------------------------------------------------

def cmd_list_voices(args):
    """List available TTS voices, optionally filtered by language."""
    api_key = resolve_api_key(args.api_key)

    log_json({"action": "list_voices", "language_filter": args.language})

    try:
        resp = api_request("GET", "/v2/voices", api_key)
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

    # The voices endpoint may return data as a list or nested under a key
    if isinstance(data, list):
        voices = data
    elif isinstance(data, dict):
        voices = data.get("voices", data.get("list", []))
    else:
        voices = []

    # Filter by language if requested
    if args.language:
        lang_filter = args.language.lower()
        voices = [
            v for v in voices
            if lang_filter in (v.get("language", "") or "").lower()
            or (v.get("voice_id", "") or "").lower().startswith(lang_filter)
        ]

    # Extract relevant fields
    voice_list = []
    for v in voices:
        voice_list.append({
            "voice_id": v.get("voice_id", ""),
            "name": v.get("name", v.get("display_name", "")),
            "language": v.get("language", ""),
            "gender": v.get("gender", ""),
        })

    output_json({
        "success": True,
        "total": len(voice_list),
        "language_filter": args.language,
        "voices": voice_list,
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Lipnardo -- Text-to-Speech via HeyGen Starfish TTS Engine"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # synthesize
    p_synth = sub.add_parser("synthesize", help="Generate speech audio from text")
    p_synth.add_argument("--text", required=True, help="Text to synthesize")
    p_synth.add_argument("--voice-id", required=True, help="TTS voice ID (e.g., en-US-JennyNeural)")
    p_synth.add_argument("--speed", type=float, default=1.0,
                         help="Speech speed multiplier (default: 1.0)")
    p_synth.add_argument("--pitch", type=int, default=0,
                         help="Pitch adjustment (default: 0)")
    p_synth.add_argument("--output", help="Exact output file path")
    p_synth.add_argument("--output-dir",
                         help="Output directory (default: ~/Documents/lipnardo_videos/tts/)")
    p_synth.add_argument("--api-key", help="HeyGen API key (or set HEYGEN_API_KEY env)")

    # list-voices
    p_voices = sub.add_parser("list-voices", help="List available TTS voices")
    p_voices.add_argument("--language", help="Filter voices by language (e.g., en, es, fr)")
    p_voices.add_argument("--api-key", help="HeyGen API key (or set HEYGEN_API_KEY env)")

    args = parser.parse_args()

    cmds = {
        "synthesize": cmd_synthesize,
        "list-voices": cmd_list_voices,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
