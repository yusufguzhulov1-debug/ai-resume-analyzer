#!/usr/bin/env bash
# framewright doctor: checks the toolchain and can install what is missing.
#   scripts/doctor.sh              report
#   scripts/doctor.sh --install    install missing pieces (asks before each step; add --yes to skip prompts)
#   scripts/doctor.sh --json       machine-readable summary for agents
# Required: node >= 20, npm, ffmpeg (libx264), ffprobe, puppeteer + Chrome in the current project.
# Optional: python3 >= 3.9 with numpy, scipy, Pillow (only for photo -> polygons).
set -u
INSTALL=0; YES=0; JSON=0
for a in "$@"; do case "$a" in --install) INSTALL=1;; --yes|-y) YES=1;; --json) JSON=1;; esac; done
OS=$(uname -s); FAIL=0; declare -a ROWS=()
say(){ [ $JSON = 1 ] || echo "$@"; }
row(){ ROWS+=("{\"check\":\"$1\",\"status\":\"$2\",\"detail\":\"$3\"}"); [ $JSON = 1 ] || printf '  %-10s %-8s %s\n' "$1" "$2" "$3"; }
confirm(){ [ $YES = 1 ] && return 0; [ $JSON = 1 ] && return 1; read -r -p "  -> $1 [y/N] " r; [[ "$r" =~ ^[Yy] ]]; }
pkg(){ # install a system package by name
  if [ "$OS" = Darwin ]; then command -v brew >/dev/null || { say "  Homebrew is missing. Install it from https://brew.sh and rerun."; return 1; }; brew install "$1"
  elif command -v apt-get >/dev/null; then sudo apt-get update -qq && sudo apt-get install -y "$1"
  elif command -v dnf >/dev/null; then sudo dnf install -y "$1"
  elif command -v pacman >/dev/null; then sudo pacman -S --noconfirm "$1"
  else say "  no known package manager, install $1 manually"; return 1; fi; }
vernum(){ echo "$1" | sed -E 's/^v//' | cut -d. -f1; }
haschrome(){ node -e "const p=require('puppeteer');const fs=require('fs');process.exit(fs.existsSync(p.executablePath())?0:1)" >/dev/null 2>&1; }

say "framewright doctor ($OS, $(pwd))"

# --- node / npm ---
if command -v node >/dev/null; then NV=$(node -v); if [ "$(vernum "$NV")" -ge 20 ]; then row node ok "$NV"; else row node old "$NV, need >= 20"; FAIL=1; fi
else row node missing "install Node 20+"; FAIL=1
  if [ $INSTALL = 1 ] && confirm "install node with the system package manager?"; then pkg node && FAIL=0; fi; fi
command -v npm >/dev/null && row npm ok "$(npm -v)" || { row npm missing "comes with node"; FAIL=1; }

# --- ffmpeg ---
if command -v ffmpeg >/dev/null; then
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264; then row ffmpeg ok "$(ffmpeg -version | head -1 | cut -d' ' -f3), libx264 present"; else row ffmpeg nox264 "libx264 encoder missing, reinstall ffmpeg with x264"; FAIL=1; fi
else row ffmpeg missing "needed to assemble the mp4"; FAIL=1
  if [ $INSTALL = 1 ] && confirm "install ffmpeg?"; then pkg ffmpeg && FAIL=0; fi; fi
command -v ffprobe >/dev/null && row ffprobe ok "" || { row ffprobe missing "comes with ffmpeg"; FAIL=1; }

# --- puppeteer + chrome (per project) ---
if [ ! -f package.json ] && [ $INSTALL = 1 ]; then say "  no package.json here, creating one"; npm init -y >/dev/null 2>&1 || true; fi
if node -e "require('puppeteer')" >/dev/null 2>&1; then
  if haschrome; then row puppeteer ok "$(node -e "console.log(require('puppeteer/package.json').version)") with Chrome"
  else row puppeteer nochrome "package present, browser missing"; FAIL=1
    if [ $INSTALL = 1 ] && confirm "download Chrome for puppeteer (~150 MB)?"; then npx --yes puppeteer browsers install chrome && FAIL=0; fi; fi
else row puppeteer missing "npm i puppeteer@23 in the project"; FAIL=1
  if [ $INSTALL = 1 ] && confirm "npm install puppeteer@23 here?"; then
    npm install puppeteer@23 --no-audit --no-fund && { haschrome || npx --yes puppeteer browsers install chrome; } && FAIL=0; fi; fi

# --- python (optional, photo tracing) ---
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
if command -v $PY >/dev/null 2>&1 || [ -x "$PY" ]; then
  if $PY -c "import numpy, scipy, PIL" >/dev/null 2>&1; then row python ok "$($PY --version 2>&1) with numpy, scipy, Pillow"
  else row python partial "$($PY --version 2>&1), numpy/scipy/Pillow missing (only needed for photos)"
    if [ $INSTALL = 1 ] && confirm "install numpy scipy pillow for python (user site, venv fallback)?"; then
      if ! $PY -m pip install --quiet --user numpy scipy pillow 2>/dev/null; then
        say "  pip refused (PEP 668), creating ./.venv"; python3 -m venv .venv && .venv/bin/pip install --quiet numpy scipy pillow && say "  use .venv/bin/python (portrait.sh picks it up automatically)"; fi; fi; fi
else row python absent "optional, only for photo tracing"; fi

# --- disk ---
FREE=$(df -Pk . | awk 'NR==2{print int($4/1024/1024)}'); if [ "${FREE:-0}" -lt 5 ]; then row disk low "${FREE} GB free, frames need ~3 GB per minute of video"; else row disk ok "${FREE} GB free"; fi

if [ $JSON = 1 ]; then printf '{"ok":%s,"checks":[%s]}\n' "$([ $FAIL = 0 ] && echo true || echo false)" "$(IFS=,; echo "${ROWS[*]}")"; fi
if [ $FAIL = 0 ]; then say "all required tools present"; exit 0; else say "missing required tools. Rerun with --install (add --yes to skip prompts)"; exit 1; fi
