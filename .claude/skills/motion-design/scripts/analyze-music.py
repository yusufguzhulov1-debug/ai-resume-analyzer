#!/usr/bin/env python3
"""Read a music track the way an editor would before syncing it to a film.

For each track: tempo (autocorrelation of a spectral-flux onset envelope, 60 to 200 BPM, with the octave
alternative), energy jumps (a rise of 6 dB or more within 1 s on the full band, 8 dB under 150 Hz where bass and
kick entries show), rises (the level climbs 6 dB or more over 3 s or more), bright or dark (median spectral
centroid), the main drop, and, with --drop-at T, where to start the track so its drop lands at film time T.

Usage (from the repository root):
  python3 .claude/skills/motion-design/scripts/analyze-music.py music/*.mp3 --drop-at 14.3
  python3 .claude/skills/motion-design/scripts/analyze-music.py track.mp3 --seconds 90 --envelope --json out.json

Jumps and drops are accurate to about 0.1 s (a drop lands on a video frame of 0.03 s: check it by ear and adjust by
one or two frames), rises to 0.5 s. Lo-fi masters are bass heavy: compare the centroid of tracks against each other.
The tempo can be read at half or double speed: both are printed.
Requires ffmpeg on PATH and numpy (installed with openai-whisper).
"""
import argparse
import json
import os
import subprocess
import sys

try:
    import numpy as np
except ImportError:
    sys.exit("analyze-music.py: numpy is required (python3 -m pip install numpy, or install openai-whisper)")

SR = 22050
HOP = 220  # 10 ms


def decode(path, seconds):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR)]
    if seconds:
        cmd += ["-t", str(seconds)]
    cmd += ["-f", "f32le", "-"]
    try:
        raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    except FileNotFoundError:
        sys.exit("analyze-music.py: ffmpeg not found on PATH")
    except subprocess.CalledProcessError as err:
        sys.exit(f"analyze-music.py: ffmpeg could not read {path}: {err.stderr.decode(errors='replace').strip()}")
    return np.frombuffer(raw[: len(raw) - len(raw) % 4], dtype="<f4").astype(np.float64)


