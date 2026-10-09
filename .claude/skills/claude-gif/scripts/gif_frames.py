#!/usr/bin/env python3
"""Frame extraction, assembly, and SVG rendering for GIF creation.

Usage:
    # Assemble image sequence to GIF
    python3 gif_frames.py --input-dir DIR --output FILE [options]

    # Extract frames from GIF/video
    python3 gif_frames.py --extract FILE --output-dir DIR

    # Render animated SVG to frames (via Playwright)
    python3 gif_frames.py --svg FILE --output FILE [options]

Options:
    --input-dir DIR      Directory of PNG/JPG/WEBP frames
    --output PATH        Output GIF path
    --fps N              Frame rate (default: 15)
    --width N            Output width in px (default: 480)
    --preset NAME        Quality preset: discord|slack|twitter|web|hq
    --sort METHOD        Sort: name|modified (default: name)
    --reverse            Reverse frame order
    --extract PATH       Extract frames from GIF/video
    --output-dir DIR     Directory for extracted frames
    --svg PATH           Animated SVG file to render
    --svg-duration N     SVG animation duration in seconds (default: 3)
    --transparent        Preserve transparency (for SVG mode)
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

PRESETS = {
    "discord":  {"width": 320, "fps": 10, "colors": 128, "dither": "bayer:bayer_scale=3"},
    "slack":    {"width": 400, "fps": 12, "colors": 192, "dither": "floyd_steinberg"},
    "twitter":  {"width": 480, "fps": 15, "colors": 256, "dither": "floyd_steinberg"},
    "web":      {"width": 480, "fps": 15, "colors": 256, "dither": "floyd_steinberg"},
    "hq":       {"width": 640, "fps": 20, "colors": 256, "dither": "sierra2"},
}


def natural_sort_key(s):
    """Sort strings with embedded numbers naturally."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def find_frames(input_dir: str, sort: str = "name") -> list[str]:
    """Find image frames in directory."""
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    frames = []
    for ext in extensions:
        frames.extend(glob.glob(os.path.join(input_dir, ext)))
    if sort == "modified":
        frames.sort(key=os.path.getmtime)
    else:
        frames.sort(key=natural_sort_key)
    return frames


def assemble_gif(frames: list[str], output: str, fps: int = 15, width: int = 480,
                  colors: int = 256, dither: str = "floyd_steinberg",
                  transparent: bool = False) -> dict:
    """Assemble image frames into optimized GIF using FFmpeg two-pass palette."""
    if not frames:
        return {"success": False, "error": "No frames found"}

    tmpdir = tempfile.mkdtemp(dir="/tmp/claude-gif", prefix="assemble_")
    palette = os.path.join(tmpdir, "palette.png")
    concat = os.path.join(tmpdir, "concat.txt")

    # Write concat file
    with open(concat, "w") as f:
        for frame in frames:
            f.write(f"file '{os.path.abspath(frame)}'\n")
            f.write(f"duration {1/fps}\n")

    reserve = "1" if transparent else "0"
    vf_scale = f"scale={width}:-1:flags=lanczos"

    try:
        # Pass 1: palette
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
             "-vf", f"fps={fps},{vf_scale},palettegen=max_colors={colors}:stats_mode=full:reserve_transparent={reserve}",
             palette],
            capture_output=True, timeout=120, check=True
        )

        # Pass 2: apply palette
        alpha_thresh = ":alpha_threshold=128" if transparent else ""
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
             "-i", palette,
             "-lavfi", f"fps={fps},{vf_scale} [x]; [x][1:v] paletteuse=dither={dither}:diff_mode=rectangle{alpha_thresh}",
             "-loop", "0", output],
            capture_output=True, timeout=120, check=True
        )

        size = os.path.getsize(output)
        return {
            "success": True,
            "output": output,
            "frames": len(frames),
            "fps": fps,
            "width": width,
            "colors": colors,
            "size_bytes": size,
            "size_kb": size // 1024,
            "transparent": transparent,
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "stderr": e.stderr.decode()[-500:] if e.stderr else ""}
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def extract_frames(input_path: str, output_dir: str) -> dict:
    """Extract frames from GIF or video file."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%04d.png")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, pattern],
            capture_output=True, timeout=120, check=True
        )
        frames = sorted(glob.glob(os.path.join(output_dir, "frame_*.png")))
        return {
            "success": True,
            "output_dir": output_dir,
            "frames": len(frames),
            "first": frames[0] if frames else None,
            "last": frames[-1] if frames else None,
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}


def render_svg_to_frames(svg_path: str, output_dir: str, fps: int = 15,
                          duration: float = 3.0, width: int = 480,
                          height: int = 480) -> dict:
    """Render animated SVG to PNG frames using Playwright.

    This captures each frame of a SMIL/CSS animated SVG at the target FPS,
    producing transparent PNGs that can be assembled into a transparent GIF.
    """
    os.makedirs(output_dir, exist_ok=True)
    total_frames = int(fps * duration)

    # Generate a Node.js script that uses Playwright to capture frames
    capture_script = os.path.join(output_dir, "_capture.mjs")
    with open(capture_script, "w") as f:
        f.write(f"""
