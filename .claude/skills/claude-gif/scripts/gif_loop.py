#!/usr/bin/env python3
"""Perfect loop creation for GIFs — crossfade, ping-pong, and freeze-frame blending.

Usage:
    python3 gif_loop.py --input FILE [options]

Options:
    --input PATH         Input GIF file (required)
    --output PATH        Output path (default: input_loop.gif)
    --method METHOD      Loop method: crossfade|pingpong|freeze (default: crossfade)
    --frames N           Overlap frames for crossfade (default: 5)
    --blend-curve CURVE  Blending curve: sine|linear|ease (default: sine)
    --assess             Assess loop quality without modifying
"""
import argparse
import glob
import json
import math
import os
import subprocess
import sys
import tempfile

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def extract_frames(gif_path: str, output_dir: str) -> list[str]:
    """Extract GIF frames as PNG files using FFmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%04d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-i", gif_path, pattern],
        capture_output=True, timeout=60, check=True
    )
    frames = sorted(glob.glob(os.path.join(output_dir, "frame_*.png")))
    return frames


def get_frame_delay(gif_path: str) -> float:
    """Get average frame delay from GIF in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "json", gif_path],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        fps_str = data.get("streams", [{}])[0].get("r_frame_rate", "15/1")
        num, den = map(int, fps_str.split("/"))
        return den / num if num > 0 else 1 / 15
    except Exception:
        return 1 / 15


def blend_alpha(t: float, curve: str = "sine") -> float:
    """Compute blend alpha for crossfade."""
    if curve == "sine":
        return (1 - math.cos(t * math.pi)) / 2
    elif curve == "ease":
        return t * t * (3 - 2 * t)
    else:  # linear
        return t


