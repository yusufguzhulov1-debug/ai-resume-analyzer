#!/usr/bin/env python3
"""Beat grid for a music bed: librosa beat_track, then a kick-band phase check, a per-beat
refine to the kick (or hi-hat), local linear smoothing and the downbeat phase.

Writes beats.json: {"beats": [...], "downbeat_phase": p, "downbeats": [...]}.
All band filters are zero-phase (sosfiltfilt) so they do not shift the kick times.

--bpm N   the tempo the grid must be built on: the tempo asked of ACE-Step, or the tempo column
          of music_rank.py. The tracker is primed with it, and the grid must come out within
          4 % of it, else the run stops and writes nothing (take the next seed). It stops a
          tracker that locks onto another pulse (a 3+3+2 kick pattern read as 2/3 of the tempo);
          it cannot find a WRONG --bpm that is a simple ratio of the real tempo: the tracker
          follows that too.
A failed run never touches an existing beats.json (build.py needs it to keep the page).

Usage: beat_grid.py <audio.wav> <project_dir> [--bpm N]      (writes <project_dir>/beats.json)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import die, load_project  # noqa: E402

SR = 32000
HOP = 256
REFINE_WINDOW = 0.040  # a refined beat never moves more than this from its input time
BPM_TOLERANCE = 0.04   # --bpm: the heard grid must be within 4 % of it


def band_envelope(y, sr, lo, hi=None, hop=HOP):
    """Onset-strength envelope of one band (zero-phase filter). Returns (env, times)."""
    import librosa
    if hi:
        sos = ss.butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    else:
        sos = ss.butter(4, lo, btype="high", fs=sr, output="sos")
    yy = ss.sosfiltfilt(sos, y).astype("float32")
    env = librosa.onset.onset_strength(y=yy, sr=sr, hop_length=hop)
    return env, librosa.frames_to_time(np.arange(len(env)), sr=sr, hop_length=hop)


def peak_near(env, t_env, t, w=0.035):
    m = (t_env > t - w) & (t_env < t + w)
    return float(env[m].max()) if m.any() else 0.0


def phase_check(beats, kick, t_env):
    """Shift the grid by half a beat when the kick is stronger off the tracked beats.
    Returns (beats, shifted, on_strength)."""
    beats = np.asarray(beats, dtype=float)
    iv = float(np.median(np.diff(beats)))
    on = float(np.mean([peak_near(kick, t_env, b) for b in beats]))
    off_t = [b + iv / 2 for b in beats if b + iv / 2 < t_env[-1]]
    off = float(np.mean([peak_near(kick, t_env, b) for b in off_t])) if off_t else 0.0
    if off > on * 1.2:
        return beats + iv / 2, True, off
    return beats, False, on


def refine(beats, kick, hi, t_env, on_strength, window=REFINE_WINDOW):
    """Move each beat to the local kick peak, or the hi-hat peak when the kick is weak.
    A beat never moves more than `window`; when no peak is found it stays put."""
    out = []
    for b in beats:
        m = (t_env > b - window) & (t_env < b + window)
        if not m.any():
            out.append(b)
            continue
        env = kick if kick[m].max() > 0.5 * on_strength else hi
        seg = env[m]
        k = int(np.argmax(seg))
        # keep the beat when there is no real peak inside the window (flat, or rising past an edge)
        if seg[k] <= 1e-9 or k in (0, len(seg) - 1):
            out.append(b)
            continue
        t = float(t_env[m][k])
        out.append(t if abs(t - b) <= window else b)
    return np.array(out)


def smooth(beats, half=4):
    """Local linear fit over a sliding window: removes frame jitter, follows slow drift."""
    beats = np.asarray(beats, dtype=float)
    sm = []
    for i in range(len(beats)):
        lo, hi = max(0, i - half), min(len(beats), i + half + 1)
        idx = np.arange(lo, hi)
        sm.append(np.polyval(np.polyfit(idx, beats[lo:hi], 1), i))
    return np.array(sm)


def extend(beats, duration, lead=0.2, beats_past_end=8):
    """Extrapolate whole beats so the grid covers 0-duration plus `beats_past_end` beats (default 8).
    full_grid() passes four bars: the template's last scene starts on D(12) (build.py refuses a
    scene after the end) and its end card addresses up to D(14), two bars later."""
    beats = list(beats)
    iv = float(np.median(np.diff(beats)))
    if not iv > 0:  # also NaN: the loops below would never end
        die(f"the beats are not in time order (median interval {iv:g}s); pick another seed")
    while beats[-1] < duration + beats_past_end * iv:
        beats.append(beats[-1] + iv)
    while beats[0] - iv > lead:
        beats.insert(0, beats[0] - iv)
    return np.array(beats)


def downbeat_phase(strengths, bpb=4):
    """Index (0..bpb-1) of the beat position with the strongest mean accent."""
    s = np.asarray(strengths, dtype=float)
    if len(s) < bpb:
        die(f"only {len(s)} beats heard, fewer than beats_per_bar ({bpb}): no downbeat can be found")
    return int(np.argmax([s[p::bpb].mean() for p in range(bpb)]))


def loudness_at(y, sr, t, n=2000):
    """RMS of the n samples from time t (from 0 when t is negative); 0 past the end (never NaN)."""
    a = max(0, int(t * sr))
    seg = y[a:a + n]
    return float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0


def full_grid(heard, strengths, duration, bpb=4):
    """Extend the beats heard in the audio to the whole video (plus four bars) and return the
    index of the first downbeat in the EXTENDED list. The accents come from the heard beats only:
    extrapolated beats have none, and would dilute the per-phase means."""
    beats = extend(heard, duration, beats_past_end=4 * bpb)
    prepended = int(np.argmin(np.abs(beats - heard[0])))
    return beats, (downbeat_phase(strengths, bpb) + prepended) % bpb


def analyse(y, sr, duration, bpb=4, bpm=None):
    import librosa
    _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", hop_length=HOP, bpm=bpm)
    if len(beats) < 8:
        die(f"beat_track found only {len(beats)} beats; pick another seed")
    kick, t_env = band_envelope(y, sr, 40, 160)
    hi, _ = band_envelope(y, sr, 2500)
    beats, shifted, on = phase_check(beats, kick, t_env)
    heard = smooth(refine(beats, kick, hi, t_env, on))
    # statistics from the beats in the audio; extrapolated beats would dilute them
    strengths = [peak_near(kick, t_env, b) + 25 * loudness_at(y, sr, b) for b in heard]
    iv = np.diff(heard)
    if bpm is not None:
        got = 60 / float(np.median(iv))
        if abs(got - bpm) > BPM_TOLERANCE * bpm:
            die(f"the grid came out at {got:.1f} BPM, not {bpm:g}: pick another seed")
    beats, phase = full_grid(heard, strengths, duration, bpb)
    print(f"half-beat shift: {'yes' if shifted else 'no'}; interval {iv.mean():.4f}s sd {iv.std() * 1000:.2f}ms; "
          f"first beat {beats[0]:.3f}; downbeat phase {phase}; {len(beats)} beats")
    return beats, phase


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("project_dir")
    ap.add_argument("--bpm", type=float)
    a = ap.parse_args(argv)
    if a.bpm is not None and not 30 <= a.bpm <= 300:  # also NaN: every comparison is False
        die(f"--bpm must be a tempo from 30 to 300, got {a.bpm:g}")
    audio, project_dir = a.audio, Path(a.project_dir)
    project = load_project(project_dir)
    import librosa
    try:
        # only the part the reel uses: make_bed cuts the same part, so an outro or a later section
        # of a long track never reaches the tracker
        y, sr = librosa.load(audio, sr=SR, mono=True, duration=project["duration"])
    except (OSError, RuntimeError, ValueError) as e:
        die(f"cannot read {audio}: {e}")
    bpb = project["beats_per_bar"]
    beats, phase = analyse(y, sr, project["duration"], bpb, a.bpm)
    doc = {"beats": [round(float(b), 4) for b in beats], "downbeat_phase": phase,
           "downbeats": [round(float(b), 3) for b in beats[phase::bpb]]}
    (project_dir / "beats.json").write_text(json.dumps(doc, indent=0) + "\n")
    print("downbeats:", [round(float(b), 2) for b in beats[phase::bpb]])


if __name__ == "__main__":
    main()
