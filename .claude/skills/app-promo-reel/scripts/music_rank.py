#!/usr/bin/env python3
"""Rank music files (generated seeds or your own track) for a beat-synced reel.

Per file: per-second RMS drop-outs, beat-interval sd, tempo wobble, and the percussive-energy lift (the "drop"), if any.
Tempo wobble is the larger of two numbers, each a fraction of the median beat interval:
  drift   the largest deviation of an interval of the SMOOTHED beats (the same local fit
          beat_grid.py uses), so a slow tempo change counts but frame jitter does not;
  glitch  the largest deviation of a RAW interval, minus the tracker's own error (two
          analysis frames, 32 ms), so a stutter of one or two beats counts.
Only the first --duration seconds are judged (the part make_bed keeps); the length check uses
the whole file.
A file is REJECTED when it has a drop-out, is shorter than the target duration, or wobbles.
Ranking of accepted files: lowest wobble, then lowest interval sd.

Usage: music_rank.py --duration 30 [--json rank.json] bgm_5.wav bgm_17.wav ...
"""
import argparse
import json
import math
import sys

import numpy as np

from beat_grid import smooth
from common import die

SR = 32000
DROPOUT_RATIO = 0.15   # a second quieter than this fraction of the median second
DROPOUT_FLOOR = 1e-3   # or quieter than -60 dBFS RMS: catches a seed that is mostly silent (median 0)
WOBBLE_MAX = 0.05      # 5 % tempo deviation
TRACKER_ERROR = 2 * 512 / SR  # librosa beat times sit on 512-sample frames: +-1 frame each end
LIFT_RATIO = 1.6       # percussive RMS after / before


def per_second_rms(y, sr):
    n = len(y) // sr
    return np.array([np.sqrt(np.mean(y[i * sr:(i + 1) * sr] ** 2)) for i in range(n)])


def dropouts(y, sr):
    """Seconds (start times) whose RMS falls below DROPOUT_RATIO of the median second, or below
    DROPOUT_FLOOR (so a seed that is silent for more than half its length is still caught)."""
    rms = per_second_rms(y, sr)
    if not len(rms):
        return []
    med = float(np.median(rms))
    return [i for i, r in enumerate(rms) if r < max(DROPOUT_RATIO * med, DROPOUT_FLOOR)]


def beat_stats(beats):
    iv = np.diff(np.asarray(beats, dtype=float))
    med = float(np.median(iv))
    if med <= 0:
        return {"tempo": 0, "interval_sd_ms": 999, "wobble": 1.0}
    drift = np.max(np.abs(np.diff(smooth(beats)) - med))
    glitch = max(0.0, np.max(np.abs(iv - med)) - TRACKER_ERROR)
    return {"tempo": round(60 / med, 1), "interval_sd_ms": round(float(iv.std()) * 1000, 2),
            "wobble": round(float(max(drift, glitch)) / med, 4)}


def lift_time(perc, sr, win=0.5, span=2.0, min_t=4.0):
    """Time of the strongest step up in percussive RMS (mean of the next `span` s over the
    previous `span` s). Returns (time, ratio) or (None, ratio) when below LIFT_RATIO."""
    hop = int(win * sr)
    rms = np.array([np.sqrt(np.mean(perc[i:i + hop] ** 2)) for i in range(0, len(perc) - hop + 1, hop)])
    k = int(span / win)
    best_t, best_r = None, 0.0
    for i in range(k, len(rms) - k + 1):
        t = i * win
        if t < min_t:
            continue
        r = rms[i:i + k].mean() / (rms[i - k:i].mean() + 1e-9)
        if r > best_r:
            best_t, best_r = t, float(r)
    return (best_t if best_r >= LIFT_RATIO else None), round(best_r, 2)


def rank_file(path, duration):
    import librosa
    try:
        length = librosa.get_duration(path=str(path))
        # only the part the reel uses is decoded and judged: an outro or a later section of a long
        # track never reaches the drop-out check, the beat tracker or the lift
        y, sr = librosa.load(path, sr=SR, mono=True, duration=duration)
    except (OSError, RuntimeError, ValueError) as e:
        die(f"cannot read {path}: {e}")
    _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    stats = beat_stats(beats) if len(beats) > 8 else {"tempo": 0, "interval_sd_ms": 999, "wobble": 1.0}
    _, perc = librosa.effects.hpss(y)
    lt, lr = lift_time(perc, sr)
    reasons = []
    drops = dropouts(y, sr)
    if drops:
        reasons.append(f"drop-out at {drops} s")
    if length < duration:
        reasons.append(f"too short ({length:.1f} s < {duration:g} s)")
    if stats["wobble"] > WOBBLE_MAX:
        reasons.append(f"tempo wobble {stats['wobble'] * 100:.1f} %")
    return {"file": str(path), "length": round(length, 2), **stats,
            "lift_at": lt, "lift_ratio": lr, "rejected": bool(reasons), "reasons": reasons}


def order(results):
    ok = sorted([r for r in results if not r["rejected"]], key=lambda r: (r["wobble"], r["interval_sd_ms"]))
    return ok + [r for r in results if r["rejected"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    if not math.isfinite(a.duration) or a.duration <= 0:
        die(f"--duration must be a number of seconds above 0, got {a.duration:g}")
    results = order([rank_file(f, a.duration) for f in a.files])
    print(f"{'file':<28} {'tempo':>6} {'sd ms':>6} {'wobble':>7} {'lift':>10}  verdict")
    for r in results:
        lift = f"{r['lift_at']:.1f}s x{r['lift_ratio']}" if r["lift_at"] is not None else "none"
        verdict = "REJECT: " + "; ".join(r["reasons"]) if r["rejected"] else "ok"
        print(f"{r['file'][-28:]:<28} {r['tempo']:>6} {r['interval_sd_ms']:>6} {r['wobble']:>7} {lift:>10}  {verdict}")
    if a.json:
        try:
            with open(a.json, "w") as f:
                json.dump(results, f, indent=1)
        except OSError as e:
            die(f"cannot write {a.json}: {e}")
    if all(r["rejected"] for r in results):
        print("all seeds rejected: generate a new batch (see SKILL.md step 3)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
