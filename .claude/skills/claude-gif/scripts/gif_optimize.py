#!/usr/bin/env python3
"""Multi-strategy GIF optimization with platform auto-fit.

Usage:
    python3 gif_optimize.py --input FILE [options]

Options:
    --input PATH         Input GIF file (required)
    --output PATH        Output path (default: input_optimized.gif)
    --target-size SIZE   Target size: 256KB, 2MB, etc.
    --platform NAME      Platform preset: discord|slack|twitter|web|github|email
    --colors N           Max colors 2-256
    --lossy N            gifsicle lossy level 30-200 (default: 80)
    --dither ALGO        Dithering algorithm
    --analyze-only       Just report stats, don't optimize
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

PLATFORM_LIMITS = {
    "discord": 256 * 1024,       # 256 KB
    "slack": 500 * 1024,         # 500 KB
    "email": 1024 * 1024,        # 1 MB
    "web": 2 * 1024 * 1024,      # 2 MB
    "github": 10 * 1024 * 1024,  # 10 MB
    "facebook": 8 * 1024 * 1024, # 8 MB
    "twitter": 15 * 1024 * 1024, # 15 MB
    "reddit": 20 * 1024 * 1024,  # 20 MB
}


def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    size_str = size_str.strip().upper()
    multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "B": 1}
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(suffix):
            return int(float(size_str[: -len(suffix)].strip()) * mult)
    return int(size_str)


def get_gif_info(path: str) -> dict:
    """Get GIF file info using ffprobe."""
    size = os.path.getsize(path)
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,nb_frames,r_frame_rate",
             "-show_entries", "format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})
        return {
            "path": path,
            "size_bytes": size,
            "size_kb": size // 1024,
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)),
            "frames": int(stream.get("nb_frames", 0)),
            "duration": float(fmt.get("duration", 0)),
        }
    except Exception:
        return {"path": path, "size_bytes": size, "size_kb": size // 1024}


def has_gifsicle() -> bool:
    return shutil.which("gifsicle") is not None


def optimize_gifsicle(input_path: str, output_path: str, lossy: int = 80, colors: int = 256) -> bool:
    """Optimize with gifsicle lossy compression."""
    cmd = ["gifsicle", "-O3", f"--lossy={lossy}"]
    if colors < 256:
        cmd.append(f"--colors={colors}")
    cmd.extend([input_path, "-o", output_path])
    try:
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
        return os.path.exists(output_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def optimize_repalette(input_path: str, output_path: str, colors: int = 256,
                       width: int = 0, fps: int = 0, dither: str = "floyd_steinberg") -> bool:
    """Re-palette GIF through FFmpeg two-pass pipeline."""
    vf_parts = []
    if fps > 0:
        vf_parts.append(f"fps={fps}")
    if width > 0:
        vf_parts.append(f"scale={width}:-1:flags=lanczos")

    palette_path = tempfile.mktemp(suffix=".png", dir="/tmp/claude-gif")
    try:
        # Pass 1: generate palette
        vf_palette = ",".join(vf_parts + [f"palettegen=max_colors={colors}:stats_mode=diff"])
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-vf", vf_palette, palette_path],
            capture_output=True, timeout=120, check=True
        )
        # Pass 2: apply palette
        vf_use = ",".join(vf_parts) if vf_parts else ""
        if vf_use:
            lavfi = f"{vf_use} [x]; [x][1:v] paletteuse=dither={dither}:diff_mode=rectangle"
        else:
            lavfi = f"[0:v][1:v] paletteuse=dither={dither}:diff_mode=rectangle"
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-i", palette_path, "-lavfi", lavfi,
             "-loop", "0", output_path],
            capture_output=True, timeout=120, check=True
        )
        return os.path.exists(output_path)
    except subprocess.CalledProcessError:
        return False
    finally:
        if os.path.exists(palette_path):
            os.unlink(palette_path)


def auto_fit(input_path: str, output_path: str, target_bytes: int) -> dict:
    """Iteratively optimize until under target size."""
    os.makedirs("/tmp/claude-gif", exist_ok=True)
    info = get_gif_info(input_path)
    current_path = input_path
    methods_applied = []

    # Strategy 1: gifsicle lossy
    if has_gifsicle():
        for lossy in [80, 120, 180]:
            tmp = tempfile.mktemp(suffix=".gif", dir="/tmp/claude-gif")
            if optimize_gifsicle(current_path, tmp, lossy=lossy):
                if os.path.getsize(tmp) < os.path.getsize(current_path):
                    if current_path != input_path:
                        os.unlink(current_path)
                    current_path = tmp
                    methods_applied.append(f"gifsicle --lossy={lossy}")
                    if os.path.getsize(current_path) <= target_bytes:
                        break
                else:
                    os.unlink(tmp)

    if os.path.getsize(current_path) <= target_bytes:
        if current_path != output_path:
            shutil.copy2(current_path, output_path)
            if current_path != input_path:
                os.unlink(current_path)
        return _result(info, output_path, methods_applied)

    # Strategy 2: reduce colors
    orig_width = info.get("width", 480)
    for colors in [192, 128, 64]:
        tmp = tempfile.mktemp(suffix=".gif", dir="/tmp/claude-gif")
        if optimize_repalette(current_path, tmp, colors=colors):
            if os.path.getsize(tmp) < os.path.getsize(current_path):
                if current_path != input_path:
                    os.unlink(current_path)
                current_path = tmp
                methods_applied.append(f"repalette colors={colors}")
                if os.path.getsize(current_path) <= target_bytes:
                    break
            else:
                os.unlink(tmp)

    if os.path.getsize(current_path) <= target_bytes:
        if current_path != output_path:
            shutil.copy2(current_path, output_path)
            if current_path != input_path:
                os.unlink(current_path)
        return _result(info, output_path, methods_applied)

    # Strategy 3: reduce dimensions (scale down 20% each step)
    width = orig_width
    for _ in range(5):
        width = int(width * 0.8)
        if width < 160:
            break
        tmp = tempfile.mktemp(suffix=".gif", dir="/tmp/claude-gif")
        if optimize_repalette(current_path, tmp, width=width, colors=128, dither="bayer:bayer_scale=3"):
            if current_path != input_path:
                os.unlink(current_path)
            current_path = tmp
            methods_applied.append(f"scale width={width}")
            if os.path.getsize(current_path) <= target_bytes:
                break

    if os.path.getsize(current_path) <= target_bytes:
        if current_path != output_path:
            shutil.copy2(current_path, output_path)
            if current_path != input_path:
                os.unlink(current_path)
        return _result(info, output_path, methods_applied)

    # Strategy 4: reduce frame rate
    for fps in [10, 8, 5]:
        tmp = tempfile.mktemp(suffix=".gif", dir="/tmp/claude-gif")
        if optimize_repalette(current_path, tmp, fps=fps, width=width, colors=128, dither="bayer:bayer_scale=3"):
            if current_path != input_path:
                os.unlink(current_path)
            current_path = tmp
            methods_applied.append(f"fps={fps}")
            if os.path.getsize(current_path) <= target_bytes:
                break

    # Final copy
    if current_path != output_path:
        shutil.copy2(current_path, output_path)
        if current_path != input_path:
            os.unlink(current_path)

    return _result(info, output_path, methods_applied)


def _result(original_info: dict, output_path: str, methods: list) -> dict:
    """Build result JSON."""
    opt_info = get_gif_info(output_path)
    orig_size = original_info["size_bytes"]
    opt_size = opt_info["size_bytes"]
    reduction = ((orig_size - opt_size) / orig_size * 100) if orig_size > 0 else 0
    return {
        "success": True,
        "input": original_info.get("path", ""),
        "output": output_path,
        "original_size_kb": orig_size // 1024,
        "optimized_size_kb": opt_size // 1024,
        "reduction_pct": round(reduction, 1),
        "methods_applied": methods,
        "output_width": opt_info.get("width", 0),
        "output_height": opt_info.get("height", 0),
        "output_frames": opt_info.get("frames", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Optimize GIF files")
    parser.add_argument("--input", required=True, help="Input GIF file")
    parser.add_argument("--output", help="Output path")
    parser.add_argument("--target-size", help="Target size (e.g., 256KB, 2MB)")
    parser.add_argument("--platform", choices=list(PLATFORM_LIMITS.keys()), help="Platform preset")
    parser.add_argument("--colors", type=int, default=256, help="Max colors")
    parser.add_argument("--lossy", type=int, default=80, help="gifsicle lossy level")
    parser.add_argument("--dither", default="floyd_steinberg", help="Dithering algorithm")
    parser.add_argument("--analyze-only", action="store_true", help="Just report stats")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(json.dumps({"error": f"Input file not found: {args.input}"}))
        sys.exit(1)

    os.makedirs("/tmp/claude-gif", exist_ok=True)

    if args.analyze_only:
        info = get_gif_info(args.input)
        info["gifsicle_available"] = has_gifsicle()
        print(json.dumps(info, indent=2))
        return

    output = args.output or args.input.replace(".gif", "_optimized.gif")

    # Determine target
    if args.platform:
        target_bytes = PLATFORM_LIMITS[args.platform]
    elif args.target_size:
        target_bytes = parse_size(args.target_size)
    else:
        target_bytes = 2 * 1024 * 1024  # Default: 2MB (web)

    result = auto_fit(args.input, output, target_bytes)
    result["target_bytes"] = target_bytes
    result["target_platform"] = args.platform or "custom"
    result["under_target"] = os.path.getsize(output) <= target_bytes
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
