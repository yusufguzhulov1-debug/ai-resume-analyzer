#!/usr/bin/env python3
"""Render styleframes (still images of the future film) to PNG with headless Chromium.

A styleframe is a standalone HTML page, 1920x1080, no timeline: ONE frozen moment of the film at final quality, with
the motion suggested in the image itself (motion blur, depth of field, an element arriving too big and blurred).
Step 5 of the motion-design skill asks for 3 directions x 3 styleframes, named A1 to C3.

Usage (from the repository root):
  python3 .claude/skills/motion-design/scripts/render-styleframes.py <project>            # every styleframe
  python3 .claude/skills/motion-design/scripts/render-styleframes.py <project> A1 B2      # only these
Reads  <project>/styleframes/<name>.html
Writes <project>/styleframes/png/<name>.png and prints each path.

Paths inside a styleframe are relative to the styleframes/ folder (fonts: "../assets/fonts/...").
Requires the Python Playwright package and its Chromium (one time):
  python3 -m pip install playwright && python3 -m playwright install chromium
"""
import argparse
import pathlib
import sys


def main():
    ap = argparse.ArgumentParser(description="Render <project>/styleframes/*.html to PNG.")
    ap.add_argument("project", nargs="?", default=".", help="project folder (default: current folder)")
    ap.add_argument("names", nargs="*", help="styleframe names without .html (default: all)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--settle-ms", type=int, default=300, help="wait after fonts are ready (default 300)")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("render-styleframes: Playwright is missing. Install it once with:\n"
                 "  python3 -m pip install playwright && python3 -m playwright install chromium")

    src = pathlib.Path(args.project).resolve() / "styleframes"
    if not src.is_dir():
        sys.exit(f"render-styleframes: {src} not found (one HTML page per styleframe goes there)")
    pages = [src / f"{n}.html" for n in args.names] if args.names else sorted(src.glob("*.html"))
    missing = [p for p in pages if not p.exists()]
    if missing:
        sys.exit("render-styleframes: not found: " + ", ".join(str(p) for p in missing))
    if not pages:
        sys.exit(f"render-styleframes: no .html in {src}")
    out = src / "png"
    out.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height}, device_scale_factor=1)
        for f in pages:
            page.goto(f.as_uri())
            page.wait_for_load_state("networkidle")
            # Wait for the web fonts, otherwise the first render uses a fallback font.
            page.evaluate("document.fonts.ready.then(() => true)")
            page.wait_for_timeout(args.settle_ms)
            target = out / (f.stem + ".png")
            page.screenshot(path=str(target), clip={"x": 0, "y": 0, "width": args.width, "height": args.height})
            print(target)
        browser.close()


if __name__ == "__main__":
    main()
