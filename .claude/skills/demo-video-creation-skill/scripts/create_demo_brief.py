#!/usr/bin/env python3
"""Create a reusable product demo video brief from a URL and optional context."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def valid_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("URL must start with http:// or https:// and include a host")
    return value


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a structured demo video brief JSON file.")
    parser.add_argument("url", type=valid_url, help="Company or product URL")
    parser.add_argument("--company", default="", help="Company or product name")
    parser.add_argument("--audience", default="", help="Primary audience")
    parser.add_argument("--duration", type=int, default=75, help="Target duration in seconds")
    parser.add_argument("--aspect", default="16:9", choices=["16:9", "9:16", "1:1", "4:5"], help="Delivery aspect ratio")
    parser.add_argument("--resolution", default="4K", choices=["1080p", "1440p", "4K"], help="Target render quality")
    parser.add_argument("--platform", default="", help="Primary platform, for example website, YouTube, TikTok, Video Channel")
    parser.add_argument("--features", default="", help="Comma-separated features to prioritize")
    parser.add_argument("--style", default="", help="Reference style or art direction")
    parser.add_argument("--cta", default="", help="Call to action")
    parser.add_argument("--output", default="demo-video-brief.json", help="Output JSON path")
    args = parser.parse_args()

    brief = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product_url": args.url,
        "company": args.company,
        "audience": args.audience,
        "target_duration_seconds": args.duration,
        "aspect_ratio": args.aspect,
        "target_resolution": args.resolution,
        "platform": args.platform,
        "priority_features": split_csv(args.features),
        "style_direction": args.style,
        "cta": args.cta,
        "known_assets": [],
        "access_notes": "",
        "claims_to_verify": [],
        "capture_plan": [
            "Homepage or product overview",
            "Primary product workflow setup state",
            "Primary action or input state",
            "Output, dashboard, result, or proof state",
            "Pricing, CTA, or final conversion state",
        ],
        "storyboard": [
            {"time": "0-6s", "scene": "Hook", "goal": "Name the user problem or desired outcome"},
            {"time": "6-18s", "scene": "Setup", "goal": "Show where the product workflow begins"},
            {"time": "18-34s", "scene": "Action", "goal": "Show the user doing the core action"},
            {"time": "34-48s", "scene": "Transformation", "goal": "Show the product output or changed state"},
            {"time": "48-62s", "scene": "Proof", "goal": "Show review, comparison, metric, or confidence signal"},
            {"time": "62-78s", "scene": "Breadth", "goal": "Show secondary features only after the core loop is clear"},
            {"time": "78-90s", "scene": "CTA", "goal": "End with product name, URL, and next step"},
        ],
    }

    output = Path(args.output)
    output.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
