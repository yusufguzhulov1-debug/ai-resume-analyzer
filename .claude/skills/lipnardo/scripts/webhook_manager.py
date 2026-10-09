#!/usr/bin/env python3
"""Lipnardo -- Webhook Registration Management for HeyGen

Purpose:
    Register, list, and delete webhook endpoints for HeyGen event notifications.
    Webhooks allow async notification when avatar videos complete or fail,
    eliminating the need to poll for status.

Usage:
    # Register a webhook for video completion/failure events:
    python3 webhook_manager.py register --url https://your-server.com/webhook \
        --events avatar_video.success,avatar_video.fail [--api-key KEY]

    # List all registered webhooks:
    python3 webhook_manager.py list [--api-key KEY]

    # Delete a webhook by ID:
    python3 webhook_manager.py delete --webhook-id WEBHOOK_ID [--api-key KEY]

Dependencies: Python 3.8+ stdlib only
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import (
    resolve_api_key,
    api_request,
    output_json,
    log_json,
    error_exit,
    HeyGenAPIError,
)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_register(args):
    """Register a new webhook endpoint with HeyGen."""
    api_key = resolve_api_key(args.api_key)

    # Parse comma-separated events into a list
    events = [e.strip() for e in args.events.split(",") if e.strip()]
    if not events:
        error_exit("--events must contain at least one event type "
                   "(e.g. avatar_video.success,avatar_video.fail)")

    body = {
        "url": args.url,
        "events": events,
    }

    log_json({"action": "register_webhook", "url": args.url, "events": events})

    try:
        resp = api_request("POST", "/v1/webhook/endpoint.add", api_key, body=body)
        data = resp.get("data", resp)

        output_json({
            "success": True,
            "webhook_id": data.get("webhook_id") or data.get("endpoint_id"),
            "url": args.url,
            "events": events,
        })

    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
        })
        sys.exit(1)


def cmd_list(args):
    """List all registered webhook endpoints."""
    api_key = resolve_api_key(args.api_key)

    log_json({"action": "list_webhooks"})

    try:
        resp = api_request("GET", "/v1/webhook/endpoint.list", api_key)
        data = resp.get("data", resp)

        # Normalize response -- data may be a list directly or nested
        if isinstance(data, list):
            webhooks = data
        else:
            webhooks = data.get("endpoints", data.get("webhooks", []))

        formatted = []
        for wh in webhooks:
            formatted.append({
                "webhook_id": wh.get("webhook_id") or wh.get("endpoint_id"),
                "url": wh.get("url"),
                "events": wh.get("events", []),
            })

        output_json({
            "success": True,
            "webhooks": formatted,
        })

    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
        })
        sys.exit(1)


def cmd_delete(args):
    """Delete a webhook endpoint by ID."""
    api_key = resolve_api_key(args.api_key)

    body = {
        "webhook_id": args.webhook_id,
    }

    log_json({"action": "delete_webhook", "webhook_id": args.webhook_id})

    try:
        # Note: HeyGen uses POST (not DELETE) for this endpoint
        resp = api_request("POST", "/v1/webhook/endpoint.delete", api_key, body=body)

        output_json({
            "success": True,
            "deleted_webhook_id": args.webhook_id,
        })

    except HeyGenAPIError as e:
        output_json({
            "error": True,
            "status_code": e.status_code,
            "error_code": e.error_code,
            "message": e.message,
            "endpoint": e.endpoint,
        })
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Manage HeyGen webhook endpoints for async event notifications"
    )
    subparsers = parser.add_subparsers(dest="command", required=True,
                                        help="Webhook management command")

    # -- register --
    reg_parser = subparsers.add_parser(
        "register", help="Register a new webhook endpoint"
    )
    reg_parser.add_argument("--url", required=True,
                            help="Webhook URL to receive event notifications")
    reg_parser.add_argument("--events", required=True,
                            help="Comma-separated event types "
                                 "(e.g. avatar_video.success,avatar_video.fail)")
    reg_parser.add_argument("--api-key",
                            help="HeyGen API key (or set HEYGEN_API_KEY)")

    # -- list --
    list_parser = subparsers.add_parser(
        "list", help="List all registered webhook endpoints"
    )
    list_parser.add_argument("--api-key",
                             help="HeyGen API key (or set HEYGEN_API_KEY)")

    # -- delete --
    del_parser = subparsers.add_parser(
        "delete", help="Delete a webhook endpoint"
    )
    del_parser.add_argument("--webhook-id", required=True,
                            help="ID of the webhook to delete")
    del_parser.add_argument("--api-key",
                            help="HeyGen API key (or set HEYGEN_API_KEY)")

    args = parser.parse_args()

    if args.command == "register":
        cmd_register(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)


if __name__ == "__main__":
    main()
