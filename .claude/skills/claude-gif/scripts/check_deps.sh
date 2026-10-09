#!/usr/bin/env bash
# Check dependency status for claude-gif (JSON output, no installs)
# Usage: bash scripts/check_deps.sh
set -euo pipefail

json_entry() {
    local name="$1" available="$2" version="${3:-}" install="${4:-}"
    if [ "$available" = "true" ]; then
        printf '{"name":"%s","available":true,"version":"%s"}' "$name" "$version"
    else
        printf '{"name":"%s","available":false,"install":"%s"}' "$name" "$install"
    fi
}

ENTRIES=()

# ffmpeg
if command -v ffmpeg &>/dev/null; then
    ver=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    ENTRIES+=("$(json_entry "ffmpeg" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "ffmpeg" "false" "" "sudo apt install ffmpeg")")
fi

# gifsicle
if command -v gifsicle &>/dev/null; then
    ver=$(gifsicle --version 2>&1 | head -1 | grep -oP '[\d.]+' || echo "unknown")
    ENTRIES+=("$(json_entry "gifsicle" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "gifsicle" "false" "" "sudo apt install gifsicle")")
fi

# python3
if command -v python3 &>/dev/null; then
    ver=$(python3 --version 2>&1 | awk '{print $2}')
    ENTRIES+=("$(json_entry "python3" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "python3" "false" "" "pyenv install 3.12")")
fi

# Pillow
PYTHON_CMD="python3"
[ -f "$HOME/.video-skill/bin/python3" ] && PYTHON_CMD="$HOME/.video-skill/bin/python3"
if $PYTHON_CMD -c "from PIL import Image" 2>/dev/null; then
    ver=$($PYTHON_CMD -c "import PIL; print(PIL.__version__)" 2>/dev/null || echo "unknown")
    ENTRIES+=("$(json_entry "pillow" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "pillow" "false" "" "pip install Pillow")")
fi

# numpy
if $PYTHON_CMD -c "import numpy" 2>/dev/null; then
    ver=$($PYTHON_CMD -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "unknown")
    ENTRIES+=("$(json_entry "numpy" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "numpy" "false" "" "pip install numpy")")
fi

# node
if command -v node &>/dev/null; then
    ver=$(node --version 2>&1)
    ENTRIES+=("$(json_entry "node" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "node" "false" "" "nvm install --lts")")
fi

# imagemagick
if command -v convert &>/dev/null; then
    ver=$(convert --version 2>&1 | head -1 | grep -oP 'ImageMagick [\d.-]+' || echo "unknown")
    ENTRIES+=("$(json_entry "imagemagick" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "imagemagick" "false" "" "sudo apt install imagemagick")")
fi

# playwright
if command -v npx &>/dev/null && npx playwright --version &>/dev/null 2>&1; then
    ver=$(npx playwright --version 2>&1 || echo "unknown")
    ENTRIES+=("$(json_entry "playwright" "true" "$ver")")
else
    ENTRIES+=("$(json_entry "playwright" "false" "" "npx playwright install chromium")")
fi

# Output JSON
echo "["
for i in "${!ENTRIES[@]}"; do
    if [ "$i" -lt $((${#ENTRIES[@]} - 1)) ]; then
        echo "  ${ENTRIES[$i]},"
    else
        echo "  ${ENTRIES[$i]}"
    fi
done
echo "]"
