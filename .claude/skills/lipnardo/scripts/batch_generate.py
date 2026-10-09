#!/usr/bin/env python3
from __future__ import annotations
"""Lipnardo -- Batch Video Generation Queue Manager

Purpose:
    Batch-generate HeyGen avatar videos from a CSV or JSON input file with
    concurrency control, retry logic, crash-recoverable manifests, and
    progress reporting.

Usage:
    # Agent mode -- each CSV row has a "prompt" column:
    python3 batch_generate.py --input data.csv --mode agent \
        [--max-concurrent 3] [--max-retries 3] [--output-dir DIR] [--api-key KEY]

    # Template mode -- CSV columns match template variable names:
    python3 batch_generate.py --input data.csv --mode template \
        --template-id TEMPLATE_ID [options]

    # Resume a batch from an existing manifest (crash recovery):
    python3 batch_generate.py --resume manifest.json

    # Check status/progress of a batch:
    python3 batch_generate.py --status manifest.json

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import csv
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
# Input Loading
# ---------------------------------------------------------------------------

def load_input(input_file: str) -> list[dict]:
    """Load input rows from a CSV or JSON file.

    CSV: first row is headers, each subsequent row becomes a dict.
    JSON: expects a list of dicts.

    Returns:
        List of row dicts.
    """
    path = Path(input_file)
    if not path.exists():
        error_exit(f"Input file not found: {input_file}")

    ext = path.suffix.lower()

    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            error_exit("JSON input must be a list of objects")
        return data

    # Default: CSV
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    if not rows:
        error_exit(f"No data rows found in {input_file}")
    return rows


# ---------------------------------------------------------------------------
# Manifest Management
# ---------------------------------------------------------------------------

def create_manifest(input_file: str, mode: str, template_id: str | None,
                    max_concurrent: int, output_dir: str,
                    rows: list[dict]) -> dict:
    """Create a new batch manifest from input rows."""
    manifest = {
        "created": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "template_id": template_id,
        "input_file": os.path.abspath(input_file),
        "max_concurrent": max_concurrent,
        "total": len(rows),
        "completed": 0,
        "failed": 0,
        "pending": len(rows),
        "output_dir": output_dir,
        "jobs": [],
    }

    for i, row in enumerate(rows):
        manifest["jobs"].append({
            "index": i,
            "status": "pending",
            "video_id": None,
            "path": None,
            "attempts": 0,
            "error": None,
            "input_row": row,
        })

    return manifest


def save_manifest(manifest: dict, manifest_path: str) -> None:
    """Write manifest to disk atomically (write tmp then rename)."""
    tmp_path = manifest_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp_path, manifest_path)


def load_manifest(manifest_path: str) -> dict:
    """Load an existing manifest from disk."""
    path = Path(manifest_path)
    if not path.exists():
        error_exit(f"Manifest file not found: {manifest_path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_manifest_counts(manifest: dict) -> None:
    """Recalculate completed/failed/pending counts from job statuses."""
    completed = 0
    failed = 0
    pending = 0
    for job in manifest["jobs"]:
        if job["status"] == "completed":
            completed += 1
        elif job["status"] == "failed":
            failed += 1
        else:
            pending += 1
    manifest["completed"] = completed
    manifest["failed"] = failed
    manifest["pending"] = pending


# ---------------------------------------------------------------------------
# Video Submission
# ---------------------------------------------------------------------------

def submit_video(job: dict, mode: str, template_id: str | None,
                 api_key: str) -> str:
    """Submit a single video generation request based on mode.

    Returns:
        video_id string

    Raises:
        HeyGenAPIError on submission failure
    """
    row = job["input_row"]

    if mode == "agent":
        prompt = row.get("prompt")
        if not prompt:
            raise HeyGenAPIError(
                400, "MISSING_PROMPT",
                f"Row {job['index']} missing required 'prompt' column",
                "/v3/video-agents"
            )

        body = {"prompt": prompt}
        if row.get("avatar_id"):
            body["avatar_id"] = row["avatar_id"]
        if row.get("voice_id"):
            body["voice_id"] = row["voice_id"]
        if row.get("name"):
            body["title"] = row["name"]

        resp = api_request("POST", "/v3/video-agents", api_key, body=body)
        data = resp.get("data", resp)
        video_id = data.get("video_id")

    elif mode == "template":
        if not template_id:
            raise HeyGenAPIError(
                400, "MISSING_TEMPLATE",
                "Template mode requires --template-id",
                "/v2/template/generate"
            )

        # All CSV columns become template variables (array format per HeyGen API)
        variables = []
        for key, value in row.items():
            variables.append({
                "name": key,
                "type": "text",
                "properties": {"content": value},
            })

        body = {
            "template_id": template_id,
            "variables": variables,
        }

        resp = api_request("POST", "/v2/template/generate", api_key, body=body)
        data = resp.get("data", resp)
        video_id = data.get("video_id")

    else:
        raise HeyGenAPIError(400, "INVALID_MODE", f"Unknown mode: {mode}", "")

    if not video_id:
        raise HeyGenAPIError(
            500, "NO_VIDEO_ID",
            f"No video_id in response for job {job['index']}",
            ""
        )

    return video_id


# ---------------------------------------------------------------------------
# Status Check (single non-blocking poll)
# ---------------------------------------------------------------------------

def check_video_status(video_id: str, api_key: str) -> dict:
    """Check the current status of a video (single non-blocking request).

    Returns:
        Dict with at least 'status' key. May include 'video_url', 'error', etc.
    """
    resp = api_request("GET", f"/v2/videos/{video_id}", api_key)
    data = resp.get("data", resp)
    return data


# ---------------------------------------------------------------------------
# Core Batch Loop
# ---------------------------------------------------------------------------

def run_batch(manifest: dict, manifest_path: str, api_key: str) -> None:
    """Execute the batch generation loop with concurrency control.

    Submits up to max_concurrent videos simultaneously, polls all active
    jobs, and as each completes submits the next from the queue. Failed
    jobs retry with exponential backoff up to max_retries.
    """
    max_concurrent = manifest["max_concurrent"]
    max_retries = manifest.get("max_retries", 3)
    output_dir = ensure_output_dir(manifest["output_dir"])
    jobs = manifest["jobs"]
    poll_interval = 15  # seconds

    active = {}  # video_id -> job index

    # Build queue: pending jobs + failed jobs that can be retried
    queue = []
    for job in jobs:
        if job["status"] == "pending":
            queue.append(job)
        elif job["status"] == "failed" and job["attempts"] < max_retries:
            queue.append(job)
        elif job["status"] == "processing" and job.get("video_id"):
            # Resumed manifest -- re-track active jobs
            active[job["video_id"]] = job["index"]

    log_json({
        "action": "batch_start",
        "total": manifest["total"],
        "queued": len(queue),
        "active": len(active),
        "max_concurrent": max_concurrent,
    })

    # Submit initial batch (fill up to max_concurrent minus already-active)
    while len(active) < max_concurrent and queue:
        job = queue.pop(0)
        try:
            video_id = submit_video(job, manifest["mode"],
                                    manifest["template_id"], api_key)
            active[video_id] = job["index"]
            job["status"] = "processing"
            job["video_id"] = video_id
            job["attempts"] += 1
            job["error"] = None
            log_json({"action": "submitted", "index": job["index"],
                       "video_id": video_id, "attempt": job["attempts"]})
        except HeyGenAPIError as e:
            job["attempts"] += 1
            job["error"] = e.message
            if job["attempts"] < max_retries:
                job["status"] = "pending"
                # Exponential backoff before re-queuing
                backoff = 2 ** job["attempts"]
                log_json({"action": "submit_failed", "index": job["index"],
                           "error": e.message, "retry_in": backoff})
                time.sleep(backoff)
                queue.append(job)
            else:
                job["status"] = "failed"
                log_json({"action": "submit_failed_permanent",
                           "index": job["index"], "error": e.message})

        update_manifest_counts(manifest)
        save_manifest(manifest, manifest_path)

    # Poll loop
    while active:
        for video_id in list(active.keys()):
            job_index = active[video_id]
            job = jobs[job_index]

            try:
                status_data = check_video_status(video_id, api_key)
                status = status_data.get("status", "unknown")

                if status == "completed":
                    video_url = status_data.get("video_url", "")
                    log_json({"action": "completed", "index": job_index,
                               "video_id": video_id})

                    # Download the video
                    if video_url:
                        filename = f"{sanitize_id(video_id, 'video_id')}.mp4"
                        output_path = str(output_dir / filename)
                        try:
                            saved_path = download_file(video_url, output_path)
                            job["path"] = saved_path
                        except Exception as dl_err:
                            log_json({"action": "download_failed",
                                       "index": job_index, "error": str(dl_err)})
                            job["path"] = None

                    job["status"] = "completed"
                    job["error"] = None
                    del active[video_id]

                    # Submit next from queue
                    if queue and len(active) < max_concurrent:
                        next_job = queue.pop(0)
                        try:
                            next_vid = submit_video(
                                next_job, manifest["mode"],
                                manifest["template_id"], api_key
                            )
                            active[next_vid] = next_job["index"]
                            next_job["status"] = "processing"
                            next_job["video_id"] = next_vid
                            next_job["attempts"] += 1
                            next_job["error"] = None
                            log_json({"action": "submitted",
                                       "index": next_job["index"],
                                       "video_id": next_vid,
                                       "attempt": next_job["attempts"]})
                        except HeyGenAPIError as e:
                            next_job["attempts"] += 1
                            next_job["error"] = e.message
                            if next_job["attempts"] < max_retries:
                                next_job["status"] = "pending"
                                queue.append(next_job)
                            else:
                                next_job["status"] = "failed"

                elif status == "failed":
                    error_msg = status_data.get(
                        "error", status_data.get("message", "Video generation failed")
                    )
                    job["error"] = str(error_msg)
                    job["status"] = "failed"
                    log_json({"action": "failed", "index": job_index,
                               "video_id": video_id, "error": job["error"]})

                    # Retry if attempts remain
                    if job["attempts"] < max_retries:
                        job["status"] = "pending"
                        queue.append(job)
                        log_json({"action": "requeued", "index": job_index,
                                   "attempts": job["attempts"],
                                   "max_retries": max_retries})

                    del active[video_id]

                    # Submit next from queue
                    if queue and len(active) < max_concurrent:
                        next_job = queue.pop(0)
                        try:
                            next_vid = submit_video(
                                next_job, manifest["mode"],
                                manifest["template_id"], api_key
                            )
                            active[next_vid] = next_job["index"]
                            next_job["status"] = "processing"
                            next_job["video_id"] = next_vid
                            next_job["attempts"] += 1
                            next_job["error"] = None
                            log_json({"action": "submitted",
                                       "index": next_job["index"],
                                       "video_id": next_vid,
                                       "attempt": next_job["attempts"]})
                        except HeyGenAPIError as e:
                            next_job["attempts"] += 1
                            next_job["error"] = e.message
                            if next_job["attempts"] < max_retries:
                                next_job["status"] = "pending"
                                queue.append(next_job)
                            else:
                                next_job["status"] = "failed"

                # else: still processing, do nothing

            except HeyGenAPIError as e:
                # Tolerate transient errors during polling (5xx)
                if e.status_code >= 500:
                    log_json({"action": "poll_error_transient",
                               "index": job_index, "video_id": video_id,
                               "error": e.message})
                else:
                    # Non-transient error -- mark failed
                    job["error"] = e.message
                    job["status"] = "failed"
                    del active[video_id]
                    log_json({"action": "poll_error_permanent",
                               "index": job_index, "error": e.message})

        update_manifest_counts(manifest)
        save_manifest(manifest, manifest_path)

        if active:
            log_json({
                "action": "poll_cycle",
                "active": len(active),
                "completed": manifest["completed"],
                "failed": manifest["failed"],
                "pending": manifest["pending"],
            })
            time.sleep(poll_interval)

    # Final save
    update_manifest_counts(manifest)
    save_manifest(manifest, manifest_path)


# ---------------------------------------------------------------------------
# Status Report
# ---------------------------------------------------------------------------

def show_status(manifest: dict) -> None:
    """Print a summary of batch progress."""
    total = manifest["total"]
    completed = manifest["completed"]
    failed = manifest["failed"]
    pending = manifest["pending"]

    # Count actively processing jobs
    active_count = sum(1 for j in manifest["jobs"] if j["status"] == "processing")

    # Estimate cost ($1 per video is a rough HeyGen estimate)
    estimated_cost = completed * 1.0

    output_json({
        "success": True,
        "summary": (
            f"Batch Progress: {completed}/{total} completed, "
            f"{failed} failed, {pending} pending"
        ),
        "active": f"{active_count} videos processing",
        "estimated_cost": f"${estimated_cost:.2f}",
        "total": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "processing": active_count,
        "mode": manifest["mode"],
        "created": manifest["created"],
        "manifest_file": manifest.get("input_file", "unknown"),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch-generate HeyGen avatar videos with concurrency control"
    )

    # Mutually exclusive top-level modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",
                       help="Input CSV or JSON file with video parameters")
    group.add_argument("--resume",
                       help="Resume from an existing manifest JSON file")
    group.add_argument("--status",
                       help="Show progress of a batch manifest")

    parser.add_argument("--mode", choices=["agent", "template"],
                        help="Generation mode (required with --input)")
    parser.add_argument("--template-id",
                        help="Template ID (required for template mode)")
    parser.add_argument("--max-concurrent", type=int, default=3,
                        help="Maximum simultaneous video generations (default: 3, range 1-10)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Maximum retry attempts per failed video (default: 3, range 0-10)")
    parser.add_argument("--max-batch", type=int, default=500,
                        help="Maximum rows to process per batch (default: 500, safety limit)")
    parser.add_argument("--output-dir",
                        help="Output directory (default: ~/Documents/lipnardo_videos/)")
    parser.add_argument("--api-key",
                        help="HeyGen API key (or set HEYGEN_API_KEY)")

    args = parser.parse_args()

    # Validate numeric bounds (prevent silent no-ops and runaway retries)
    if args.max_concurrent < 1 or args.max_concurrent > 10:
        parser.error("--max-concurrent must be between 1 and 10")
    if args.max_retries < 0 or args.max_retries > 10:
        parser.error("--max-retries must be between 0 and 10")
    if args.max_batch < 1:
        parser.error("--max-batch must be >= 1")

    # -- Status mode --
    if args.status:
        manifest = load_manifest(args.status)
        update_manifest_counts(manifest)
        show_status(manifest)
        return

    # -- Resume mode --
    if args.resume:
        api_key = resolve_api_key(args.api_key)
        manifest_path = os.path.abspath(args.resume)
        manifest = load_manifest(manifest_path)

        # Allow overriding max_concurrent on resume
        if args.max_concurrent != 3:
            manifest["max_concurrent"] = args.max_concurrent
        if args.max_retries != 3:
            manifest["max_retries"] = args.max_retries

        log_json({"action": "resume", "manifest": manifest_path,
                   "completed": manifest.get("completed", 0),
                   "total": manifest.get("total", 0)})

        try:
            run_batch(manifest, manifest_path, api_key)
        except KeyboardInterrupt:
            update_manifest_counts(manifest)
            save_manifest(manifest, manifest_path)
            log_json({"action": "interrupted", "manifest": manifest_path})
            error_exit("Batch interrupted. Resume with: "
                       f"python3 batch_generate.py --resume {manifest_path}")

        show_status(manifest)
        return

    # -- New batch mode --
    if not args.mode:
        parser.error("--mode is required when using --input")
    if args.mode == "template" and not args.template_id:
        parser.error("--template-id is required for template mode")

    api_key = resolve_api_key(args.api_key)
    rows = load_input(args.input)

    # Safety gate: enforce batch size limit
    if len(rows) > args.max_batch:
        error_exit(
            f"Input has {len(rows)} rows, exceeding --max-batch limit of {args.max_batch}. "
            f"To override, run with: --max-batch {len(rows)}"
        )

    # Cost warning: estimate worst-case cost so the user sees it before charging starts
    avg_duration_seconds = 60
    rate_per_second = 0.0667  # use highest rate (digital_twin/precision) to be conservative
    est_cost_usd = round(len(rows) * avg_duration_seconds * rate_per_second, 2)
    log_json({
        "warning": (
            f"About to start a batch of {len(rows)} videos. "
            f"Worst-case estimated cost: ${est_cost_usd} "
            f"(assuming {avg_duration_seconds}s avg at ${rate_per_second}/sec). "
            f"Run 'credit_check.py balance' to verify your remaining quota."
        )
    })

    output_dir = str(ensure_output_dir(args.output_dir))

    manifest = create_manifest(
        input_file=args.input,
        mode=args.mode,
        template_id=args.template_id,
        max_concurrent=args.max_concurrent,
        output_dir=output_dir,
        rows=rows,
    )
    manifest["max_retries"] = args.max_retries

    # Generate manifest filename with timestamp
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    manifest_filename = f"batch_manifest_{ts}.json"
    manifest_path = os.path.join(output_dir, manifest_filename)

    save_manifest(manifest, manifest_path)
    log_json({"action": "manifest_created", "path": manifest_path,
               "total_jobs": len(rows)})

    try:
        run_batch(manifest, manifest_path, api_key)
    except KeyboardInterrupt:
        update_manifest_counts(manifest)
        save_manifest(manifest, manifest_path)
        log_json({"action": "interrupted", "manifest": manifest_path})
        error_exit("Batch interrupted. Resume with: "
                   f"python3 batch_generate.py --resume {manifest_path}")

    # Final report
    show_status(manifest)


if __name__ == "__main__":
    main()
