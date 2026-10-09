#!/usr/bin/env python3
"""Lipnardo -- HeyGen Credit & Cost Tracker

Track HeyGen video generation costs, check remaining balance, estimate
batch costs, and view usage summaries.

Usage:
    credit_check.py balance [--api-key KEY]
    credit_check.py estimate --feature FEATURE --duration SECONDS
    credit_check.py estimate-batch --input FILE --feature FEATURE --avg-duration SECONDS
    credit_check.py log --feature FEATURE --duration SECONDS --video-id ID [--prompt SUMMARY]
    credit_check.py summary
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import resolve_api_key, api_request, output_json, error_exit

LEDGER_PATH = Path.home() / ".heygen" / "costs.json"

# HeyGen pricing per second of output (USD)
PRICING_PER_SECOND = {
    "avatar3": 0.0167,
    "video_agent": 0.0333,
    "photo_avatar": 0.05,
    "digital_twin": 0.0667,
    "translate_fast": 0.0333,
    "translate_quality": 0.0667,
    "tts": 0.000667,
}


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _load_ledger():
    """Load the cost ledger from disk."""
    if not LEDGER_PATH.exists():
        return {"total_cost": 0.0, "total_videos": 0, "entries": [], "daily": {}}
    with open(LEDGER_PATH, "r") as f:
        return json.load(f)


def _save_ledger(ledger):
    """Save the cost ledger atomically with restrictive permissions.

    Writes to a temp file (mode 0600), then atomically renames over the
    final path. The parent directory is created with mode 0700. This
    prevents corruption from interrupted writes and protects the cost
    history from being read by other local users.
    """
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp_path = str(LEDGER_PATH) + ".tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(ledger, f, indent=2)
    os.replace(tmp_path, str(LEDGER_PATH))


def _lookup_cost(feature, duration):
    """Calculate cost for a feature and duration."""
    if duration < 0:
        error_exit(f"Duration must be non-negative, got: {duration}")
    rate = PRICING_PER_SECOND.get(feature)
    if rate is None:
        error_exit(
            f"Unknown feature '{feature}'. Valid features: {', '.join(sorted(PRICING_PER_SECOND))}"
        )
    return round(rate * duration, 4)


def _count_rows(file_path):
    """Count data rows in a CSV or JSON file."""
    p = Path(file_path)
    if not p.exists():
        error_exit(f"Input file not found: {file_path}")

    suffix = p.suffix.lower()

    if suffix == ".csv":
        with open(p, "r", newline="") as f:
            reader = csv.reader(f)
            # Skip header row
            try:
                next(reader)
            except StopIteration:
                return 0
            return sum(1 for _ in reader)

    if suffix == ".json":
        with open(p, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return len(data)
        error_exit("JSON input must be an array of objects")

    error_exit(f"Unsupported file type '{suffix}'. Use .csv or .json")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_balance(args):
    """Check remaining HeyGen credit balance."""
    api_key = resolve_api_key(args.api_key)
    try:
        resp = api_request("GET", "/v2/user/remaining_quota", api_key)
    except Exception as e:
        error_exit(f"Failed to fetch balance: {e}")

    data = resp.get("data", resp)
    output_json({
        "command": "balance",
        "remaining_quota": data,
    })


def cmd_estimate(args):
    """Estimate cost for a single video."""
    cost = _lookup_cost(args.feature, args.duration)
    rate = PRICING_PER_SECOND[args.feature]
    output_json({
        "command": "estimate",
        "feature": args.feature,
        "duration_seconds": args.duration,
        "rate_per_second": rate,
        "estimated_cost_usd": cost,
    })


def cmd_estimate_batch(args):
    """Estimate cost for a batch of videos from a CSV/JSON file."""
    row_count = _count_rows(args.input)
    cost_per_video = _lookup_cost(args.feature, args.avg_duration)
    total_cost = round(cost_per_video * row_count, 4)
    rate = PRICING_PER_SECOND[args.feature]
    output_json({
        "command": "estimate-batch",
        "input_file": args.input,
        "row_count": row_count,
        "feature": args.feature,
        "avg_duration_seconds": args.avg_duration,
        "rate_per_second": rate,
        "cost_per_video_usd": cost_per_video,
        "total_estimated_cost_usd": total_cost,
    })


def cmd_log(args):
    """Log a completed video generation to the ledger."""
    cost = _lookup_cost(args.feature, args.duration)
    ledger = _load_ledger()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    entry = {
        "ts": now,
        "feature": args.feature,
        "duration": args.duration,
        "cost": cost,
        "video_id": args.video_id,
        "prompt": (args.prompt or "")[:100],
    }

    ledger["entries"].append(entry)
    ledger["total_cost"] = round(ledger["total_cost"] + cost, 4)
    ledger["total_videos"] += 1

    if today not in ledger["daily"]:
        ledger["daily"][today] = {"cost": 0.0, "count": 0}
    ledger["daily"][today]["count"] += 1
    ledger["daily"][today]["cost"] = round(ledger["daily"][today]["cost"] + cost, 4)

    _save_ledger(ledger)
    output_json({
        "command": "log",
        "logged": True,
        "entry": entry,
        "total_cost": ledger["total_cost"],
        "total_videos": ledger["total_videos"],
    })


def cmd_summary(args):
    """Show usage summary from the ledger."""
    ledger = _load_ledger()

    # Per-feature breakdown
    feature_breakdown = {}
    for entry in ledger.get("entries", []):
        feat = entry.get("feature", "unknown")
        if feat not in feature_breakdown:
            feature_breakdown[feat] = {"cost": 0.0, "count": 0}
        feature_breakdown[feat]["count"] += 1
        feature_breakdown[feat]["cost"] = round(
            feature_breakdown[feat]["cost"] + entry.get("cost", 0), 4
        )

    # Daily breakdown (last 14 days, sorted descending)
    daily = ledger.get("daily", {})
    sorted_days = sorted(daily.keys(), reverse=True)[:14]
    daily_breakdown = {day: daily[day] for day in sorted_days}

    output_json({
        "command": "summary",
        "total_cost_usd": ledger.get("total_cost", 0.0),
        "total_videos": ledger.get("total_videos", 0),
        "daily_breakdown": daily_breakdown,
        "feature_breakdown": feature_breakdown,
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Lipnardo -- HeyGen Credit & Cost Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # balance
    p_balance = sub.add_parser("balance", help="Check remaining HeyGen credit balance")
    p_balance.add_argument("--api-key", help="HeyGen API key (or set HEYGEN_API_KEY env)")

    # estimate
    p_estimate = sub.add_parser("estimate", help="Estimate cost for a single video")
    p_estimate.add_argument("--feature", required=True,
                            choices=sorted(PRICING_PER_SECOND.keys()),
                            help="HeyGen feature type")
    p_estimate.add_argument("--duration", required=True, type=float,
                            help="Duration in seconds")

    # estimate-batch
    p_batch = sub.add_parser("estimate-batch", help="Estimate cost for a batch of videos")
    p_batch.add_argument("--input", required=True, help="Path to CSV or JSON input file")
    p_batch.add_argument("--feature", required=True,
                         choices=sorted(PRICING_PER_SECOND.keys()),
                         help="HeyGen feature type")
    p_batch.add_argument("--avg-duration", required=True, type=float,
                         help="Average video duration in seconds")

    # log
    p_log = sub.add_parser("log", help="Log a completed video generation")
    p_log.add_argument("--feature", required=True,
                       choices=sorted(PRICING_PER_SECOND.keys()),
                       help="HeyGen feature type")
    p_log.add_argument("--duration", required=True, type=float,
                       help="Duration in seconds")
    p_log.add_argument("--video-id", required=True, help="HeyGen video ID")
    p_log.add_argument("--prompt", default="", help="Brief prompt/description (truncated to 100 chars)")

    # summary
    sub.add_parser("summary", help="Show usage summary from the ledger")

    args = parser.parse_args()
    cmds = {
        "balance": cmd_balance,
        "estimate": cmd_estimate,
        "estimate-batch": cmd_estimate_batch,
        "log": cmd_log,
        "summary": cmd_summary,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
