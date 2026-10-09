#!/usr/bin/env bash
# Photo -> posterized polygons -> index.html.   ./portrait.sh photo.jpg [trace.py options]
# Example options: --levels 0.14,0.28,0.42,0.56,0.70,0.84 --height 900 --blur 1.6 --minarea 36 --crop x0,y0,x1,y1 --bgthr 0.9
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PHOTO=${1:?usage: portrait.sh photo.jpg [options]}; shift || true
[ -f "$PHOTO" ] || { echo "no such file: $PHOTO"; exit 1; }
mkdir -p shots
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
$PY "$HERE/trace.py" "$PHOTO" --out portrait.js --preview shots/portrait_preview.png "$@"
node "$HERE/inject.mjs" portrait.js "${HTML:-index.html}"
echo "look at shots/portrait_preview.png, then shoot the portrait scene: node look.mjs shot <frame> 1200 7"