def crossfade_loop(frames: list[str], output_dir: str, overlap: int = 5,
                    curve: str = "sine") -> list[str]:
    """Create seamless loop by crossfading end into beginning."""
    if not HAS_PIL:
        raise RuntimeError("Pillow required for crossfade. Install: pip install Pillow")

    n = len(frames)
    if overlap >= n // 2:
        overlap = max(2, n // 4)

    images = [Image.open(f).convert("RGBA") for f in frames]

    # Blend the last `overlap` frames with the first `overlap` frames
    for i in range(overlap):
        t = i / (overlap - 1) if overlap > 1 else 0.5
        alpha = blend_alpha(t, curve)

        start_img = images[i]
        end_idx = n - overlap + i
        end_img = images[end_idx]

        blended = Image.blend(end_img, start_img, alpha)
        images[end_idx] = blended

    # Remove the first `overlap` frames (they're now blended into the end)
    result_images = images[overlap:]

    # Save
    os.makedirs(output_dir, exist_ok=True)
    result_paths = []
    for i, img in enumerate(result_images):
        path = os.path.join(output_dir, f"loop_{i:04d}.png")
        img.convert("RGB").save(path)
        result_paths.append(path)

    return result_paths


def pingpong_loop(frames: list[str], output_dir: str) -> list[str]:
    """Create ping-pong loop (forward then reverse, skip first/last to avoid pause)."""
    os.makedirs(output_dir, exist_ok=True)
    # Forward + reverse (excluding endpoints to avoid double-frame pause)
    all_frames = list(frames) + list(reversed(frames[1:-1]))
    result_paths = []
    for i, src in enumerate(all_frames):
        dst = os.path.join(output_dir, f"pong_{i:04d}.png")
        if os.path.abspath(src) != os.path.abspath(dst):
            subprocess.run(["cp", src, dst], check=True)
        result_paths.append(dst)
    return result_paths


def freeze_blend_loop(frames: list[str], output_dir: str) -> list[str]:
    """Blend first and last frames to create a subtle meeting point."""
    if not HAS_PIL:
        raise RuntimeError("Pillow required. Install: pip install Pillow")

    os.makedirs(output_dir, exist_ok=True)
    images = [Image.open(f).convert("RGB") for f in frames]

    # Average of first and last
    avg = Image.blend(images[0], images[-1], 0.5)
    images[0] = avg
    images[-1] = avg

    result_paths = []
    for i, img in enumerate(images):
        path = os.path.join(output_dir, f"freeze_{i:04d}.png")
        img.save(path)
        result_paths.append(path)
    return result_paths


def assess_loop_quality(gif_path: str) -> dict:
    """Measure how well a GIF loops by comparing first and last frames."""
    tmpdir = tempfile.mkdtemp(dir="/tmp/claude-gif", prefix="assess_")
    try:
        frames = extract_frames(gif_path, tmpdir)
        if len(frames) < 2:
            return {"error": "Need at least 2 frames", "frames": len(frames)}

        if HAS_PIL and HAS_NUMPY:
            first = np.array(Image.open(frames[0]).convert("RGB"), dtype=float)
            last = np.array(Image.open(frames[-1]).convert("RGB"), dtype=float)
            mae = float(np.mean(np.abs(first - last)))
        else:
            mae = -1  # Can't compute without numpy/PIL

        if mae < 0:
            rating = "unknown (install Pillow + numpy)"
        elif mae < 5:
            rating = "perfect"
        elif mae < 15:
            rating = "good"
        elif mae < 30:
            rating = "fair"
        else:
            rating = "poor"

        recommendation = ""
        if mae > 15:
            recommendation = "Use --method crossfade to blend the seam"
        elif mae > 5:
            recommendation = "Loop is decent; crossfade could improve it slightly"
        elif mae >= 0:
            recommendation = "Loop is already seamless"

        return {
            "frames": len(frames),
            "mae": round(mae, 2),
            "rating": rating,
            "recommendation": recommendation,
        }
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def assemble_gif(frame_paths: list[str], output_path: str, fps: int = 15) -> bool:
    """Assemble PNG frames into optimized GIF using FFmpeg two-pass palette."""
    if not frame_paths:
        return False

    tmpdir = os.path.dirname(frame_paths[0])
    palette = os.path.join(tmpdir, "palette.png")

    # Create concat file for non-sequential names
    concat_file = os.path.join(tmpdir, "concat.txt")
    with open(concat_file, "w") as f:
        for p in frame_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
            f.write(f"duration {1/fps}\n")

    try:
        # Pass 1: palette
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
             "-vf", f"fps={fps},palettegen=max_colors=256:stats_mode=full",
             palette],
            capture_output=True, timeout=120, check=True
        )
        # Pass 2: apply
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
             "-i", palette,
             "-lavfi", f"fps={fps} [x]; [x][1:v] paletteuse=dither=floyd_steinberg:diff_mode=rectangle",
             "-loop", "0", output_path],
            capture_output=True, timeout=120, check=True
        )
        return os.path.exists(output_path)
    except subprocess.CalledProcessError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Create perfect GIF loops")
    parser.add_argument("--input", required=True, help="Input GIF file")
    parser.add_argument("--output", help="Output path")
    parser.add_argument("--method", choices=["crossfade", "pingpong", "freeze"],
                        default="crossfade", help="Loop method")
    parser.add_argument("--frames", type=int, default=5, help="Overlap frames for crossfade")
    parser.add_argument("--blend-curve", choices=["sine", "linear", "ease"],
                        default="sine", help="Blending curve")
    parser.add_argument("--assess", action="store_true", help="Assess loop quality only")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(json.dumps({"error": f"Input not found: {args.input}"}))
        sys.exit(1)

    os.makedirs("/tmp/claude-gif", exist_ok=True)

    if args.assess:
        result = assess_loop_quality(args.input)
        print(json.dumps(result, indent=2))
        return

    output = args.output or args.input.replace(".gif", "_loop.gif")

    # Extract frames
    work_dir = tempfile.mkdtemp(dir="/tmp/claude-gif", prefix="loop_")
    extract_dir = os.path.join(work_dir, "extracted")
    loop_dir = os.path.join(work_dir, "looped")

    try:
        frames = extract_frames(args.input, extract_dir)
        if len(frames) < 4:
            print(json.dumps({"error": "Need at least 4 frames for loop creation"}))
            sys.exit(1)

        # Get original FPS
        delay = get_frame_delay(args.input)
        fps = max(1, round(1 / delay))

        # Apply loop method
        if args.method == "crossfade":
            looped = crossfade_loop(frames, loop_dir, args.frames, args.blend_curve)
        elif args.method == "pingpong":
            looped = pingpong_loop(frames, loop_dir)
        elif args.method == "freeze":
            looped = freeze_blend_loop(frames, loop_dir)
        else:
            looped = frames

        # Assemble
        if assemble_gif(looped, output, fps=fps):
            # Assess result
            quality = assess_loop_quality(output)
            result = {
                "success": True,
                "output": output,
                "method": args.method,
                "original_frames": len(frames),
                "output_frames": len(looped),
                "fps": fps,
                "loop_quality": quality,
                "size_kb": os.path.getsize(output) // 1024,
            }
            if args.method == "crossfade":
                result["overlap_frames"] = args.frames
                result["blend_curve"] = args.blend_curve
        else:
            result = {"success": False, "error": "Failed to assemble GIF"}

        print(json.dumps(result, indent=2))

    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
