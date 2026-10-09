#!/usr/bin/env python3
"""Finish a rendered reel: loudness, checks, contact sheet, versioned output.

1. Two-pass loudnorm (I=-14 LUFS, TP=-2 dBTP) on the 48 kHz WAV of the raw render. The final
   AAC file must measure within 1 LU of -14 LUFS and at most -1 dBTP, or the run fails.
2. A/V check before the AAC encode: the cross-correlation lag between the WAV before and
   after loudnorm must be < 5 ms.
3. Mux: video stream copied (-c:v copy), audio AAC, to renders/<app>-<variant>-v<N>.checking.mp4,
   N = one more than the highest existing version (a leftover .checking file counts too).
   An existing file is never overwritten.
4. Picture check: codec, size, frame count and duration of the video stream are unchanged,
   the size is the one of project.json's format, and the duration matches project.json within
   one frame.
5. Sync report: for each cue in cues.realized.json (the cues build.py actually mixed) with
   "sync": true, the cue's own sound is located within +-150 ms by a matched filter
   (normalised cross-correlation with the SFX file) on the final audio minus the music bed.
   A found cue more than one frame off fails the check, and so does a cue that is not found
   ("masked": under a louder sound, or missing). A cue that is meant to sit under a louder
   sound is marked "sync": false in cues.json and is not checked.
6. Contact sheet of frames from the final MP4.
7. Frame checks on the final MP4 (warnings only: they never fail the run or rename the file):
   a blank opening (frame 0 is the feed thumbnail; the hook must show within 1 s) and "pops",
   frame-to-frame changes far above their neighbours: a one-frame flash, or a cut that is near
   no beat and no scene start. They find one-frame events, not two texts on top of each other
   during a crossfade: that is for the critique loop in SKILL.md. A reel with sound also gets a
   warning for each "hold": nothing on screen moves for more than 0.8 s (the end card may hold
   2.5 s). The whole frame is measured, so a visible background pulse counts as movement.

8. Poster frame (only when every check passed): renders/<app>-<variant>-v<N>-poster.jpg, full video
   size, JPEG quality 90, the frame with the most detail among the settled frames of the scenes
   (pick_poster below). It is written before the report, inside the same guarded block as the mux:
   a failure there renames the MP4 to -failed and leaves no report. --poster-at <s> names the
   frame instead; a time outside the video exits 2 before any file is written.

Only when every check passed is the file renamed to ...-v<N>.mp4 (sheet: -v<N>-sheet.jpg). A
failed check exits 1 and names it ...-v<N>-failed.mp4; so does any other exit after the mux
(an error, Ctrl-C). The report, -v<N>-report.json, is written last, with the final names. A
.checking file left by a killed run was never checked; the script never deletes it.

A silent format (16:9, a web hero that loops) skips everything about sound: no loudnorm, lag
check, sync report or loudness gate, and cues.realized.json is not read. The mux drops the audio
(-c:v copy -an), and the checks that stay are the picture checks, the contact sheet and the frame
checks, plus three more, each of which fails the run: the output has no audio stream; the frame
count is exactly duration x fps (a loop is that many frames: one more or less is a hitch at the
seam); and the SEAM check (seam_check below): frame N-1 to frame 0 must look like any other step,
measured on a 480 px decode of the whole clip, because the 54 px frames of the frame checks cannot
see a small shift of a phone. A seam that cannot be checked (a decode failure, fewer than 8
frames) is a problem too, never a pass.

Usage: finish.py <project_dir> <raw_render.mp4> [--frames 1.0,5.2,...] [--poster-at 6.5]
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (attack_index, decode_audio, die, is_number, is_silent, load_project, read_json,  # noqa: E402
                    SCENE_SETTLE, SCENE_SETTLE_END, scene_spans, scene_windows)

SR = 48000
TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -2.0, 11.0
# gate on the final AAC file: AAC adds a few tenths of a dB of inter-sample peak on top of the
# -2 dBTP PCM target, so the delivered file is held to -1 dBTP (the usual platform ceiling)
MAX_LU_OFF, MAX_FINAL_TP = 1.0, -1.0
MAX_LAG = 0.005
SYNC_WINDOW = 0.150
TEMPLATE_LEN = 0.25  # seconds of each SFX used as the matched-filter template
MIN_MATCH = 0.2      # normalised correlation below this = the sound is not in the window
# frame checks, on frames decoded to FRAME_W px wide grayscale. Calibrated 2026-09-29 on three
# delivered reels: an empty gradient opening measures 1.4-2.2 detail, frames with text or UI 2.8+;
# scene cuts change 30-100 gray levels in one frame, a headline settling after its slam 4-10.
FRAME_W = 54
BLANK_DETAIL = 2.5   # mean neighbouring-pixel difference below this = nothing to read on the frame
POP_MIN = 12.0       # a spike changes at least this many gray levels (mean) from the frame before
POP_RATIO = 3.0      # ... and this many times the median change of the 3 frames on each side
POP_GROUP = 3        # spikes at most this many frames apart are one fast move
POP_MOVE_MAX = 0.3   # seconds: a fast move is never longer (the longest in the calibration reels: 0.07 s)
FLASH_BACK = 3.0     # a flash: the frame after the odd one is this many times closer to the one before
POP_LEAD = 0.15      # a fast move may start up to this long before the beat it lands on
HOOK_BY = 1.0        # seconds: something readable must be on screen by then
HOLD_PIX = 8         # a pixel has changed when it differs from the run's first frame by more than this
HOLD_SHARE = 0.002   # ... and a frame has changed when more than this share of its pixels has
HOLD_MAX = 0.8       # seconds: a longer still run is a dead hold (references/storyboard.md, "Density")
HOLD_END = 2.5       # seconds: the end card may hold this long
HOLD_END_SLACK = 2   # frames: a run that ends this close to the last frame is the end card
# the seam check of a silent loop, on frames decoded SEAM_W px wide: the 54 px frames of the frame
# checks turn a 5 px shift of a phone into 0.14 px. A step is judged by two measures: `mad` (mean
# gray-level change) and `moved` (the share of pixels that change by more than SEAM_PIX levels: a
# shifted sharp edge changes few pixels a lot, which the mean hides). The seam is bad when either
# is above max(its floor, SEAM_RATIO x the largest of the SEAM_REST steps on each side of the seam).
POSTER_SETTLE = SCENE_SETTLE   # seconds after a scene start: its text and UI have landed (references/storyboard.md)
POSTER_EDGE = 0.05    # a candidate stays this far inside the end of its window and of the video
POSTER_LAST = SCENE_SETTLE_END     # the last scene: this long before the end of the video
POSTER_QUALITY = 90
SEAM_W = 480
SEAM_PIX = 16
SEAM_REST = 3
SEAM_MIN_FRAMES = 8
SEAM_MIN_MAD = 0.6
SEAM_MIN_MOVED = 0.002
SEAM_RATIO = 3.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        die(f"{cmd[0]} failed ({' '.join(map(str, cmd[1:6]))} ...):\n{r.stderr[-800:]}")
    return r


def next_version_path(renders, stem):
    """renders/<stem>-v<N>.mp4 with N = max existing (incl. -failed and .checking) + 1."""
    pat = re.compile(re.escape(stem) + r"-v(\d+)(?:-failed|\.checking)?\.mp4$")
    nums = [int(m.group(1)) for p in renders.glob(f"{stem}-v*.mp4") if (m := pat.match(p.name))]
    return renders / f"{stem}-v{max(nums, default=0) + 1}.mp4"


def video_info(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
               "stream=codec_name,width,height,nb_read_packets,duration:format=duration", "-of", "json",
               str(path)]).stdout
    doc = json.loads(out)
    streams = doc.get("streams") or []
    if not streams:
        die(f"{path} has no video stream")
    s = streams[0]
    # some containers keep the duration on the format, not the stream; ffprobe writes "N/A" when
    # it has none
    duration = next((d for d in (_seconds(s.get("duration")), _seconds(doc.get("format", {}).get("duration")))
                     if d is not None), None)
    if duration is None:
        die(f"ffprobe gives no duration for {path}")
    return {"codec": s["codec_name"], "width": s["width"], "height": s["height"],
            "frames": int(s["nb_read_packets"]), "duration": round(duration, 3)}


def _seconds(v):
    """A duration from ffprobe, or None for "N/A", a missing value, NaN or infinity."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


