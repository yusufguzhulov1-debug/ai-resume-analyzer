#!/bin/bash
# New motion design project, ready for the method (script, voice, storyboard, animation, music).
# Creates the folder tree and the HyperFrames project files (meta.json, hyperframes.json), then copies what the method
# fills for each film from this skill's templates/: frame.md, STORYBOARD.md, assemble.sh, build-audio.sh,
# build-music-options.py, plus DIRECTIONS.md from templates/DIRECTIONS-TEMPLATE.md at the repository root.
# Nothing leaves the machine unless --fonts is given (the default fonts, SIL Open Font License, from jsDelivr).
#
# Usage (from anywhere):
#   bash .claude/skills/motion-design/scripts/new-project.sh <name> [--fonts]   -> <repository root>/<name>/
#   bash .claude/skills/motion-design/scripts/new-project.sh <path/to/name>     -> that folder (tests only: the
#        project scripts reach the skills through ../.claude/skills/, so a real film lives at the repository root)
# A complete film to imitate: examples/ligne-du-temps-v8/ (frame.md, STORYBOARD.md, reference/, frames, mix script).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(dirname "$HERE")"
TPL="$SKILL/templates"
ROOT="$(cd "$SKILL/../../.." && pwd)"

ARG="${1:-}"
FONTS="${2:-}"
[ -n "$ARG" ] || { echo "usage: new-project.sh <name> [--fonts]" >&2; exit 1; }
case "$ARG" in
  */*) DST="$ARG" ;;
  *) DST="$ROOT/$ARG" ;;
esac
NAME="$(basename "$DST")"
[[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "new-project: use a kebab-case name (a-z, 0-9, -), not '$NAME'" >&2; exit 1; }
[ ! -e "$DST" ] || { echo "new-project: $DST already exists" >&2; exit 1; }
[ -f "$ROOT/templates/DIRECTIONS-TEMPLATE.md" ] || { echo "new-project: templates/ not found at $ROOT" >&2; exit 1; }

mkdir -p "$DST"/assets/{audio,fonts,icons,img,music} "$DST"/compositions/frames "$DST"/reference "$DST"/styleframes
cp "$TPL"/frame.md "$TPL"/STORYBOARD.md "$TPL"/assemble.sh "$TPL"/build-audio.sh "$TPL"/build-music-options.py "$DST"/
cp "$ROOT"/templates/DIRECTIONS-TEMPLATE.md "$DST"/DIRECTIONS.md
chmod +x "$DST"/assemble.sh "$DST"/build-audio.sh "$DST"/build-music-options.py
echo '[]' > "$DST"/assets/audio/sfx-events.json   # format: templates/sfx-events.json

cat > "$DST"/meta.json <<EOF
{
  "id": "$NAME",
  "name": "$NAME",
  "width": 1920,
  "height": 1080,
  "fps": 30
}
EOF
cat > "$DST"/hyperframes.json <<'EOF'
{
  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
  "paths": { "blocks": "compositions", "components": "compositions/components", "assets": "assets" }
}
EOF

if [ "$FONTS" = "--fonts" ]; then
  F="$DST/assets/fonts"; U=https://cdn.jsdelivr.net/fontsource/fonts
  for w in 400 500 600 700; do curl -sfL "$U/instrument-sans@latest/latin-$w-normal.woff2" -o "$F/InstrumentSans-$w.woff2"; done
  for w in 400 700; do curl -sfL "$U/space-mono@latest/latin-$w-normal.woff2" -o "$F/SpaceMono-$w.woff2"; done
  curl -sfL "$U/big-shoulders@latest/latin-800-normal.woff2" -o "$F/BigShoulders-800.woff2"
  echo "fonts: $(ls "$F" | wc -l | tr -d ' ') files in $F"
fi

echo "project created: $DST"
[ "$(cd "$DST/.." && pwd)" = "$ROOT" ] || echo "warning: not at the repository root, assemble.sh and build-audio.sh will not find ../.claude/skills/"
echo "to fill for this film: SCRIPT.md, DIRECTIONS.md, frame.md, STORYBOARD.md (grep -n '{{' must print nothing),"
echo "then the settings of build-audio.sh, assemble.sh and build-music-options.py (see references/method.md)"
[ "$FONTS" = "--fonts" ] || echo "fonts: not fetched (pass --fonts at creation, or run the commands of references/method.md step 2)"