def stft_mag(x, n_fft, hop):
    if len(x) < n_fft:
        x = np.pad(x, (0, n_fft - len(x)))
    frames = 1 + (len(x) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(frames)[:, None]
    return np.abs(np.fft.rfft(x[idx] * np.hanning(n_fft)[None, :], axis=1))


def tempo(x):
    mag = stft_mag(x, 1024, 256)
    flux = np.maximum(0.0, np.diff(np.log1p(100 * mag), axis=0)).sum(axis=1)
    flux = flux - np.convolve(flux, np.ones(32) / 32, mode="same")
    flux = np.maximum(flux, 0.0)
    if not flux.any():
        return None
    fps = SR / 256
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    ac = ac / (ac[0] + 1e-12)
    lags = np.arange(len(ac))
    bpm = np.where(lags > 0, 60 * fps / np.maximum(lags, 1), 0)
    ok = (bpm >= 60) & (bpm <= 200)
    if not ok.any():
        return None
    weight = np.exp(-0.5 * (np.log2(np.maximum(bpm, 1) / 120) / 1.0) ** 2)
    score = np.where(ok, ac * weight, -1)
    best = int(np.argmax(score))

    def refine(lag):
        if 1 <= lag < len(ac) - 1:
            a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
            den = a - 2 * b + c
            return lag + (0.5 * (a - c) / den if den else 0.0)
        return float(lag)

    main = 60 * fps / refine(best)
    alt, alt_strength = None, 0.0
    for factor in (2, 0.5):  # the octave alternative (half or double tempo), whichever is stronger
        lag = int(round(best * factor))
        if 1 <= lag < len(ac) and 60 <= 60 * fps / lag <= 200 and ac[lag] > alt_strength:
            alt, alt_strength = 60 * fps / refine(lag), float(ac[lag])
    return {"bpm": round(main, 1), "alt_bpm": round(alt, 1) if alt else None, "clarity": round(float(ac[best]), 2)}


def jumps(power, threshold, offset, window=100, hold=15, merge=150):
    """Energy jumps: the level of the next 150 ms is `threshold` dB or more above the mean energy of the second
    before. `power` is linear power per 10 ms frame; `offset` is the time of frame 0 (s). Returns (onset, +dB)."""
    floor = power.max() * 1e-6  # 60 dB under the loudest frame: digital silence does not make fake jumps
    p = np.maximum(power, floor)
    fine = 10 * np.log10(np.convolve(p, np.ones(3) / 3, mode="same"))
    csum = np.concatenate([[0.0], np.cumsum(p)])
    events = []
    i = window
    while i < len(p) - hold:
        before = 10 * np.log10((csum[i] - csum[i - window]) / window)
        after = 10 * np.log10((csum[i + hold] - csum[i]) / hold)
        if after - before >= threshold:
            peak = fine[i:i + hold].max()
            onset = i
            for f in range(max(0, i - hold), i + hold):
                if fine[f] >= peak - 3:
                    onset = f
                    break
            events.append((offset + onset * HOP / SR, float(after - before)))
            i += hold
        else:
            i += 1
    merged = []
    for t, rise in events:
        if merged and t - merged[-1][0] < merge * HOP / SR:
            if rise > merged[-1][1]:
                merged[-1] = (t, rise)  # keep the strongest event of the cluster, with its own time
        else:
            merged.append((t, rise))
    return [(round(t, 2), round(r, 1)) for t, r in merged]


def rises(level_block, block=0.5, need=6.0, min_len=3.0, skip=1.0, tolerance=2.0):
    """Builds: runs where the level (per 0.5 s block, smoothed over 1.5 s) keeps climbing, 6 dB or more over 3 s or
    more. A dip of up to `tolerance` dB between two blocks does not break the run."""
    level_block = np.convolve(np.pad(level_block, 1, mode="edge"), np.ones(3) / 3, mode="valid")
    out = []
    i = int(skip / block)
    while i < len(level_block) - 1:
        j = i
        while j + 1 < len(level_block) and level_block[j + 1] >= level_block[j] - tolerance:
            j += 1
        top = level_block[i:j + 1].max()
        peak = next(k for k in range(i, j + 1) if level_block[k] >= top - 1.0)  # where the climb reaches the plateau
        low = level_block[i:peak + 1].min() if peak > i else level_block[i]
        start = max(k for k in range(i, peak + 1) if level_block[k] <= low + 0.5)
        if (peak - start) * block >= min_len and level_block[peak] - level_block[start] >= need:
            out.append((round(start * block, 1), round(peak * block, 1), round(float(level_block[peak] - level_block[start]), 1)))
            i = peak + 1
        else:
            i = max(i + 1, j + 1) if j > i else i + 1
    return out


def analyze(path, seconds, drop_at):
    x = decode(path, seconds)
    duration = len(x) / SR
    frames = max(1, (len(x) - HOP) // HOP)
    power = np.array([np.mean(x[k * HOP:(k + 1) * HOP] ** 2) for k in range(frames)])
    mag = stft_mag(x, 2048, HOP)
    freqs = np.fft.rfftfreq(2048, 1 / SR)
    low_power = (mag[:, freqs < 150] ** 2).sum(axis=1) / (2048 ** 2)

    loud = 10 * np.log10(power + 1e-12)
    active = loud[: len(mag)] > loud.max() - 40
    centroid = (mag * freqs[None, :]).sum(axis=1) / (mag.sum(axis=1) + 1e-12)
    cen = float(np.median(centroid[active])) if active.any() else 0.0
    tone = "dark" if cen < 900 else "medium" if cen <= 1600 else "bright"

    jumps_full = jumps(power, 6.0, 0.5 * HOP / SR)
    jumps_low = jumps(low_power, 8.0, 1024 / SR)  # STFT frames are centered 1024 samples after their start
    block = int(0.5 * SR / HOP)
    level_block = np.array([10 * np.log10(np.mean(power[k:k + block]) + 1e-12) for k in range(0, len(power), block)])
    per_second = [10 * np.log10(np.mean(power[k:k + 100]) + 1e-12) for k in range(0, len(power), 100)]
    top = max(per_second) if per_second else 0.0

    candidates = [(t, r) for t, r in jumps_low if r >= 12 and t <= 60] or [(t, r) for t, r in jumps_full if r >= 10 and t <= 60]
    drop = max(candidates, key=lambda e: e[1])[0] if candidates else None
    result = {
        "file": os.path.basename(path), "duration": round(duration, 1), "tempo": tempo(x),
        "centroid_hz": round(cen), "tone": tone, "main_drop": drop,
        "jumps_full": jumps_full, "jumps_under_150hz": jumps_low, "rises": rises(level_block),
        "energy_per_second_db": [round(v - top) for v in per_second],
    }
    if drop_at is not None and drop is not None:
        if drop <= drop_at:
            result["sync"] = {"drop_at": drop_at, "start_music_at_film": round(drop_at - drop, 2), "trim_file": 0.0}
        else:
            result["sync"] = {"drop_at": drop_at, "start_music_at_film": 0.0, "trim_file": round(drop - drop_at, 2)}
    return result


def show(r, envelope):
    t = r["tempo"]
    bpm = f"{t['bpm']} BPM" + (f" (or {t['alt_bpm']})" if t and t["alt_bpm"] else "") + f", beat clarity {t['clarity']}" if t else "no clear beat"
    print(f"{r['file']}  {r['duration']} s  {bpm}  {r['tone']} ({r['centroid_hz']} Hz)")
    print(f"  main drop: {r['main_drop'] if r['main_drop'] is not None else 'none'}")
    if "sync" in r:
        s = r["sync"]
        if s["trim_file"] > 0:
            print(f"  drop at film {s['drop_at']} s: start the file at {s['trim_file']} s (trim), from film 0")
        else:
            print(f"  drop at film {s['drop_at']} s: start the music at film {s['start_music_at_film']} s (no trim)")
    print("  jumps full band (s, +dB): " + (", ".join(f"{a} (+{b})" for a, b in r["jumps_full"]) or "none"))
    print("  jumps under 150 Hz (s, +dB): " + (", ".join(f"{a} (+{b})" for a, b in r["jumps_under_150hz"]) or "none"))
    print("  rises (start to peak s, +dB): " + (", ".join(f"{a} to {b} (+{c})" for a, b, c in r["rises"]) or "none"))
    if envelope:
        values = r["energy_per_second_db"]
        for k in range(0, len(values), 20):
            print(f"  {k:4d} s " + "".join(f"{v:5d}" for v in values[k:k + 20]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tracks", nargs="+")
    ap.add_argument("--drop-at", type=float, help="film time (s) where the drop must land, e.g. the light flash")
    ap.add_argument("--seconds", type=float, default=120, help="analyze only the first N seconds (default 120, 0 = all)")
    ap.add_argument("--envelope", action="store_true", help="print the energy per second (dB relative to the loudest second)")
    ap.add_argument("--json", help="write all results to this JSON file")
    args = ap.parse_args()
    results = []
    for path in args.tracks:
        if not os.path.exists(path):
            sys.exit(f"analyze-music.py: {path} not found")
        r = analyze(path, args.seconds, args.drop_at)
        show(r, args.envelope)
        results.append(r)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=1)
            fh.write("\n")


if __name__ == "__main__":
    main()
