#!/usr/bin/env bash
# Core GIF conversion — FFmpeg two-pass palette pipeline
# Usage: bash gif_convert.sh --input FILE [options]
#
# Options:
#   --input PATH       Input video/image file (required)
#   --output PATH      Output GIF path (default: input_basename.gif)
#   --fps N            Frame rate (default: 15)
#   --width N          Output width in px, height auto (default: 480)
#   --preset NAME      Quality preset: discord|slack|twitter|web|hq (overrides fps/width/colors/dither)
#   --start SS         Start time in seconds (default: 0)
#   --duration SS      Duration in seconds (default: full)
#   --dither ALGO      Dithering: floyd_steinberg|bayer:3|sierra2|sierra2_4a|none (default: floyd_steinberg)
#   --stats-mode MODE  Palette mode: full|diff|single (default: full)
#   --colors N         Max colors 2-256 (default: 256)
#   --loop N           Loop count: 0=infinite, N=fixed (default: 0)
#   --transparent      Enable transparency (single color key)
#   -y                 Overwrite output if exists
set -euo pipefail

# Defaults
INPUT=""
OUTPUT=""
FPS=15
WIDTH=480
PRESET=""
START=""
DURATION=""
DITHER="floyd_steinberg"
STATS_MODE="full"
COLORS=256
LOOP=0
OVERWRITE=""
TRANSPARENT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --input)      INPUT="$2"; shift 2 ;;
        --output)     OUTPUT="$2"; shift 2 ;;
        --fps)        FPS="$2"; shift 2 ;;
        --width)      WIDTH="$2"; shift 2 ;;
        --preset)     PRESET="$2"; shift 2 ;;
        --start)      START="$2"; shift 2 ;;
        --duration)   DURATION="$2"; shift 2 ;;
        --dither)     DITHER="$2"; shift 2 ;;
        --stats-mode) STATS_MODE="$2"; shift 2 ;;
        --colors)     COLORS="$2"; shift 2 ;;
        --loop)       LOOP="$2"; shift 2 ;;
        --transparent) TRANSPARENT="1"; shift ;;
        -y)           OVERWRITE="-y"; shift ;;
        *)            echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [ -z "$INPUT" ]; then
    echo '{"error": "Missing --input argument"}' >&2
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "{\"error\": \"Input file not found: $INPUT\"}" >&2
    exit 1
fi

# Apply preset overrides
case "$PRESET" in
    discord)
        WIDTH=320; FPS=10; COLORS=128; DITHER="bayer:bayer_scale=3"; STATS_MODE="diff"
        ;;
    slack)
        WIDTH=400; FPS=12; COLORS=192; DITHER="floyd_steinberg"; STATS_MODE="full"
        ;;
    twitter)
        WIDTH=480; FPS=15; COLORS=256; DITHER="floyd_steinberg"; STATS_MODE="full"
        ;;
    web)
        WIDTH=480; FPS=15; COLORS=256; DITHER="floyd_steinberg"; STATS_MODE="full"
        ;;
    hq)
        WIDTH=640; FPS=20; COLORS=256; DITHER="sierra2"; STATS_MODE="diff"
        ;;
    "")
        ;; # No preset, use explicit values
    *)
        echo "{\"error\": \"Unknown preset: $PRESET. Use: discord|slack|twitter|web|hq\"}" >&2
        exit 1
        ;;
esac

# Default output path
if [ -z "$OUTPUT" ]; then
    BASENAME=$(basename "$INPUT")
    OUTPUT_DIR=$(dirname "$INPUT")
    OUTPUT="${OUTPUT_DIR}/${BASENAME%.*}.gif"
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT")"

# Temp palette file
PALETTE="/tmp/claude-gif/palette_$$.png"
mkdir -p /tmp/claude-gif
trap 'rm -f "$PALETTE"' EXIT INT TERM

# Build time selection flags
TIME_FLAGS=""
[ -n "$START" ] && TIME_FLAGS="-ss $START"
[ -n "$DURATION" ] && TIME_FLAGS="$TIME_FLAGS -t $DURATION"

# Build overwrite flag
OW_FLAG="${OVERWRITE:--n}"

# Build scale filter
SCALE_FILTER="scale=${WIDTH}:-1:flags=lanczos"

# Pass 1: Generate optimal palette
echo "Pass 1: Generating palette (${COLORS} colors, stats_mode=${STATS_MODE})..." >&2
ffmpeg -y $TIME_FLAGS -i "$INPUT" \
    -vf "fps=${FPS},${SCALE_FILTER},palettegen=max_colors=${COLORS}:stats_mode=${STATS_MODE}:reserve_transparent=${TRANSPARENT:-0}" \
    "$PALETTE" 2>/dev/null

# Pass 2: Apply palette with dithering
echo "Pass 2: Rendering GIF (dither=${DITHER}, loop=${LOOP})..." >&2
ffmpeg $OW_FLAG $TIME_FLAGS -i "$INPUT" -i "$PALETTE" \
    -lavfi "fps=${FPS},${SCALE_FILTER} [x]; [x][1:v] paletteuse=dither=${DITHER}:diff_mode=rectangle" \
    -loop "$LOOP" \
    "$OUTPUT" 2>/dev/null

# Get output stats
if [ -f "$OUTPUT" ]; then
    SIZE_BYTES=$(stat -c%s "$OUTPUT" 2>/dev/null || stat -f%z "$OUTPUT" 2>/dev/null)
    SIZE_KB=$((SIZE_BYTES / 1024))
    SIZE_MB=$(echo "scale=2; $SIZE_BYTES / 1048576" | bc 2>/dev/null || echo "N/A")

    # Get frame count and dimensions
    FRAME_INFO=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames,r_frame_rate -of json "$OUTPUT" 2>/dev/null || echo '{}')
    OUT_WIDTH=$(echo "$FRAME_INFO" | grep -oP '"width":\s*\K\d+' || echo "$WIDTH")
    OUT_HEIGHT=$(echo "$FRAME_INFO" | grep -oP '"height":\s*\K\d+' || echo "auto")

    cat <<EOF
{
  "success": true,
  "output": "$OUTPUT",
  "size_bytes": $SIZE_BYTES,
  "size_kb": $SIZE_KB,
  "size_mb": "$SIZE_MB",
  "width": $OUT_WIDTH,
  "height": $OUT_HEIGHT,
  "fps": $FPS,
  "colors": $COLORS,
  "dither": "$DITHER",
  "stats_mode": "$STATS_MODE",
  "preset": "${PRESET:-custom}",
  "loop": $LOOP
}
EOF
else
    echo '{"success": false, "error": "Output file was not created"}' >&2
    exit 1
fi