LOUDNORM = f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"


def measure(path):
    """loudnorm analysis pass: input_i, input_tp, input_lra, input_thresh, target_offset."""
    p = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(path), "-af",
                        LOUDNORM + ":print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr)
    if p.returncode or not m:
        die("loudnorm analysis failed:\n" + p.stderr[-800:])
    return json.loads(m.group(0))


def loudnorm(src_wav, dst_wav):
    base = LOUDNORM
    s = measure(src_wav)
    af = (f"{base}:measured_I={s['input_i']}:measured_TP={s['input_tp']}:measured_LRA={s['input_lra']}"
          f":measured_thresh={s['input_thresh']}:offset={s['target_offset']}:linear=true")
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src_wav), "-af", af, "-ar", str(SR), "-c:a", "pcm_s16le",
         str(dst_wav)])
    return s


def lag_seconds(a, b, sr=SR, max_lag=0.1):
    """Lag of b against a (seconds), searched within +-max_lag."""
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    c = ss.correlate(b, a, mode="full", method="fft")
    mid = n - 1
    k = int(max_lag * sr)
    seg = c[mid - k:mid + k + 1]
    return (int(np.argmax(seg)) - k) / sr


def window_energy(x, n):
    """Sum of squares of every n-sample window of x (len(x) - n + 1 values), in O(len(x))."""
    run_sum = np.concatenate(([0.0], np.cumsum(np.asarray(x, dtype=np.float64) ** 2)))
    return run_sum[n:] - run_sum[:-n]


