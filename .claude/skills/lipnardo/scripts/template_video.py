#!/usr/bin/env python3
from __future__ import annotations
"""Lipnardo -- Template Video Generation

List, inspect, and generate videos from HeyGen templates with variable
injection. Supports single generation and batch from CSV/JSON.

Usage:
    # List available templates:
    template_video.py list

    # Inspect a template (see variables):
    template_video.py inspect --template-id TEMPLATE_ID

    # Generate from template with variables:
    template_video.py generate --template-id ID --variables '{"name":"John","role":"CEO"}'

    # Batch generate from CSV (columns = variable names):
    template_video.py generate --template-id ID --input prospects.csv

Options:
    --template-id ID        Template ID (required for inspect/generate)
    --variables JSON        JSON object of variable key-value pairs
    --input FILE            CSV or JSON file for batch variable injection
    --api-key KEY           HeyGen API key override
    --output-dir DIR        Output directory
    --no-download           Skip download, return video_id only
"""

import argparse
import csv
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
    output_json,
    log_json,
    error_exit,
    add_common_args,
    sanitize_id,
    HeyGenAPIError,
)


def cmd_list(args):
    """List available templates."""
    api_key = resolve_api_key(args.api_key)

    try:
        resp = api_request("GET", "/v2/templates", api_key)
        data = resp.get("data", resp)
        templates = data.get("templates", [])

        output_json({
            "success": True,
            "total": len(templates),
            "templates": [
                {
                    "template_id": t.get("template_id", ""),
                    "name": t.get("name", ""),
                    "thumbnail_url": t.get("thumbnail_image_url", ""),
                }
                for t in templates
            ],
        })
    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def cmd_inspect(args):
    """Inspect a template and show its variables."""
    api_key = resolve_api_key(args.api_key)

    try:
        resp = api_request("GET", f"/v3/template/{args.template_id}", api_key)
        data = resp.get("data", resp)

        # Extract variables from scenes
        variables = []
        scenes = data.get("scenes", [])
        for i, scene in enumerate(scenes):
            scene_vars = scene.get("variables", [])
            for var in scene_vars:
                variables.append({
                    "scene_index": i,
                    "name": var.get("name", ""),
                    "type": var.get("type", ""),
                    "properties": var.get("properties", {}),
                })

        output_json({
            "success": True,
            "template_id": args.template_id,
            "name": data.get("name", ""),
            "scene_count": len(scenes),
            "variables": variables,
            "variable_names": list(set(v["name"] for v in variables)),
        })
    except HeyGenAPIError as e:
        output_json(e.to_dict())
        sys.exit(1)


def _generate_single(api_key: str, template_id: str, variables: dict,
                      output_dir: Path, no_download: bool = False) -> dict:
    """Generate a single video from a template with variables.

    Args:
        api_key: HeyGen API key
        template_id: Template ID
        variables: Dict of variable name -> value
        output_dir: Where to save the video
        no_download: If True, skip download

    Returns:
        Result dict
    """
    # Build variables array in HeyGen format
    var_array = []
    for name, value in variables.items():
        var_entry = {"name": name}
        if isinstance(value, dict):
            # Complex variable with type and properties
            var_entry["type"] = value.get("type", "text")
            var_entry["properties"] = value.get("properties", {"content": str(value)})
        else:
            # Simple text variable
            var_entry["type"] = "text"
            var_entry["properties"] = {"content": str(value)}
        var_array.append(var_entry)

    body = {
        "template_id": template_id,
        "variables": var_array,
    }

    log_json({"action": "submit_template", "template_id": template_id,
              "variable_count": len(var_array)})

    start_time = time.time()
    resp = api_request("POST", "/v2/template/generate", api_key, body=body)
    data = resp.get("data", resp)
    video_id = data.get("video_id")

    if not video_id:
        return {"error": True, "message": f"No video_id in response: {json.dumps(resp)}"}

    if no_download:
        return {
            "success": True,
            "video_id": video_id,
            "template_id": template_id,
            "variables": variables,
        }

    # Poll and download
    result = poll_video_status(video_id, api_key)
    video_url = result.get("video_url", "")
    duration = result.get("duration", 0)
    elapsed = round(time.time() - start_time, 1)

    if not video_url:
        return {"error": True, "message": "Video completed but no URL returned",
                "video_id": video_id}

    filename = f"{sanitize_id(video_id, 'video_id')}.mp4"
    saved_path = download_file(video_url, str(output_dir / filename))
    file_size = os.path.getsize(saved_path)

    return {
        "success": True,
        "video_id": video_id,
        "template_id": template_id,
        "path": saved_path,
        "duration_seconds": duration,
        "elapsed_seconds": elapsed,
        "size_bytes": file_size,
        "variables": variables,
    }


def _load_input_rows(input_file: str) -> list[dict]:
    """Load variable rows from CSV or JSON file."""
    path = Path(input_file)
    if not path.exists():
        error_exit(f"Input file not found: {input_file}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        rows = []
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "rows" in data:
            return data["rows"]
        else:
            error_exit("JSON input must be an array or {\"rows\": [...]}")

    else:
        error_exit(f"Unsupported input format: {suffix} (use .csv or .json)")


def cmd_generate(args):
    """Generate video(s) from a template with variable injection."""
    api_key = resolve_api_key(args.api_key)
    output_dir = ensure_output_dir(args.output_dir)

    # Determine input source
    if args.input:
        # Batch from file
        rows = _load_input_rows(args.input)
        if not rows:
            error_exit("Input file contains no rows")

        log_json({"action": "batch_template", "template_id": args.template_id,
                  "rows": len(rows)})

        results = []
        for i, row in enumerate(rows):
            log_json({"action": "generating", "index": i, "total": len(rows)})
            try:
                result = _generate_single(
                    api_key, args.template_id, row, output_dir, args.no_download
                )
                results.append(result)
            except HeyGenAPIError as e:
                results.append({"error": True, "index": i, **e.to_dict()})

        succeeded = sum(1 for r in results if r.get("success"))
        output_json({
            "success": True,
            "template_id": args.template_id,
            "total": len(rows),
            "succeeded": succeeded,
            "failed": len(rows) - succeeded,
            "results": results,
        })

    elif args.variables:
        # Single from JSON variables
        try:
            variables = json.loads(args.variables)
        except json.JSONDecodeError as e:
            error_exit(f"Invalid JSON in --variables: {e}")

        try:
            result = _generate_single(
                api_key, args.template_id, variables, output_dir, args.no_download
            )
            output_json(result)
        except HeyGenAPIError as e:
            output_json(e.to_dict())
            sys.exit(1)

    else:
        error_exit("Provide --variables '{...}' or --input file.csv for template generation")


def main():
    parser = argparse.ArgumentParser(
        description="HeyGen template video generation with variable injection"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    subparsers.required = True

    # list
    p_list = subparsers.add_parser("list", help="List available templates")
    p_list.add_argument("--api-key", help="HeyGen API key")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect template variables")
    p_inspect.add_argument("--template-id", required=True, help="Template ID")
    p_inspect.add_argument("--api-key", help="HeyGen API key")

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate from template")
    p_gen.add_argument("--template-id", required=True, help="Template ID")
    p_gen.add_argument("--variables", help="JSON variables: '{\"name\":\"John\"}'")
    p_gen.add_argument("--input", help="CSV or JSON file with variable rows")
    p_gen.add_argument("--no-download", action="store_true", help="Skip download")
    add_common_args(p_gen)

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "generate":
        cmd_generate(args)


if __name__ == "__main__":
    main()