import {{ chromium }} from 'playwright';
import {{ readFileSync }} from 'fs';
import {{ resolve }} from 'path';

const svgPath = resolve('{os.path.abspath(svg_path)}');
const svgContent = readFileSync(svgPath, 'utf-8');
const outputDir = resolve('{os.path.abspath(output_dir)}');
const fps = {fps};
const duration = {duration};
const totalFrames = {total_frames};
const width = {width};
const height = {height};

const browser = await chromium.launch();
const page = await browser.newPage({{
    viewport: {{ width, height }},
    deviceScaleFactor: 1,
}});

// Load SVG in a minimal HTML page with transparent background
const html = `<!DOCTYPE html>
<html><head><style>
  html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
  svg {{ width: ${{width}}px; height: ${{height}}px; display: block; }}
</style></head>
<body>${{svgContent}}</body></html>`;

await page.setContent(html, {{ waitUntil: 'networkidle' }});

// Capture frames at target FPS intervals
const frameDelay = 1000 / fps;
for (let i = 0; i < totalFrames; i++) {{
    const padded = String(i).padStart(4, '0');
    await page.screenshot({{
        path: `${{outputDir}}/frame_${{padded}}.png`,
        omitBackground: true,
    }});
    // Advance time by waiting for next animation frame
    await page.waitForTimeout(frameDelay);
}}

await browser.close();
console.log(JSON.stringify({{ success: true, frames: totalFrames }}));
""")

    try:
        result = subprocess.run(
            ["node", capture_script],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Playwright capture failed",
                "stderr": result.stderr[-500:] if result.stderr else "",
                "hint": "Run 'npx playwright install chromium' if not installed"
            }

        frames = sorted(glob.glob(os.path.join(output_dir, "frame_*.png")))
        return {
            "success": True,
            "output_dir": output_dir,
            "frames": len(frames),
            "fps": fps,
            "duration": duration,
            "transparent": True,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "SVG render timed out (120s)"}
    finally:
        if os.path.exists(capture_script):
            os.unlink(capture_script)


def main():
    parser = argparse.ArgumentParser(description="GIF frame tools")
    parser.add_argument("--input-dir", help="Directory of image frames")
    parser.add_argument("--output", help="Output GIF path")
    parser.add_argument("--fps", type=int, default=15, help="Frame rate")
    parser.add_argument("--width", type=int, default=480, help="Output width")
    parser.add_argument("--height", type=int, default=480, help="Output height (SVG mode)")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Quality preset")
    parser.add_argument("--sort", choices=["name", "modified"], default="name")
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--transparent", action="store_true")
    # Extract mode
    parser.add_argument("--extract", help="Extract frames from GIF/video")
    parser.add_argument("--output-dir", help="Output directory for extracted frames")
    # SVG mode
    parser.add_argument("--svg", help="Animated SVG file to render")
    parser.add_argument("--svg-duration", type=float, default=3.0, help="SVG animation duration")
    args = parser.parse_args()

    os.makedirs("/tmp/claude-gif", exist_ok=True)

    # Apply preset
    if args.preset:
        p = PRESETS[args.preset]
        args.width = p["width"]
        args.fps = p["fps"]
        colors = p["colors"]
        dither = p["dither"]
    else:
        colors = 256
        dither = "floyd_steinberg"

    # Mode: Extract frames
    if args.extract:
        out_dir = args.output_dir or "/tmp/claude-gif/extracted"
        result = extract_frames(args.extract, out_dir)
        print(json.dumps(result, indent=2))
        return

    # Mode: SVG render → GIF
    if args.svg:
        if not args.output:
            args.output = args.svg.replace(".svg", ".gif")
        render_dir = tempfile.mkdtemp(dir="/tmp/claude-gif", prefix="svg_")
        render_result = render_svg_to_frames(
            args.svg, render_dir, fps=args.fps,
            duration=args.svg_duration, width=args.width, height=args.height
        )
        if not render_result.get("success"):
            print(json.dumps(render_result, indent=2))
            sys.exit(1)

        frames = sorted(glob.glob(os.path.join(render_dir, "frame_*.png")))
        result = assemble_gif(frames, args.output, fps=args.fps, width=args.width,
                               colors=colors, dither=dither, transparent=True)
        print(json.dumps(result, indent=2))
        return

    # Mode: Assemble frames → GIF
    if args.input_dir:
        if not args.output:
            print(json.dumps({"error": "Missing --output"}))
            sys.exit(1)

        frames = find_frames(args.input_dir, args.sort)
        if args.reverse:
            frames.reverse()

        if not frames:
            print(json.dumps({"error": f"No image frames found in {args.input_dir}"}))
            sys.exit(1)

        result = assemble_gif(frames, args.output, fps=args.fps, width=args.width,
                               colors=colors, dither=dither, transparent=args.transparent)
        print(json.dumps(result, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