def locate(y, tmpl, t, window=SYNC_WINDOW, sr=SR):
    """Matched filter: where does `tmpl` (the cue's own sound) start in y, within t +- window?
    Returns (start_time, normalised correlation 0-1). Music does not correlate with the SFX
    waveform, so the peak marks the SFX even inside a full mix; the gain of loudnorm cancels."""
    n = len(tmpl)
    a = max(0, int(round((t - window) * sr)))
    seg = y[a:int(round((t + window) * sr)) + n]
    if len(seg) < n:
        return None, 0.0
    num = ss.correlate(seg, tmpl, mode="valid", method="fft")
    energy = window_energy(seg, n)
    ncc = num / (np.sqrt(np.maximum(energy, 1e-12)) * np.linalg.norm(tmpl) + 1e-12)
    k = int(np.argmax(ncc))
    return (a + k) / sr, float(ncc[k])


def required_match(n, sr=SR, window=SYNC_WINDOW):
    """Correlation a sound must reach to count as found. Noise alone reaches about
    sqrt(2 ln(lags) / n) by chance, which is high for very short sounds."""
    lags = 2 * window * sr + 1
    return max(MIN_MATCH, 1.5 * np.sqrt(2 * np.log(lags) / max(n, 1)))


def remove_bed(y, bed):
    """Subtract the music bed (least-squares gain) so quiet SFX stand out for matching."""
    n = min(len(y), len(bed))
    if n == 0 or not np.any(bed[:n]):
        return y
    g = float(np.dot(y[:n], bed[:n]) / np.dot(bed[:n], bed[:n]))
    out = y.astype(np.float64).copy()
    out[:n] -= g * bed[:n]
    return out


def loudness_problems(final):
    i, tp = float(final["input_i"]), float(final["input_tp"])
    out = []
    if abs(i - TARGET_I) > MAX_LU_OFF:
        out.append(f"final loudness {i:.2f} LUFS is more than {MAX_LU_OFF:g} LU from {TARGET_I:g}")
    if tp > MAX_FINAL_TP:
        out.append(f"final true peak {tp:.2f} dBTP is above {MAX_FINAL_TP:g} dBTP")
    return out


def sync_report(y, realized, fps, project_dir, sr=SR):
    """Per cue: found (with delta), off by more than one frame, or masked (not found: usually
    under a louder sound). Returns (rows, problems)."""
    frame = 1.0 / fps
    bed_path = Path(project_dir) / "assets" / "audio" / "bgm.wav"
    if bed_path.is_file():
        y = remove_bed(y, decode_audio(bed_path, sr))
    templates, rows = {}, []
    for cue in realized:
        if not cue.get("sync", True):
            continue
        if cue["file"] not in templates:
            path = Path(project_dir) / cue["file"]
            if not path.is_file():
                die(f"{path} (cue {cue['id']}) is gone since build.py ran; rebuild and render again")
            snd = decode_audio(path, sr)
            lead = attack_index(snd)
            templates[cue["file"]] = (snd[lead:lead + int(TEMPLATE_LEN * sr)], lead / sr)
        tmpl, lead = templates[cue["file"]]
        expected = cue["time"] + lead  # where the audible attack should be
        found, score = locate(y, tmpl, expected, sr=sr)
        base = {**cue, "lead_ms": round(lead * 1000, 1), "match": round(score, 3)}
        if found is None or score < required_match(len(tmpl), sr):
            rows.append({**base, "found": None, "delta_ms": None, "flag": "masked"})
            continue
        delta = found - expected
        rows.append({**base, "found": round(found, 4), "delta_ms": round(delta * 1000, 1),
                     "flag": "off by more than one frame" if abs(delta) > frame else None})
    problems = [f"cue {r['id']} at {r['time']:.3f}s: off by more than one frame ({r['delta_ms']:+.1f} ms)"
                for r in rows if r["flag"] == "off by more than one frame"]
    problems += [f"cue {r['id']} at {r['time']:.3f}s: not found in the final audio (masked by a louder sound, "
                 f"or missing). If it is meant to sit under a louder sound, set \"sync\": false on it in "
                 f"cues.json and rebuild" for r in rows if r["flag"] == "masked"]
    return rows, problems


def late_starts(pdir, realized, fps, sr=SR):
    """{file: ms of leading silence} for the files of align "start" cues (checked for sync or not)
    whose sound begins more than one frame after the cue time."""
    out = {}
    for f in dict.fromkeys(c["file"] for c in realized if c.get("align") == "start"):
        path = Path(pdir) / f
        if path.is_file():
            ms = attack_index(decode_audio(path, sr)) / sr * 1000
            if ms > 1000 / fps:
                out[f] = ms
    return out


