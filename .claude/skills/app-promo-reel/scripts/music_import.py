#!/usr/bin/env python3
"""Bring your own music: prepare a track you downloaded yourself for music_rank.py.

Usage: music_import.py <local audio file> --out work/ --source "<URL or note>" [--start SECONDS]
Writes <out>/bgm_user.wav (48 kHz stereo, from --start to the end of the track) and
<out>/bgm_user.source.txt (the original file name, --source and the start time). Then it goes
through the same gate as a generated seed: music_rank.py --duration 30 work/bgm_user.wav.

This tool never downloads music; it takes a local file only. Many music sites forbid automated
downloads (Mixkit's terms ban bots and mass downloads; Pixabay allows manual downloads only). The
track's licence is yours to check; --source records where it came from.

Every failure exits 2 and leaves no bgm_user.wav: the old import is deleted first, so it can never
be ranked as the new one.
"""
import argparse
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import soundfile as sf

SR = 48000
URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="a local audio file (mp3, m4a, wav, ...)")
    ap.add_argument("--out", required=True)
    # --source and --start are checked below, not by argparse: a bad value must also clear the old import
    ap.add_argument("--source", help="required: where the track came from: its page URL, its licence")
    ap.add_argument("--start", default="0", help="seconds to skip at the start of the track")
    a = ap.parse_args(argv)
    out = Path(a.out)
    wav, note, tmp = out / "bgm_user.wav", out / "bgm_user.source.txt", out / ".partial-user.wav"
    # the old import goes before any check: a failed run must never leave it to be ranked as the new one
    try:
        for old in (wav, note, tmp):
            old.unlink(missing_ok=True)
    except OSError as e:
        fail(f"cannot clear the old import in {out} ({e})")
    if URL.match(a.file):
        fail(f"{a.file} is a URL: download the track yourself; this tool never downloads music")
    src = Path(a.file)
    if not src.is_file():
        fail(f"{a.file} is not a file")
    if not (a.source or "").strip():
        fail("--source is missing or empty: say where the track came from (its page URL, its licence)")
    try:
        start = float(a.start)
    except ValueError:
        start = math.nan
    if not 0 <= start < math.inf:  # also NaN
        fail(f"--start must be a number of seconds, 0 or more, got {a.start}")
    out.mkdir(parents=True, exist_ok=True)
    # -ss after -i: an output seek, exact to the sample on mp3 and m4a too
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(src), "-ss", f"{start:.6f}", "-vn",
                        "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", "-f", "wav", str(tmp)],
                       capture_output=True, text=True)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        fail(f"ffmpeg could not decode {src}:\n{r.stderr[-600:]}")
    try:
        frames = sf.info(tmp).frames
    except RuntimeError:  # soundfile cannot read a WAV with no samples in it
        frames = 0
    if not frames:
        tmp.unlink(missing_ok=True)
        fail(f"nothing left of {src} after --start {start:g}s")
    os.replace(tmp, wav)
    try:
        note.write_text(f"file: {src.name}\nsource: {a.source.strip()}\nstart: {start:g} s\n")
    except OSError as e:
        wav.unlink(missing_ok=True)  # a track with no source record must never be ranked
        fail(f"cannot write {note} ({e})")
    print(f"wrote {wav} ({frames / SR:.2f}s from {src.name}, start {start:g}s) and {note.name}")


if __name__ == "__main__":
    main()
