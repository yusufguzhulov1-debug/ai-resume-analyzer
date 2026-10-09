#!/usr/bin/env python3
"""Real envelope of an audio excerpt as N normalized bars, to draw a waveform that matches the voice.

The excerpt is decoded to mono 16 kHz with ffmpeg, split into N equal slices, and the RMS of each
slice is normalized so the loudest bar is 1.0. --gamma < 1 lifts quiet bars (0.7 reads well on
screen), --floor keeps a minimum height so silent bars stay visible.

Usage (from the repository root):
  python3 .claude/skills/motion-design/scripts/waveform.py <project>/assets/audio/voix-montage.wav \
      --start 12.40 --duration 2.6 --bars 48 [--out <project>/assets/waveform-frame3.json] [--preview]

Prints a JSON array of N floats (0 to 1, 3 decimals) on stdout, ready to paste in a composition
(for example as the heights of N <div> bars, animated in by a stagger on the voice cue).
Requires ffmpeg on PATH. No Python dependency.
"""
import argparse
import json
import math
import subprocess
import sys
from array import array

SR = 16000


def decode(path, start, duration):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    try:
        raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    except FileNotFoundError:
        sys.exit("waveform.py: ffmpeg not found on PATH")
    except subprocess.CalledProcessError as err:
        sys.exit(f"waveform.py: ffmpeg could not read {path}: {err.stderr.decode(errors='replace').strip()}")
    samples = array("f")
    samples.frombytes(raw[: len(raw) - len(raw) % 4])
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def bars(samples, count, gamma, floor):
    if count < 1:
        sys.exit("waveform.py: --bars must be at least 1")
    if len(samples) < count:
        sys.exit("waveform.py: excerpt too short for that many bars")
    size = len(samples) / count
    levels = []
    for i in range(count):
        chunk = samples[int(i * size):int((i + 1) * size)]
        levels.append(math.sqrt(sum(x * x for x in chunk) / len(chunk)) if chunk else 0.0)
    peak = max(levels) or 1.0
    return [round(max(floor, (level / peak) ** gamma), 3) for level in levels]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--start", type=float, default=0.0, help="excerpt start in seconds (default 0)")
    ap.add_argument("--duration", type=float, default=0.0, help="excerpt length in seconds (default: to the end)")
    ap.add_argument("--bars", type=int, default=48, help="number of bars (default 48)")
    ap.add_argument("--gamma", type=float, default=0.7, help="curve applied after normalization (default 0.7)")
    ap.add_argument("--floor", type=float, default=0.06, help="minimum bar height (default 0.06)")
    ap.add_argument("--out", help="also write the JSON array to this file")
    ap.add_argument("--preview", action="store_true", help="print a one-line text preview on stderr")
    args = ap.parse_args()

    values = bars(decode(args.audio, args.start, args.duration), args.bars, args.gamma, args.floor)
    text = json.dumps(values)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    if args.preview:
        ramp = " .:-=+*#%@"
        print("".join(ramp[min(len(ramp) - 1, int(v * (len(ramp) - 1) + 0.5))] for v in values), file=sys.stderr)


if __name__ == "__main__":
    main()