def contact_sheet(mp4, times, dest):
    from PIL import Image
    tmp = Path(tempfile.mkdtemp(prefix="reel-sheet-"))
    try:
        thumbs = []
        for i, t in enumerate(times):
            f = tmp / f"{i:03d}.png"
            run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(mp4), "-frames:v", "1",
                 "-vf", "scale=270:-2", str(f)])
            thumbs.append(Image.open(f).convert("RGB"))
        tw, th = thumbs[0].size
        cols = min(len(thumbs), 6)
        rows = -(-len(thumbs) // cols)
        sheet = Image.new("RGB", (cols * tw, rows * th), "black")
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
        sheet.save(dest, quality=88)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def decode_gray(mp4, width, height, frame_w=FRAME_W, dtype=np.float32):
    """Every frame of mp4 as grayscale (float32, or `dtype`), frame_w px wide, height kept in
    proportion. Raises (never die()): the frame checks must not end the run."""
    h = max(2, round(frame_w * height / width / 2) * 2)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(mp4), "-vf", f"scale={frame_w}:{h},format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg could not decode the frames: {r.stderr.decode(errors='replace')[-300:]}")
    n = len(r.stdout) // (frame_w * h)
    return np.frombuffer(r.stdout[:n * frame_w * h], np.uint8).reshape(n, h, frame_w).astype(dtype, copy=False)


def frame_detail(frames):
    """Mean absolute difference between neighbouring pixels, per frame: ~0 on a flat colour."""
    return (np.abs(np.diff(frames, axis=2)).mean(axis=(1, 2))
            + np.abs(np.diff(frames, axis=1)).mean(axis=(1, 2)))


def pop_events(frames, dt):
    """Spikes of the frame-to-frame change: [{"type": "flash" | "cut", "time", "frames"}].
    A flash is one odd frame (the change into it and back out are one event); a cut is one spike
    or a run of spikes at most POP_GROUP frames apart and at most POP_MOVE_MAX long (one fast
    move). Without that length cap one beat could mark a whole chain of later cuts as planned."""
    n = len(frames)
    d = np.zeros(n)
    d[1:] = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    spikes = []
    for i in range(1, n):
        around = np.concatenate([d[max(1, i - 3):i], d[i + 1:i + 4]])  # d[0] is not a change
        if d[i] > POP_MIN and (not len(around) or d[i] > POP_RATIO * np.median(around)):
            spikes.append(i)
    # flashes first: grouped into a fast move, a glitch frame next to a cut would go unreported
    events, cuts, spikeset = [], [], set(spikes)
    for a in spikes:
        if a not in spikeset:
            continue
        if a + 1 in spikeset and np.abs(frames[a + 1] - frames[a - 1]).mean() < d[a] / FLASH_BACK:
            events.append({"type": "flash", "time": round(a * dt, 3), "frames": 1})
            spikeset -= {a, a + 1}
        else:
            cuts.append(a)
    longest = max(0, int(POP_MOVE_MAX / dt + 1e-9))  # frames from the first spike of a move to its last
    i = 0
    while i < len(cuts):
        run_ = [cuts[i]]
        while i + 1 < len(cuts) and cuts[i + 1] - run_[-1] <= POP_GROUP and cuts[i + 1] - run_[0] <= longest:
            i += 1
            run_.append(cuts[i])
        events.append({"type": "cut", "time": round(run_[0] * dt, 3), "end": round(run_[-1] * dt, 3),
                       "frames": run_[-1] - run_[0] + 1})
        i += 1
    return sorted(events, key=lambda e: e["time"])


def scene_starts(html):
    """data-start of every live <section> of the built index.html (as build.check_scenes reads it).
    Returns (starts, notes): a value that is not a finite number skips only its own section, with
    a note, so one bad section never drops the other scene starts."""
    live = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    starts, notes = [], []
    for tag in re.findall(r"<section\b[^>]*>", live):
        m = re.search(r"""\bdata-start\s*=\s*(["'])(.*?)\1""", tag)
        if not m:
            continue
        try:
            t = float(m.group(2))
        except ValueError:
            t = None
        if not is_number(t):
            notes.append(f"index.html: data-start {m.group(2)!r} is not a number: that scene start is "
                         f"not compared with cuts")
            continue
        starts.append(t)
    return starts, notes


def poster_candidates(spans, duration):
    """Times of the settled frame of each scene. The candidate is POSTER_SETTLE after the scene
    start (POSTER_LAST before the end for the last scene), moved back inside the scene's clean
    window (common.scene_windows); a scene whose candidate falls outside its window (an empty
    window always does) or outside the video gives none. Frame 0 is never a candidate."""
    times = []
    windows = scene_windows(spans, duration)
    for i, (start, lo, hi) in enumerate(windows):
        t = duration - POSTER_LAST if i == len(windows) - 1 else start + POSTER_SETTLE
        if t >= hi:
            t = hi - POSTER_EDGE
        t = round(t, 3)
        if t < lo or t <= 0 or t >= duration - POSTER_EDGE:
            continue
        times.append(t)
    return times


def pick_poster(frames, fps, spans, duration, silent=False, forced_t=None):
    """(frame index, report) of the poster. The winner is the candidate with the most detail
    (frame_detail on the 54 px frames); a tie goes to the later time. With no candidate, and for a
    silent project of one section (a hero loop), the frame in the middle of the clip. The score and the
    JPEG both come from the frame index round(t * fps)."""
    detail = frame_detail(frames)
    n = len(frames)

    def at(t):
        i = min(max(int(round(t * fps)), 0), n - 1)
        return i, {"t": round(t, 3), "score": round(float(detail[i]), 3)}

    if forced_t is not None:
        i, row = at(forced_t)
        return i, {"t": row["t"], "score": row["score"], "candidates": [row]}
    times = [] if silent and len(spans) <= 1 else poster_candidates(spans, duration)
    times = [t for t in times if round(t * fps) > 0]
    if not times:
        i = n // 2
        row = {"t": round(i / fps, 3), "score": round(float(detail[i]), 3)}
        return i, {**row, "candidates": [row]}
    rows = [at(t) for t in times]
    i, row = max(rows, key=lambda r: (r[1]["score"], r[1]["t"]))
    return i, {"t": row["t"], "score": row["score"], "candidates": [r for _, r in rows]}


