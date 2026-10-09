#!/usr/bin/env python3
"""Scaffold a reel project from template/.

Creates <out>/<app>-<variant>/ with src.html.tmpl, DESIGN.md, project.json, cues.json, motion.js (9:16 and 4:5),
hyperframes.json and package.json (HyperFrames pinned). If $SFX_DIR is set, the audio files
in it are COPIED (not linked) into assets/audio/ so the renderer sees real files.

The default <out> is ~/app-promo-reels. An <out> inside a git work tree is refused unless
--force; an <out> inside the app-promo-reel repo itself is always refused.

Usage: new_project.py --app my-app --variant a [--out DIR] [--lang en] [--format 9:16|4:5|16:9]
                      [--stores app_store,google_play] [--duration 30] [--force]
--format: 9:16 (1080x1920, Reels / TikTok / Shorts / Stories, the default) or 4:5 (1080x1350,
a feed post) or 16:9 (1920x1080, a silent web hero that loops, 8 s by default: it gets the hero
template, no cues.json, no assets/audio and no SFX). It sets format, width and height in
project.json and the DESIGN.md header.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FORMATS, HERO_DURATION, KNOWN_STORES, PROJECT_DEFAULTS,  # noqa: E402
                    SILENT_MIN_DURATION, die, is_silent)

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "template"
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}


def _git(path, *args):
    p = Path(path).resolve()
    while not p.exists():
        p = p.parent
    # a caller's GIT_DIR / GIT_WORK_TREE (e.g. inside a git hook) would answer for the wrong repo
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    r = subprocess.run(["git", "-C", str(p), *args], capture_output=True, text=True, env=env)
    return r.stdout.strip() if r.returncode == 0 else None


def git_toplevel(path):
    top = _git(path, "rev-parse", "--show-toplevel")
    return Path(top).resolve() if top else None


def repo_root(path):
    """The main checkout of the repo that holds `path`, also when `path` is in a linked worktree."""
    common = _git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).resolve().parent if common else None


def is_inside(child, parent):
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def check_out_dir(out, force):
    repo = repo_root(SKILL_DIR)
    if repo and (is_inside(out, repo) or repo_root(out) == repo):
        die(f"{out} is inside the app-promo-reel repo ({repo}); pick a folder outside it")
    top = git_toplevel(out)
    if top and not force:
        die(f"{out} is inside the git work tree {top}; generated media must not land in a repo "
            f"(use --force if you are sure)")


def scaffold(app, variant, out, lang="en", stores=None, duration=None, force=False, sfx_dir=None,
             fmt="9:16"):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", app) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", variant):
        die("--app and --variant must be lowercase slugs (a-z, 0-9, -)")
    stores = stores or list(PROJECT_DEFAULTS["stores"])
    if not stores or any(s not in KNOWN_STORES for s in stores):
        die(f"--stores must be a non-empty subset of {list(KNOWN_STORES)}")
    if fmt not in FORMATS:
        die(f"--format must be one of {', '.join(FORMATS)}")
    silent = is_silent(fmt)
    if duration is not None and duration <= 1:
        die("--duration must be above 1 second")
    if silent and duration is not None and duration < SILENT_MIN_DURATION:
        die(f"--duration for a {fmt} loop must be at least {SILENT_MIN_DURATION:g} s "
            f"(it starts from rest, moves and comes back to rest)")
    out = Path(out).expanduser()
    check_out_dir(out, force)
    dest = out / f"{app}-{variant}"
    if dest.exists():
        die(f"{dest} already exists; pick another --variant")
    dest.mkdir(parents=True)
    shutil.copy2(TEMPLATE / ("hero.html.tmpl" if silent else "src.html.tmpl"), dest / "src.html.tmpl")
    for name in ("hyperframes.json",) if silent else ("hyperframes.json", "cues.json", "motion.js"):
        shutil.copy2(TEMPLATE / name, dest / name)
    shutil.copy2(TEMPLATE / ("SHOTLIST.hero.md.tmpl" if silent else "SHOTLIST.md.tmpl"), dest / "shotlist.md")
    design = (TEMPLATE / "DESIGN.md.tmpl").read_text().replace("<format>", fmt, 1)
    if silent:
        design = re.sub(r"(?ms)^## Music\n.*?(?=^## |\Z)", "## Music\n\n16:9 is silent: no music.\n\n", design)
    (dest / "DESIGN.md").write_text(design)
    pkg = json.loads((TEMPLATE / "package.json").read_text())
    pkg["name"] = f"{app}-{variant}-reel"
    (dest / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    project = json.loads((TEMPLATE / "project.json").read_text())
    width, height = FORMATS[fmt]
    project.update({"app": app, "variant": variant, "lang": lang, "format": fmt, "width": width,
                    "height": height, "stores": stores})
    if silent:
        project["duration"] = HERO_DURATION
    if duration is not None:
        project["duration"] = duration
    (dest / "project.json").write_text(json.dumps(project, indent=2) + "\n")
    for sub in ("assets/img", "assets/fonts", "renders", "work") if silent else \
            ("assets/audio", "assets/img", "assets/fonts", "renders", "work"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    copied = 0
    if sfx_dir and not silent:
        for f in sorted(Path(sfx_dir).expanduser().iterdir()):
            if f.is_file() and f.suffix.lower() in AUDIO_EXT:
                shutil.copy2(f, dest / "assets" / "audio" / f.name)
                copied += 1
    return dest, copied


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", default="~/app-promo-reels")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--format", default="9:16", choices=tuple(FORMATS))
    ap.add_argument("--stores", default="app_store,google_play")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sfx = os.environ.get("SFX_DIR")
    if sfx and not is_silent(a.format) and not Path(sfx).expanduser().is_dir():
        die(f"SFX_DIR={sfx} is not a folder")
    dest, copied = scaffold(a.app, a.variant, a.out, a.lang, a.stores.split(","), a.duration, a.force, sfx,
                            a.format)
    print(f"created {dest}")
    if is_silent(a.format):
        print(f"{a.format} is silent: no SFX copied")
        return
    print(f"copied {copied} SFX files from $SFX_DIR" if sfx else
          "no $SFX_DIR: the reel builds without SFX (cues are skipped with a warning)")


if __name__ == "__main__":
    main()
