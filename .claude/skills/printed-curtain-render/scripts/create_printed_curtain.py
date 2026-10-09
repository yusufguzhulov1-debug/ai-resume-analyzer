#!/usr/bin/env python3
"""Create a self-contained interactive printed-curtain web directory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


ARTBOARD_WIDTH = 1200
ARTBOARD_HEIGHT = 1600
DEFAULT_OUTPUT = "out/printed-curtain"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def parse_hex_colour(value: str) -> list[int]:
    raw = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", raw):
        raw = "#" + "".join(character * 2 for character in raw[1:])
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", raw):
        raise argparse.ArgumentTypeError("expected a CSS hex colour such as #002FA7")
    return [int(raw[index : index + 2], 16) for index in (1, 3, 5)]


def positive_number(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("expected a number greater than zero")
    return number


def unit_interval(value: str) -> float:
    number = float(value)
    if number < 0 or number > 1:
        raise argparse.ArgumentTypeError("expected a number from 0 to 1")
    return number


def resolve_image(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"Image file is unavailable: {path}")
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        allowed = ", ".join(sorted(IMAGE_SUFFIXES))
        raise RuntimeError(
            f"Unsupported image type {path.suffix!r}; use one of: {allowed}"
        )
    return path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "printed-curtain"


def choose_name(explicit: str, image: Path | None, texts: list[str]) -> str:
    if explicit.strip():
        return explicit.strip()
    if image:
        return image.stem.replace("-", " ").replace("_", " ").strip()
    if texts:
        return texts[0]
    return "Printed Curtain"


def copy_template(template: Path, output: Path, overwrite: bool) -> None:
    if not template.is_dir():
        raise RuntimeError(f"Bundled template is unavailable: {template}")
    if output.exists() and not output.is_dir():
        raise RuntimeError(f"Output exists and is not a directory: {output}")
    if output.exists() and any(output.iterdir()) and not overwrite:
        raise RuntimeError(
            f"Output directory is not empty: {output}. Use --overwrite to replace generated files."
        )

    output.mkdir(parents=True, exist_ok=True)
    for source in template.iterdir():
        destination = output / source.name
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(source, destination)


def build_artwork(
    args: argparse.Namespace,
    image_filename: str | None,
    texts: list[str],
    name: str,
) -> dict[str, object]:
    images: list[dict[str, object]] = []
    lines: list[dict[str, object]] = []
    vertical_bounds: list[tuple[float, float]] = []

    if image_filename:
        images.append(
            {
                "src": image_filename,
                "x": args.image_x,
                "y": args.image_y,
                "w": args.image_width,
                "h": args.image_height,
                "fit": args.image_fit,
                "opacity": args.image_opacity,
            }
        )
        vertical_bounds.append((args.image_y, args.image_y + args.image_height))

    text_y = args.text_y
    if text_y is None:
        text_y = 1040 if image_filename else 700
    family = args.font_family.strip() or '"Helvetica Neue", Arial, sans-serif'
    weight = args.font_weight.strip() or "700"

    for index, line_text in enumerate(texts):
        y = text_y + index * (args.text_height + args.text_gap)
        lines.append(
            {
                "text": line_text,
                "family": family,
                "weight": weight + " ",
                "cx": ARTBOARD_WIDTH / 2,
                "y": y,
                "h": args.text_height,
                "w": args.text_width,
            }
        )
        vertical_bounds.append((y, y + args.text_height))

    first_y = min(bound[0] for bound in vertical_bounds)
    last_y = max(bound[1] for bound in vertical_bounds)
    lockup = max(1, last_y - first_y)
    anchor = (first_y + last_y) / 2

    return {
        "id": slugify(name),
        "name": name,
        "artboard": {
            "w": ARTBOARD_WIDTH,
            "h": ARTBOARD_HEIGHT,
            "lockup": round(lockup, 4),
            "anchor": round(anchor, 4),
        },
        "images": images,
        "lines": lines,
    }


def write_artwork(
    output: Path,
    artwork: dict[str, object],
    cloth: list[int],
    ink: list[int],
    backdrop: list[int],
) -> None:
    artwork_json = json.dumps(artwork, ensure_ascii=False, indent=2)
    style_json = json.dumps(
        {"cloth": cloth, "ink": ink, "backdrop": backdrop},
        ensure_ascii=False,
        indent=2,
    )
    source = (
        "/* Generated by printed-curtain-render. Edit and reload to refine the lockup. */\n"
        f"var CURTAIN_ARTWORK = {artwork_json};\n\n"
        f"var CURTAIN_STYLE = {style_json};\n"
    )
    (output / "artwork.js").write_text(source, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an interactive artwork-woven p5.js curtain."
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT,
        help=f"Generated web directory (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument("--image", help="Optional PNG, JPEG, or WebP artwork file.")
    parser.add_argument("--name", default="", help="Artwork name and browser title.")
    parser.add_argument(
        "--text",
        action="append",
        default=[],
        help="Optional printed text line; repeat for multiple lines.",
    )
    parser.add_argument(
        "--image-fit", choices=("contain", "cover", "stretch"), default="contain"
    )
    parser.add_argument("--image-x", type=float, default=240)
    parser.add_argument("--image-y", type=float, default=220)
    parser.add_argument("--image-width", type=positive_number, default=720)
    parser.add_argument("--image-height", type=positive_number, default=720)
    parser.add_argument("--image-opacity", type=unit_interval, default=1.0)
    parser.add_argument("--text-y", type=float)
    parser.add_argument("--text-width", type=positive_number, default=920)
    parser.add_argument("--text-height", type=positive_number, default=180)
    parser.add_argument("--text-gap", type=float, default=48)
    parser.add_argument(
        "--font-family",
        default='"Helvetica Neue", Arial, sans-serif',
        help="Canvas CSS font-family list.",
    )
    parser.add_argument("--font-weight", default="700", help="Canvas font weight.")
    parser.add_argument("--cloth-color", type=parse_hex_colour, default=[0, 47, 167])
    parser.add_argument("--ink-color", type=parse_hex_colour, default=[248, 248, 246])
    parser.add_argument(
        "--background-color", type=parse_hex_colour, default=[255, 255, 255]
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite generated filenames in an existing directory; keep unrelated files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    image = resolve_image(args.image)
    texts = [value.strip() for value in args.text if value.strip()]
    if not image and not texts:
        texts = ["VIBE MOTION"]

    name = choose_name(args.name, image, texts)
    output = Path(args.output_dir).expanduser().resolve()
    skill_dir = Path(__file__).resolve().parent.parent
    template = skill_dir / "assets" / "printed-curtain-template"
    copy_template(template, output, args.overwrite)

    image_filename = None
    if image:
        image_filename = f"artwork{image.suffix.lower()}"
        destination = output / image_filename
        if image != destination:
            shutil.copy2(image, destination)

    artwork = build_artwork(args, image_filename, texts, name)
    write_artwork(
        output,
        artwork,
        cloth=args.cloth_color,
        ink=args.ink_color,
        backdrop=args.background_color,
    )

    html_path = output / "index.html"
    if not html_path.is_file() or not (output / "artwork.js").is_file():
        raise RuntimeError(f"Generated output is incomplete: {output}")
    print(
        "VALIDATION=PASS "
        f"image={'yes' if image else 'no'} text_lines={len(texts)} output={output}",
        flush=True,
    )
    print(f"OUTPUT_DIR={output}", flush=True)
    print(f"OUTPUT_HTML={html_path}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[Error] Interrupted.", file=sys.stderr)
        raise SystemExit(130)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"[Error] {error}", file=sys.stderr)
        raise SystemExit(1)