def write_poster(mp4, index, dest):
    """The decoded frame number `index` of mp4, at full size, as a JPEG at `dest`."""
    from PIL import Image
    tmp = Path(tempfile.mkdtemp(prefix="reel-poster-"))
    try:
        png = tmp / "frame.png"
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(mp4), "-vf", f"select=eq(n\\,{index})",
             "-fps_mode", "passthrough", "-frames:v", "1", str(png)])
        if not png.exists():
            raise RuntimeError(f"frame {index} was not decoded")
        Image.open(png).convert("RGB").save(dest, quality=POSTER_QUALITY)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_poster(pdir, mp4, vi, project, dest, silent, forced_t=None):
    """Choose the poster of mp4 and write it to dest. Returns the report entry. Raises on failure."""
    frames = decode_gray(mp4, vi["width"], vi["height"])
    if not len(frames):
        raise RuntimeError("no frame decoded")
    try:
        spans = scene_spans((pdir / "index.html").read_text())
    except OSError:
        spans = []
    index, info = pick_poster(frames, project["fps"], spans, project["duration"], silent, forced_t)
    write_poster(mp4, index, dest)
    return {"path": str(dest), **info}


def _step(a, b):
    """(mean change in gray levels, share of pixels that change by more than SEAM_PIX) between two frames."""
    diff = np.abs(a.astype(np.float32) - b.astype(np.float32))
    return float(diff.mean()), float((diff > SEAM_PIX).mean())


def seam_check(frames):
    """The step from the last frame of a loop to its first, against the steps beside the seam.
    Returns {"ok", "mad", "moved", "rest_mad", "rest_moved", "limit_mad", "limit_moved", "frames"}
    or, with fewer than SEAM_MIN_FRAMES frames, {"ok": False, "frames": n, "error": ...}: a seam
    that cannot be measured is not a good seam."""
    n = len(frames)
    if n < SEAM_MIN_FRAMES:
        return {"ok": False, "frames": n, "error": f"only {n} frames, at least {SEAM_MIN_FRAMES} are needed"}
    mad, moved = _step(frames[n - 1], frames[0])
    rest = ([_step(frames[i], frames[i + 1]) for i in range(n - 1 - SEAM_REST, n - 1)]
            + [_step(frames[i], frames[i + 1]) for i in range(SEAM_REST)])
    rest_mad, rest_moved = max(r[0] for r in rest), max(r[1] for r in rest)
    limit_mad = max(SEAM_MIN_MAD, SEAM_RATIO * rest_mad)
    limit_moved = max(SEAM_MIN_MOVED, SEAM_RATIO * rest_moved)
    return {"ok": bool(mad <= limit_mad and moved <= limit_moved), "frames": n,
            "mad": round(mad, 4), "moved": round(moved, 5), "rest_mad": round(rest_mad, 4),
            "rest_moved": round(rest_moved, 5), "limit_mad": round(limit_mad, 4),
            "limit_moved": round(limit_moved, 5)}


def expected_frames(project):
    """(frames, tolerance) of a loop: exactly duration x fps for a whole number of frames at a
    whole fps; one frame either way for a rate like 29.97, where the renderer rounds."""
    exact = project["duration"] * project["fps"]
    whole = float(project["fps"]).is_integer() and abs(exact - round(exact)) < 1e-6
    return round(exact), 0 if whole else 1


def silent_loop_problems(mp4, project, vi):
    """Frame count and seam of a silent loop, on one decode of the whole clip. Returns
    (problems, seam_report). Never raises: a decode that fails is a problem, because the seam is
    the whole contract of the format."""
    try:
        frames = decode_gray(mp4, vi["width"], vi["height"], SEAM_W, np.uint8)
        seam = seam_check(frames)
    except Exception as e:  # noqa: BLE001
        return [f"seam: could not be checked ({e!r})"], {"ok": False, "error": repr(e)}
    problems = []
    want, tol = expected_frames(project)
    if abs(len(frames) - want) > tol:
        problems.append(f"{len(frames)} frames, a {project['duration']:g} s loop at {project['fps']:g} fps "
                        f"is {want}{f' (+-{tol})' if tol else ''}: one frame more or less is a hitch at the seam")
    if "error" in seam:
        problems.append(f"seam: could not be checked ({seam['error']})")
    elif not seam["ok"]:
        problems.append(
            f"seam: the loop jumps from its last frame to its first (mean change {seam['mad']:.2f} gray levels, "
            f"limit {seam['limit_mad']:.2f}; {seam['moved'] * 100:.2f}% of pixels changed, limit "
            f"{seam['limit_moved'] * 100:.2f}%): every animated property must end at its value at t = 0")
    seam["frames_expected"] = want
    return problems, seam


