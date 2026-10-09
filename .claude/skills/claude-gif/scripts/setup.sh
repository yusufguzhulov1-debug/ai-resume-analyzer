#!/usr/bin/env bash
# Setup dependencies for claude-gif skill
# Usage: bash scripts/setup.sh [--check-only]
set -euo pipefail

CHECK_ONLY="${1:-}"
RESULTS=()
INSTALLED=0
FAILED=0

check_tool() {
    local name="$1" cmd="$2" install="$3"
    if command -v "$cmd" &>/dev/null; then
        local ver
        ver=$("$cmd" --version 2>&1 | head -1 || echo "unknown")
        RESULTS+=("{\"name\":\"$name\",\"available\":true,\"version\":\"$ver\"}")
    else
        RESULTS+=("{\"name\":\"$name\",\"available\":false,\"install\":\"$install\"}")
        if [ "$CHECK_ONLY" != "--check-only" ]; then
            echo "Installing $name..."
            if eval "$install" 2>/dev/null; then
                ((INSTALLED++))
            else
                ((FAILED++))
                echo "WARNING: Failed to install $name. Run manually: $install"
            fi
        fi
    fi
}

check_python_pkg() {
    local name="$1" import="$2"
    local python_cmd="python3"
    # Prefer video-skill venv if available
    [ -f "$HOME/.video-skill/bin/python3" ] && python_cmd="$HOME/.video-skill/bin/python3"

    if $python_cmd -c "import $import; print($import.__version__)" 2>/dev/null; then
        local ver
        ver=$($python_cmd -c "import $import; print($import.__version__)" 2>/dev/null)
        RESULTS+=("{\"name\":\"$name\",\"available\":true,\"version\":\"$ver\"}")
    else
        RESULTS+=("{\"name\":\"$name\",\"available\":false,\"install\":\"pip install $name\"}")
    fi
}

echo "=== claude-gif dependency check ==="

# Core tools
check_tool "ffmpeg" "ffmpeg" "sudo apt install -y ffmpeg"
check_tool "gifsicle" "gifsicle" "sudo apt install -y gifsicle"
check_tool "python3" "python3" "pyenv install 3.12"
check_tool "node" "node" "nvm install --lts"
check_tool "convert" "convert" "sudo apt install -y imagemagick"

# Python packages
check_python_pkg "Pillow" "PIL"
check_python_pkg "numpy" "numpy"

# Optional: Playwright for SVG rendering
if command -v npx &>/dev/null && npx playwright --version &>/dev/null 2>&1; then
    RESULTS+=("{\"name\":\"playwright\",\"available\":true}")
else
    RESULTS+=("{\"name\":\"playwright\",\"available\":false,\"install\":\"npx playwright install chromium\"}")
fi

# Create output directory
mkdir -p "$HOME/Documents/gif_output"
mkdir -p /tmp/claude-gif

# Build JSON output
echo ""
echo "{"
echo "  \"status\": \"complete\","
echo "  \"installed\": $INSTALLED,"
echo "  \"failed\": $FAILED,"
echo "  \"output_dir\": \"$HOME/Documents/gif_output\","
echo "  \"temp_dir\": \"/tmp/claude-gif\","
echo "  \"dependencies\": ["
for i in "${!RESULTS[@]}"; do
    if [ "$i" -lt $((${#RESULTS[@]} - 1)) ]; then
        echo "    ${RESULTS[$i]},"
    else
        echo "    ${RESULTS[$i]}"
    fi
done
echo "  ]"
echo "}"
