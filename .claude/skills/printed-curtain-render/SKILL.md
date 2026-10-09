---
name: printed-curtain-render
description: Generate a browser-based p5.js curtain simulation that weaves user-supplied PNG, JPEG, or WebP artwork and optional text into individually moving strands. Use when users ask for an interactive curtain or thread simulation, artwork woven into cloth or ropes, image-bearing fabric motion, 可交互线帘/幕布, 图片织入布料, printed curtain effects, or a customizable browser-based fabric reveal.
---

# Printed Curtain Render

## Workflow

1. Resolve the source image, optional text lines, palette, and output directory.
2. Resolve the installed skill directory and run `scripts/create_printed_curtain.py`.
3. Wait for `VALIDATION=PASS` and `OUTPUT_HTML=<absolute path>`.
4. Serve the output directory over HTTP and inspect the result in a browser. Do not use `file://`; browser canvas security can prevent local artwork pixels from being sampled.
5. Return the absolute HTML path, the local-server command, and the chosen artwork settings.

## Quick Start

```bash
/usr/local/bin/python3 scripts/create_printed_curtain.py \
  --image "/absolute/path/to/artwork.png" \
  --text "VIBE MOTION" \
  --output-dir "$(pwd)/out/printed-curtain"
```

## Installed Skill Resolution

Use the installed skill copy, not a source checkout of this skill collection:

```bash
skill_dir=""
for base in "${AGENTS_HOME:-$HOME/.agents}" "${CLAUDE_HOME:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; do
  if [ -d "$base/skills/printed-curtain-render" ]; then
    skill_dir="$base/skills/printed-curtain-render"
    break
  fi
done
[ -n "$skill_dir" ] || { echo "printed-curtain-render skill not found under ~/.agents, ~/.claude, or ~/.codex"; exit 1; }

/usr/local/bin/python3 "$skill_dir/scripts/create_printed_curtain.py" \
  --image "/absolute/path/to/artwork.png" \
  --text "VIBE MOTION" \
  --output-dir "$(pwd)/out/printed-curtain"
```

## Preview

Serve the generated directory, then open the printed URL:

```bash
/usr/local/bin/python3 -m http.server 8000 --directory "$(pwd)/out/printed-curtain"
```

- Move the pointer across the curtain to push individual strands aside.
- Press `H` to toggle the live controls and image picker.
- Press `R` to rebuild the cloth.
- Drop a PNG, JPEG, or WebP on the canvas for a temporary in-browser replacement.

## Customization

- Repeat `--text` to add multiple centered text lines.
- Use `--image-fit contain|cover|stretch` and the `--image-x`, `--image-y`, `--image-width`, and `--image-height` artboard controls to place artwork on the 1200×1600 material canvas.
- Use `--text-y`, `--text-width`, `--text-height`, `--text-gap`, `--font-family`, and `--font-weight` to refine type.
- Use `--cloth-color`, `--ink-color`, and `--background-color` with CSS hex colors.
- Use `--overwrite` only to update generated filenames in an existing output directory. It keeps unrelated files.
- Edit generated `artwork.js` for fine-grained image layers or per-line colors without forking the physics engine.

## Behavior

- Copy the bundled p5.js simulation and the selected image into a portable output directory; do not upload user artwork or require a network connection.
- Bake artwork into the cloth's material coordinates so it stretches, folds, and separates with the strands instead of floating above them.
- Simulate 40 Verlet strands and interpolate the visible weave for a dense curtain at modest physics cost.
- Fit the stage to a centered 3:4 frame and preserve artwork proportions on other window shapes.
- Refuse a non-empty output directory unless `--overwrite` is explicit.
- Generate a text-only `VIBE MOTION` curtain when neither `--image` nor `--text` is supplied.

## Requirements

- Python 3.9+
- A modern browser with Canvas support

## License

The bundled curtain engine is adapted from Jason Labbe's **Dynamic ropes 2** and remains licensed under CC BY-SA 4.0. Preserve its source attribution and share adaptations under the same license.