def has_audio_stream(path):
    return bool(run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                     "-of", "csv=p=0", str(path)]).stdout.strip())


def still_runs(frames):
    """(first, end) frame indices of every run of frames that stay within HOLD_SHARE changed pixels
    of the run's first frame (end is exclusive). Comparing with the first frame, not the frame
    before, makes a slow creep count as change once it adds up."""
    runs, i, n = [], 0, len(frames)
    while i < n:
        j = i + 1
        while j < n and float((np.abs(frames[j] - frames[i]) > HOLD_PIX).mean()) <= HOLD_SHARE:
            j += 1
        runs.append((i, j))
        i = j
    return runs


def dead_holds(frames, dt):
    """[{"time", "length"}] of each still run longer than HOLD_MAX, except an end card: a run that
    ends within HOLD_END_SLACK frames of the last frame and is at most HOLD_END long."""
    holds, n = [], len(frames)
    for first, end in still_runs(frames):
        length = (end - first) * dt
        if end - 1 >= n - 1 - HOLD_END_SLACK and length <= HOLD_END:
            continue
        if length > HOLD_MAX:
            holds.append({"time": round(first * dt, 3), "length": round(length, 3)})
    return holds


def frame_checks(pdir, mp4, vi, silent=False):
    """Blank opening and pops on the final MP4. Returns the report dict; its "warnings" are
    printed and never change the exit code. Reads files with plain read_text/json.loads, never
    read_json or die(): a SystemExit here would turn a good reel into -failed. A silent project
    has no beats.json to compare cuts with."""
    frames = decode_gray(mp4, vi["width"], vi["height"])
    if not len(frames):
        raise RuntimeError("no frame decoded")
    # video_info gives the video STREAM's duration (the container's only as a fallback): muxed audio
    # that runs longer must not stretch the frame times
    dt = vi["duration"] / len(frames)
    warnings, notes = [], []

    detail = frame_detail(frames)
    readable = np.flatnonzero(detail >= BLANK_DETAIL)
    first = round(float(readable[0] * dt), 3) if len(readable) else None
    if first is None:
        warnings.append("no frame has anything to read on it: the video looks empty")
    else:
        if detail[0] < BLANK_DETAIL:
            warnings.append("frame 0 is blank, and feeds show frame 0 as the thumbnail: start on the hook "
                            "text or UI")
        if first > HOOK_BY:
            warnings.append(f"nothing to read until {first:.2f} s: the hook must show within {HOOK_BY:g} s")

    def html_starts():
        starts, html_notes = scene_starts((pdir / "index.html").read_text())
        notes.extend(html_notes)
        return starts

    marks = []
    sources = (("index.html", html_starts),
               ("beats.json", lambda: [float(b) for b in json.loads((pdir / "beats.json").read_text())["beats"]]))
    if silent:
        sources = sources[:1]
    for name, load in sources:
        try:
            marks += load()
        except (OSError, ValueError, TypeError, KeyError, OverflowError) as e:
            notes.append(f"{name} not read ({e!r}): cuts are not compared with it")
    events = pop_events(frames, dt)
    for e in events:
        if e["type"] == "flash":
            warnings.append(f"one-frame flash at {e['time']:.2f} s: a glitch frame (look at it)")
            continue
        e["planned"] = any(e["time"] - 2 * dt - 1e-6 <= m <= e["end"] + POP_LEAD for m in marks)
        if not e["planned"]:
            warnings.append(f"sudden change at {e['time']:.2f} s near no beat and no scene start (look at it)")
    holds = [] if silent else dead_holds(frames, dt)
    for h in holds:
        warnings.append(f"still for {h['length']:.2f} s from {h['time']:.2f} s: nothing on screen moves (look at it)")
    return {"frame0_blank": bool(detail[0] < BLANK_DETAIL), "first_detail_time": first,
            "events": events, "holds": holds, "warnings": warnings, "notes": notes}


def picture_problems(project, vi_raw, vi_out):
    """The video stream is unchanged by the mux, has the size of the format and the duration of
    project.json (within one frame)."""
    problems = []
    if vi_raw != vi_out:
        problems.append(f"video stream changed: {vi_raw} -> {vi_out}")
    if (vi_out["width"], vi_out["height"]) != (project["width"], project["height"]):
        problems.append(f"video is {vi_out['width']}x{vi_out['height']}, project.json says "
                        f"{project['width']}x{project['height']} (format {project['format']}): build and render again")
    frame = 1.0 / project["fps"]
    if abs(vi_out["duration"] - project["duration"]) > frame + 1e-6:
        problems.append(f"video is {vi_out['duration']}s, project.json says {project['duration']:g}s")
    return problems


def contact_sheet_times(project, vi_out, frames):
    dur = project["duration"]
    times = frames or [round(dur * i / 9, 2) for i in range(9)] + [round(dur - 0.1, 2)]
    last = min(dur, vi_out["duration"]) - 0.05
    return [min(t, last) for t in times]


