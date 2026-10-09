#!/usr/bin/env python3
"""Lipnardo -- HeyGen Asset Manager

Purpose:
    Upload, list, and inspect HeyGen assets (images, videos, audio files)
    used in avatar video generation.

Usage:
    # Upload an asset:
    python3 asset_manager.py upload --file /path/to/image.png [--type image] [--api-key KEY]

    # List assets:
    python3 asset_manager.py list [--type image|video|audio] [--limit 50] [--api-key KEY]

    # Get asset info:
    python3 asset_manager.py info --asset-id ID [--api-key KEY]

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import (
    resolve_api_key,
    api_request,
    api_upload,
    output_json,
    log_json,
    error_exit,
    HeyGenAPIError,
)

# Extension-to-type mapping for auto-detection
EXTENSION_TYPE_MAP = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".mp4": "video",
    ".mov": "video",
    ".avi": "video",
    ".mkv": "video",
    ".webm": "video",
    ".mp3": "audio",
    ".wav": "audio",
    ".aac": "audio",
    ".ogg": "audio",
    ".flac": "audio",
    ".m4a": "audio",
}


def detect_asset_type(file_path: str) -> str:
    """Auto-detect asset type from file extension.

    Returns:
        Asset type string: 'image', 'video', or 'audio'
    """
    ext = Path(file_path).suffix.lower()
    asset_type = EXTENSION_TYPE_MAP.get(ext)
    if not asset_type:
        error_exit(
            f"Cannot auto-detect asset type for extension '{ext}'. "
            f"Supported: {', '.join(sorted(EXTENSION_TYPE_MAP.keys()))}. "
            "Use --type to specify explicitly."
        )
    return asset_type


# ---------------------------------------------------------------------------
# Upload subcommand
# ---------------------------------------------------------------------------

def cmd_upload(args):
    """Upload a file to HeyGen as an asset."""
    api_key = resolve_api_key(args.api_key)

    file_path = args.file
    if not os.path.isfile(file_path):
        error_exit(f"File not found: {file_path}")

    # Determine asset type
    asset_type = args.type if args.type else detect_asset_type(file_path)
    filename = os.path.basename(file_path)

    log_json({
        "action": "upload_asset",
        "file": file_path,
        "type": asset_type,
        "filename": filename,
    })

    try:
        resp = api_upload(
            path="/v1/asset",
            api_key=api_key,
            file_path=file_path,
            fields={"type": asset_type},
        )
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

    output_json({
        "success": True,
        "asset_id": data.get("asset_id", data.get("id", "")),
        "url": data.get("url", ""),
        "type": asset_type,
        "filename": filename,
    })


# ---------------------------------------------------------------------------
# List subcommand
# ---------------------------------------------------------------------------

def cmd_list(args):
    """List HeyGen assets with optional type filter."""
    api_key = resolve_api_key(args.api_key)
    limit = args.limit if args.limit else 50

    # Build query path with parameters
    path = f"/v1/asset/list?limit={limit}"
    if args.type:
        path += f"&type={args.type}"

    log_json({
        "action": "list_assets",
        "type_filter": args.type,
        "limit": limit,
    })

    try:
        resp = api_request("GET", path, api_key)
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

    # Extract asset list — API may nest under different keys
    if isinstance(data, list):
        assets_raw = data
    elif isinstance(data, dict):
        assets_raw = data.get("assets", data.get("list", data.get("items", [])))
    else:
        assets_raw = []

    # Normalize asset entries
    assets = []
    for a in assets_raw:
        assets.append({
            "asset_id": a.get("asset_id", a.get("id", "")),
            "url": a.get("url", ""),
            "type": a.get("type", ""),
            "created_at": a.get("created_at", a.get("create_time", "")),
        })

    output_json({
        "success": True,
        "total": len(assets),
        "type_filter": args.type,
        "assets": assets,
    })


# ---------------------------------------------------------------------------
# Info subcommand
# ---------------------------------------------------------------------------

def cmd_info(args):
    """Get detailed information about a specific asset."""
    api_key = resolve_api_key(args.api_key)

    log_json({"action": "asset_info", "asset_id": args.asset_id})

    try:
        resp = api_request("GET", f"/v1/asset/{args.asset_id}", api_key)
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

    output_json({
        "success": True,
        "asset_id": data.get("asset_id", data.get("id", args.asset_id)),
        "url": data.get("url", ""),
        "type": data.get("type", ""),
        "filename": data.get("filename", data.get("name", "")),
        "created_at": data.get("created_at", data.get("create_time", "")),
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Lipnardo -- HeyGen Asset Manager (upload, list, info)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # upload
    p_upload = sub.add_parser("upload", help="Upload a file as a HeyGen asset")
    p_upload.add_argument("--file", required=True,
                          help="Path to file to upload")
    p_upload.add_argument("--type", choices=["image", "video", "audio"],
                          help="Asset type (auto-detected from extension if not specified)")
    p_upload.add_argument("--api-key",
                          help="HeyGen API key (or set HEYGEN_API_KEY env)")

    # list
    p_list = sub.add_parser("list", help="List HeyGen assets")
    p_list.add_argument("--type", choices=["image", "video", "audio"],
                        help="Filter by asset type")
    p_list.add_argument("--limit", type=int, default=50,
                        help="Maximum number of assets to return (default: 50)")
    p_list.add_argument("--api-key",
                        help="HeyGen API key (or set HEYGEN_API_KEY env)")

    # info
    p_info = sub.add_parser("info", help="Get info about a specific asset")
    p_info.add_argument("--asset-id", required=True,
                        help="HeyGen asset ID")
    p_info.add_argument("--api-key",
                        help="HeyGen API key (or set HEYGEN_API_KEY env)")

    args = parser.parse_args()

    cmds = {
        "upload": cmd_upload,
        "list": cmd_list,
        "info": cmd_info,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
