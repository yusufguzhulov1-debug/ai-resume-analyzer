#!/usr/bin/env bash
# Pre-flight safety check before any GIF write operation
# Usage: bash scripts/preflight.sh <input_file> <output_file>
# Output: JSON with pass/fail status and any warnings
set -euo pipefail

INPUT="${1:-}"
OUTPUT="${2:-}"

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
    echo '{"pass":false,"error":"Usage: preflight.sh <input_file> <output_file>"}'
    exit 1
fi

WARNINGS=()
ERRORS=()

# Check input exists
if [ ! -f "$INPUT" ]; then
    ERRORS+=("Input file not found: $INPUT")
fi

# Check output != input (resolve symlinks and relative paths)
if [ -f "$INPUT" ]; then
    REAL_INPUT=$(realpath "$INPUT" 2>/dev/null || echo "$INPUT")
    REAL_OUTPUT=$(realpath -m "$OUTPUT" 2>/dev/null || echo "$OUTPUT")
    if [ "$REAL_INPUT" = "$REAL_OUTPUT" ]; then
        ERRORS+=("Output path equals input path — would destroy source file")
    fi
fi

# Check output doesn't already exist
if [ -f "$OUTPUT" ]; then
    WARNINGS+=("Output file already exists: $OUTPUT (use -y to overwrite)")
fi

# Check output directory exists
OUTPUT_DIR=$(dirname "$OUTPUT")
if [ ! -d "$OUTPUT_DIR" ]; then
    WARNINGS+=("Output directory does not exist: $OUTPUT_DIR (will be created)")
fi

# Check disk space (estimate 2x input size as safety margin)
if [ -f "$INPUT" ]; then
    INPUT_SIZE_KB=$(du -k "$INPUT" | cut -f1)
    NEEDED_KB=$((INPUT_SIZE_KB * 2))
    AVAIL_KB=$(df -k "$OUTPUT_DIR" 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -n "$AVAIL_KB" ] && [ "$AVAIL_KB" -lt "$NEEDED_KB" ]; then
        WARNINGS+=("Low disk space: ${AVAIL_KB}KB available, estimated ${NEEDED_KB}KB needed")
    fi

    # GIF-specific: warn if input is very large
    INPUT_SIZE_MB=$((INPUT_SIZE_KB / 1024))
    if [ "$INPUT_SIZE_MB" -gt 100 ]; then
        WARNINGS+=("Large input (${INPUT_SIZE_MB}MB) — GIF output may be very large. Consider trimming or reducing resolution.")
    fi
fi

# Ensure temp directory exists
mkdir -p /tmp/claude-gif

# Build JSON output
PASS="true"
if [ ${#ERRORS[@]} -gt 0 ]; then
    PASS="false"
fi

ERROR_JSON="[]"
if [ ${#ERRORS[@]} -gt 0 ]; then
    ERROR_JSON=$(printf '%s\n' "${ERRORS[@]}" | jq -R . | jq -s .)
fi

WARN_JSON="[]"
if [ ${#WARNINGS[@]} -gt 0 ]; then
    WARN_JSON=$(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)
fi

cat <<EOF
{
  "pass": $PASS,
  "input": "$INPUT",
  "output": "$OUTPUT",
  "errors": $ERROR_JSON,
  "warnings": $WARN_JSON
}
EOF

[ "$PASS" = "true" ] && exit 0 || exit 1