def _checks_silent(pdir, project, raw_mp4, checking, sheet, frames):
    """The checks of a silent loop (see the module docstring). Same return as _checks. A clip that
    cannot be copied, probed or decoded is a problem in the report, never an unreported crash: the
    seam is the whole contract of the format, and an unchecked seam is not a pass."""
    problems = []
    vi_out = None
    try:
        run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(raw_mp4), "-map", "0:v:0", "-c:v", "copy", "-an",
             "-movflags", "+faststart", str(checking)])
        vi_raw, vi_out = video_info(raw_mp4), video_info(checking)
        problems += picture_problems(project, vi_raw, vi_out)
        if has_audio_stream(checking):
            problems.append("the output has an audio stream: a silent format must not")
    except (Exception, SystemExit) as e:  # die() in video_info is a SystemExit
        vi_out = None
        problems.append(f"seam: could not be checked (the clip could not be read: {e!r})")
        if not checking.exists():
            shutil.copyfile(raw_mp4, checking)  # keep the raw clip as the -failed file, to look at
    if vi_out is None:
        return problems, {"silent": True, "video": None, "seam": {"ok": False, "error": "clip not readable"},
                          "frames": {"warnings": [], "holds": [], "notes": []}, "problems": problems}
    try:
        contact_sheet(checking, contact_sheet_times(project, vi_out, frames), sheet)
    except (Exception, SystemExit) as e:  # a sheet that cannot be made is a note: the seam still decides
        sheet_note = f"contact sheet not made: {e!r}"
    else:
        sheet_note = None
    try:
        frame_report = frame_checks(pdir, checking, vi_out, silent=True)
    except Exception as e:  # a heuristic check that cannot run is a note, never a failed reel
        frame_report = {"error": repr(e), "warnings": [], "holds": [], "notes": [f"frame checks did not run: {e!r}"]}
    if sheet_note:
        frame_report["notes"].append(sheet_note)
    loop_problems, seam = silent_loop_problems(checking, project, vi_out)
    problems += loop_problems
    return problems, {"silent": True, "video": vi_out, "seam": seam, "frames": frame_report,
                      "problems": problems}


def _checks(pdir, project, raw_mp4, realized, checking, sheet, frames):
    """Mux the loudness-normalised audio to `checking`, make the contact sheet at `sheet` and run
    every check. Returns (problems, report); naming the files is the caller's job."""
    work = Path(tempfile.mkdtemp(prefix="reel-finish-"))
    problems = []
    try:
        raw_wav, norm_wav = work / "raw.wav", work / "norm.wav"
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(raw_mp4), "-vn", "-ar", str(SR), "-ac", "2",
             "-c:a", "pcm_s16le", str(raw_wav)])
        meas = loudnorm(raw_wav, norm_wav)
        lag = lag_seconds(decode_audio(raw_wav, SR), decode_audio(norm_wav, SR))
        if abs(lag) >= MAX_LAG:
            problems.append(f"loudnorm moved audio by {lag * 1000:.1f} ms")
        run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(raw_mp4), "-i", str(norm_wav), "-map", "0:v:0",
             "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             str(checking)])
    finally:
        shutil.rmtree(work, ignore_errors=True)

    vi_raw, vi_out = video_info(raw_mp4), video_info(checking)
    problems += picture_problems(project, vi_raw, vi_out)

    rows, sync_problems = sync_report(decode_audio(checking, SR), realized, project["fps"], pdir)
    problems += sync_problems

    contact_sheet(checking, contact_sheet_times(project, vi_out, frames), sheet)
    try:
        frame_report = frame_checks(pdir, checking, vi_out)
    except Exception as e:  # a heuristic check that cannot run is a note, never a failed reel
        frame_report = {"error": repr(e), "warnings": [], "holds": [], "notes": [f"frame checks did not run: {e!r}"]}

    final = measure(checking)
    problems += loudness_problems(final)
    return problems, {"loudnorm_input": meas, "final_lufs": final["input_i"], "final_tp": final["input_tp"],
                      "lag_ms": round(lag * 1000, 2), "video": vi_out, "sync": rows, "frames": frame_report,
                      "problems": problems}


