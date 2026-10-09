#!/usr/bin/env python3
"""Lipnardo -- Pre-flight Setup Validation

Purpose:
    Validates that all prerequisites are met before generating HeyGen videos.
    Checks API key configuration, API connectivity, output directory, and
    Python version.

Usage:
    python3 validate_setup.py
"""

import json
import os
import sys
from pathlib import Path

# Import heygen_client from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heygen_client import resolve_api_key, api_request, HeyGenAPIError, log_json

OUTPUT_DIR = Path.home() / "Documents" / "lipnardo_videos"
MIN_PYTHON = (3, 8)


def _mask_key(key: str) -> str:
    """Mask an API key, showing only first 4 and last 4 characters."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def check_api_key() -> tuple:
    """Check that a HeyGen API key is configured.

    Returns:
        (passed: bool, message: str, api_key: str or None)
    """
    try:
        key = resolve_api_key()
        return True, f"configured ({_mask_key(key)})", key
    except SystemExit:
        return (
            False,
            "not found\n"
            "  -> Set HEYGEN_API_KEY env var, pass --api-key, or create ~/.heygen/config.json",
            None,
        )


def check_api_connection(api_key: str) -> tuple:
    """Check API connectivity by querying the remaining quota endpoint.

    Returns:
        (passed: bool, message: str)
    """
    if api_key is None:
        return False, "skipped (no API key)"

    try:
        resp = api_request("GET", "/v2/user/remaining_quota", api_key)
        # Extract balance from response -- HeyGen nests under "data"
        data = resp.get("data", resp)
        balance = data.get("remaining_quota", data.get("balance"))
        if balance is not None:
            return True, f"connected (balance: ${balance:.2f})"
        return True, "connected (balance: unknown)"
    except HeyGenAPIError as e:
        return False, f"failed ({e.message})"
    except Exception as e:
        return False, f"failed ({e})"


def check_output_directory() -> tuple:
    """Check that the output directory exists or can be created.

    Returns:
        (passed: bool, message: str)
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        display = str(OUTPUT_DIR).replace(str(Path.home()), "~")
        return True, display
    except OSError as e:
        return False, f"cannot create {OUTPUT_DIR} ({e})"


def check_python_version() -> tuple:
    """Check that the Python version meets the minimum requirement.

    Returns:
        (passed: bool, message: str)
    """
    version = sys.version_info[:3]
    version_str = ".".join(str(v) for v in version)

    if version >= MIN_PYTHON:
        return True, version_str
    return (
        False,
        f"{version_str} (requires >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
    )


def main():
    log_json({"status": "validating_setup"})

    results = []

    # 1. API Key
    key_ok, key_msg, api_key = check_api_key()
    results.append(("API Key", key_ok, key_msg))

    # 2. API Connectivity
    conn_ok, conn_msg = check_api_connection(api_key)
    results.append(("API Connection", conn_ok, conn_msg))

    # 3. Output Directory
    dir_ok, dir_msg = check_output_directory()
    results.append(("Output Directory", dir_ok, dir_msg))

    # 4. Python Version
    py_ok, py_msg = check_python_version()
    results.append(("Python Version", py_ok, py_msg))

    # Print checklist
    print("Lipnardo Setup Validation")
    print("=" * 26)

    all_passed = True
    for name, passed, message in results:
        tag = "[PASS]" if passed else "[FAIL]"
        print(f"{tag} {name}: {message}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All checks passed! Ready to generate videos.")
    else:
        print("Some checks failed. Fix the issues above before generating videos.")

    log_json({"status": "validation_complete", "all_passed": all_passed})
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
