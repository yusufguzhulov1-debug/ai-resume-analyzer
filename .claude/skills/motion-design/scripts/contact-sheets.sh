#!/bin/bash
# Check a rendered video the way a human editor would: find black frames, then lay the whole film out
# on contact sheets (4 images per second, 4 x 6 grids = 6 s per sheet, timestamp on every image) that
# Claude can open and read one by one.
#
# Usage (from the repository root):
#   bash .claude/skills/motion-design/scripts/contact-sheets.sh <project>/renders/video.mp4 [OUT_DIR]
# Default OUT_DIR: <folder of the video>/contact-sheets (inside renders/, ignored by git).
# Tunables (environment): FPS=4 COLS=4 ROWS=6 WIDTH=480 BLACK_MIN=0.04 BLACK_PIX=0.02
#   BLACK_PIX=0.02 flags pure black (a frame that failed to paint over the black host page) but not a
#   near-black stage such as #0d0b0a; raise it only if your dark world is darker than #060606.
# Exit code: 0 when no black segment is found, 2 when there is at least one.
set -euo pipefail

VIDEO="${1:?usage: contact-sheets.sh VIDEO [OUT_DIR]}"
OUT="${2:-$(dirname "$VIDEO")/contact-sheets}"
FPS="${FPS:-4}"
COLS="${COLS:-4}"
ROWS="${ROWS:-6}"
WIDTH="${WIDTH:-480}"
BLACK_MIN="${BLACK_MIN:-0.04}"
BLACK_PIX="${BLACK_PIX:-0.02}"

command -v ffmpeg >/dev/null || { echo "contact-sheets: ffmpeg not found on PATH" >&2; exit 1; }
command -v ffprobe >/dev/null || { echo "contact-sheets: ffprobe not found on PATH" >&2; exit 1; }
[ -f "$VIDEO" ] || { echo "contact-sheets: $VIDEO not found" >&2; exit 1; }
mkdir -p "$OUT"
rm -f "$OUT"/sheet-*.jpg

DURATION="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$VIDEO")"
echo "video: $VIDEO (${DURATION} s)"

# 1. Black frames. blackdetect reports every interval longer than BLACK_MIN seconds.
ffmpeg -hide_banner -nostats -i "$VIDEO" -vf "blackdetect=d=${BLACK_MIN}:pix_th=${BLACK_PIX}" -an -f null - 2>&1 \
  | grep -o "black_start:[0-9.]* black_end:[0-9.]* black_duration:[0-9.]*" > "$OUT/blackdetect.txt" || true
BLACK_COUNT="$(wc -l < "$OUT/blackdetect.txt" | tr -d ' ')"
if [ "$BLACK_COUNT" -eq 0 ]; then
  echo "black frames: none"
else
  echo "black frames: $BLACK_COUNT segment(s)"
  sed 's/^/  /' "$OUT/blackdetect.txt"
fi

# 2. Contact sheets with a timestamp (HH:MM:SS.mmm) burnt on every image.
FONT=""
for candidate in /System/Library/Fonts/Supplemental/Arial.ttf /System/Library/Fonts/Helvetica.ttc \
  /Library/Fonts/Arial.ttf /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /usr/share/fonts/TTF/DejaVuSans.ttf \
  /usr/share/fonts/dejavu/DejaVuSans.ttf; do
  if [ -f "$candidate" ]; then FONT="$candidate"; break; fi
done
STAMP=""
FILTERS="$(ffmpeg -hide_banner -filters 2>/dev/null || true)"
if grep -q " drawtext " <<< "$FILTERS"; then
  STAMP=",drawtext=${FONT:+fontfile='$FONT':}text='%{pts\:hms}':x=10:y=10:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=6"
else
  echo "note: this ffmpeg has no drawtext filter, sheets are not timestamped (sheet N starts at (N-1) x $((COLS * ROWS)) / $FPS s)"
fi
ffmpeg -v error -y -i "$VIDEO" -an \
  -vf "fps=${FPS},scale=${WIDTH}:-2${STAMP},tile=${COLS}x${ROWS}:padding=6:margin=6:color=0x202020" \
  -q:v 3 "$OUT/sheet-%03d.jpg"

PER_SHEET="$(awk -v n=$((COLS * ROWS)) -v f="$FPS" 'BEGIN { printf "%g", n / f }')"
COUNT="$(ls "$OUT"/sheet-*.jpg | wc -l | tr -d ' ')"
echo "contact sheets: $COUNT in $OUT (${FPS} images/s, ${COLS}x${ROWS}, ${PER_SHEET} s per sheet)"
i=0
for sheet in "$OUT"/sheet-*.jpg; do
  awk -v a="$i" -v p="$PER_SHEET" -v s="$(basename "$sheet")" 'BEGIN { printf "  %s  %6.2f to %6.2f s\n", s, a * p, (a + 1) * p }'
  i=$((i + 1))
done

[ "$BLACK_COUNT" -eq 0 ] || exit 2