def finish(project_dir, raw_mp4, frames=None, poster_at=None):
    pdir = Path(project_dir)
    project = load_project(pdir)
    raw_mp4 = Path(raw_mp4)
    if not raw_mp4.is_file():
        die(f"{raw_mp4} not found")
    silent = is_silent(project)
    realized = []
    realized_path = pdir / "cues.realized.json"
    if not silent:
        if not realized_path.is_file():
            die(f"{realized_path} not found: run build.py before finish.py")
        realized = read_json(realized_path, list)
    for cue in realized:
        if not (isinstance(cue, dict) and isinstance(cue.get("id"), str) and isinstance(cue.get("file"), str)
                and isinstance(cue.get("time"), (int, float)) and not isinstance(cue.get("time"), bool)):
            die(f"{realized_path}: every entry needs id, file and time (it is written by build.py: rebuild)")
    if poster_at is not None:  # a bad value exits 2 before any file is written
        vi_raw = video_info(raw_mp4)
        if not (math.isfinite(poster_at) and 0 <= poster_at and round(poster_at * project["fps"]) < vi_raw["frames"]):
            die(f"--poster-at {poster_at:g}: the video has {vi_raw['frames']} frames at {project['fps']:g} fps, "
                f"so the time must be from 0 to {(vi_raw['frames'] - 1) / project['fps']:.3f} s")
    renders = pdir / "renders"
    renders.mkdir(exist_ok=True)
    stem = f"{project['app']}-{project['variant']}"
    out = next_version_path(renders, stem)
    checking = out.with_name(out.stem + ".checking.mp4")
    sheet = out.with_name(out.stem + ".checking-sheet.jpg")
    failed, failed_sheet = out.with_name(out.stem + "-failed.mp4"), out.with_name(out.stem + "-failed-sheet.jpg")
    good_sheet = out.with_name(out.stem + "-sheet.jpg")
    poster_path = out.with_name(out.stem + "-poster.jpg")
    report_path = out.with_name(out.stem + "-report.json")
    partial = report_path.with_name("." + report_path.name + ".partial")
    # reads only the cue sounds, so it runs before the mux: an error here leaves no file in renders/
    late = late_starts(pdir, realized, project["fps"])
    try:
        if silent:
            problems, report = _checks_silent(pdir, project, raw_mp4, checking, sheet, frames)
        else:
            problems, report = _checks(pdir, project, raw_mp4, realized, checking, sheet, frames)
        poster = None
        if not problems:  # before the report: a failure here must leave no report that names it
            poster = make_poster(pdir, checking, report["video"], project, poster_path, silent, poster_at)
        final_mp4, final_sheet = (failed, failed_sheet) if problems else (out, good_sheet)
        checking.rename(final_mp4)
        if silent and not sheet.exists():  # a silent run can fail before it made a sheet
            final_sheet = None
        else:
            sheet.rename(final_sheet)
        report = {"output": str(final_mp4), "sheet": str(final_sheet) if final_sheet else None, "poster": poster,
                  **report}
        partial.write_text(json.dumps(report, indent=1) + "\n")
        os.replace(partial, report_path)
    except BaseException:
        # an error or Ctrl-C anywhere after the mux, up to the report: the run did not complete, so
        # nothing may keep a delivery name; no report is left
        for src, dst in ((checking, failed), (out, failed), (sheet, failed_sheet), (good_sheet, failed_sheet)):
            if src.exists():
                src.rename(dst)
        partial.unlink(missing_ok=True)
        poster_path.unlink(missing_ok=True)
        raise

    rows, vi_out = report.get("sync"), report["video"]
    if silent:
        pass
    elif rows:
        found = [r for r in rows if r["delta_ms"] is not None]
        worst = max((abs(r["delta_ms"]) for r in found), default=0)
        masked = [r["id"] for r in rows if r["delta_ms"] is None]
        print(f"sync: {len(found)} of {len(rows)} checked cues found, worst {worst:.1f} ms"
              + (f"; not found: {', '.join(masked)}" if masked else ""))
    else:
        print("sync: no cues (no SFX mixed)")
    for w in report["frames"]["warnings"]:
        print(f"warning: {w}", file=sys.stderr)
    for note in report["frames"]["notes"]:
        print(f"note: {note}", file=sys.stderr)
    for f, ms in late.items():
        print(f"warning: {f} starts with {ms:.0f} ms of silence and its cues use align \"start\", so it "
              f"sounds {ms:.0f} ms after the cue time; use align \"attack\" or trim the file", file=sys.stderr)
    if silent:
        seam = report["seam"]
        print(f"silent: no audio; seam {seam.get('mad', 'n/a')} gray levels (limit {seam.get('limit_mad', 'n/a')}); "
              f"video {vi_out}")
    else:
        print(f"loudness {report['final_lufs']} LUFS, true peak {report['final_tp']} dBTP; loudnorm lag "
              f"{report['lag_ms']:.2f} ms; video {vi_out}")
    if problems:
        print("FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
        print(f"output kept as {final_mp4}", file=sys.stderr)
        return 1
    print(f"ok: {final_mp4}\ncontact sheet: {final_sheet}\nposter: {poster['path']} (t={poster['t']:g} s)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("raw_mp4")
    ap.add_argument("--frames", help="comma-separated times for the contact sheet")
    ap.add_argument("--poster-at", type=float, help="time in seconds of the poster frame (default: chosen)")
    a = ap.parse_args()
    try:
        frames = [float(x) for x in a.frames.split(",")] if a.frames else None
    except ValueError:
        die(f"--frames takes comma-separated seconds, got {a.frames!r}")
    if frames and min(frames) < 0:
        die("--frames times must be 0 or more")
    if a.poster_at is not None and not (math.isfinite(a.poster_at) and a.poster_at >= 0):
        die(f"--poster-at takes a time in seconds, 0 or more, got {a.poster_at!r}")
    sys.exit(finish(a.project_dir, a.raw_mp4, frames, a.poster_at))


if __name__ == "__main__":
    main()
