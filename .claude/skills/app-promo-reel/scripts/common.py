"""Shared helpers: project.json, the beat grid and the D()/E() beat addressing.

Beat addressing (one signature everywhere, see references/pipeline.md):
  D(bar, beat=0)  time of `beat` (0-based) inside `bar`. Bar 0 starts on the first
                  downbeat; negative bars are pickup beats before it.
  E(bar, beat=0)  the "and": halfway between D(bar, beat) and the next beat.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

# the frame size of each format; "9:16" is the default and the reference for FRAME_SCALE
FORMATS = {"9:16": (1080, 1920), "4:5": (1080, 1350), "16:9": (1920, 1080)}
# formats with no music, no beat grid, no cues and no audio: a web hero that loops
SILENT_FORMATS = ("16:9",)
# The feed safe box per format (x0, y0, x1, y1 in px of the frame): the big vertical feeds draw their
# own UI outside it (references/storyboard.md, "Feed safe zones"). The 16:9 hero is a web page: none.
FEED_BOXES = {"9:16": (64, 270, 960, 1500), "4:5": (64, 96, 1016, 1254)}
# Seconds after a scene start when what entered with it has landed, and before the end of its window
# when what entered late has landed too (references/storyboard.md).
SCENE_SETTLE = 1.1
SCENE_SETTLE_END = 0.5
HERO_DURATION = 8.0
SILENT_MIN_DURATION = 4.0
PROJECT_DEFAULTS = {
    "duration": 30.0,
    "fps": 30,
    "format": "9:16",
    "width": 1080,
    "height": 1920,
    "beats_per_bar": 4,
    "stores": ["app_store", "google_play"],
}
KNOWN_STORES = ("app_store", "google_play")


def is_silent(project):
    """True for a project (or format string) of a silent format."""
    fmt = project if isinstance(project, str) else project.get("format")
    return fmt in SILENT_FORMATS


def is_number(v):
    """A finite JSON number: int or float, not bool (True is an int in Python), not NaN/Infinity
    (Python's json accepts both), not an int too large for a float (a 400-digit JSON integer)."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    try:
        return math.isfinite(v)
    except OverflowError:
        return False


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def read_json(path, kind=dict):
    """Parse a JSON file the agent edits by hand; a missing file, bad JSON or the wrong top-level
    type exits 2 with the file name instead of a traceback."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        die(f"cannot read {path}: {e}")
    if not isinstance(data, kind):
        die(f"{path} must hold a JSON {'object' if kind is dict else 'array'}")
    return data


def load_project(project_dir):
    path = Path(project_dir) / "project.json"
    if not path.is_file():
        die(f"{path} not found (is this a project folder made by new_project.py?)")
    raw = read_json(path)
    data = {**PROJECT_DEFAULTS, **raw}
    # the file's own keys: the merged defaults always hold a duration
    if is_silent(raw) and "duration" not in raw:
        data["duration"] = HERO_DURATION
    missing = [k for k in ("app", "variant") if not data.get(k)]
    if missing:
        die(f"{path} has no {' / '.join(missing)}")
    # JSON numbers only: a quoted "30" or true is a mistake to report, not to coerce
    bad = [k for k in ("duration", "fps", "beats_per_bar") if not is_number(data[k])]
    if bad:
        die(f"{path}: {', '.join(bad)} must be JSON numbers, got {', '.join(repr(data[k]) for k in bad)}")
    if data["beats_per_bar"] != int(data["beats_per_bar"]):
        die(f"{path}: beats_per_bar must be a whole number, got {data['beats_per_bar']}")
    data["duration"] = float(data["duration"])
    data["beats_per_bar"] = int(data["beats_per_bar"])  # fps stays as given: 29.97 is a real rate
    if data["duration"] <= 1 or data["fps"] <= 0 or data["beats_per_bar"] <= 0:
        die(f"{path}: duration must be above 1 s (the bed fades take 0.8 s), fps and beats_per_bar above 0")
    fmt = data["format"]
    if not isinstance(fmt, str) or fmt not in FORMATS:
        die(f"{path}: format must be one of {', '.join(FORMATS)}, got {fmt!r}")
    if is_silent(fmt) and data["duration"] < SILENT_MIN_DURATION:
        die(f"{path}: a {fmt} loop needs a duration of at least {SILENT_MIN_DURATION:g} s "
            f"(it starts from rest, moves and comes back to rest), got {data['duration']:g}")
    size = dict(zip(("width", "height"), FORMATS[fmt]))
    # the file's own keys, not the merged defaults: a 4:5 file with no width/height takes 1080x1350
    wrong = {k: raw[k] for k in size if k in raw and raw[k] != size[k]}
    if wrong:
        die(f"{path}: format {fmt} is {size['width']}x{size['height']}, but the file says "
            f"{', '.join(f'{k} {v!r}' for k, v in wrong.items())}; the size comes from the format: "
            f"fix or remove width and height")
    data.update(size)
    stores = data["stores"]
    bad = [s for s in stores if s not in KNOWN_STORES] if isinstance(stores, list) else [stores]
    if bad or not stores:
        die(f"project.json stores must be a non-empty subset of {list(KNOWN_STORES)}, got {data['stores']}")
    return data


class Grid:
    def __init__(self, beats, downbeat_phase, beats_per_bar=4):
        self.beats = [float(b) for b in beats]
        self.first = int(downbeat_phase)
        self.bpb = int(beats_per_bar)

    @classmethod
    def load(cls, path, beats_per_bar=4):
        g = read_json(path)
        phase = g.get("downbeat_phase")

        def bad_phase(top):
            die(f"{path}: downbeat_phase must be a whole number from 0 to {top} (below beats_per_bar "
                f"and inside the beat list), got {phase!r}")
        # checked before Grid() converts it: int(inf) from a JSON 1e999 raises OverflowError
        if not isinstance(phase, int) or isinstance(phase, bool):
            bad_phase(int(beats_per_bar) - 1)
        if not isinstance(g.get("beats"), list):
            die(f"{path} is not a beat grid from beat_grid.py (beats must be a JSON array, got {g.get('beats')!r})")
        try:
            grid = cls(g["beats"], phase, beats_per_bar)
        except (TypeError, ValueError, OverflowError) as e:
            die(f"{path} is not a beat grid from beat_grid.py ({e!r})")
        if not 0 <= phase < min(grid.bpb, len(grid.beats)):
            bad_phase(min(grid.bpb, len(grid.beats)) - 1)
        return grid

    def _index(self, bar, beat):
        if not 0 <= int(beat) < self.bpb:
            raise ValueError(f"D({bar}, {beat}): beat must be 0-{self.bpb - 1} (beats_per_bar {self.bpb})")
        i = self.first + int(bar) * self.bpb + int(beat)
        if not 0 <= i < len(self.beats):
            raise ValueError(f"D({bar}, {beat}) is outside the beat grid ({len(self.beats)} beats, "
                             f"first downbeat at index {self.first})")
        return i

    def D(self, bar, beat=0):
        return self.beats[self._index(bar, beat)]

    def E(self, bar, beat=0):
        i = self._index(bar, beat)
        if i + 1 >= len(self.beats):
            raise ValueError(f"E({bar}, {beat}) needs the beat after it, which is outside the grid")
        return (self.beats[i] + self.beats[i + 1]) / 2


def media_duration(path):
    """Duration in seconds of an audio or video file, read with ffprobe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        die(f"ffprobe could not read {path}:\n{r.stderr[-400:]}")
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        die(f"ffprobe gives no duration for {path}")


def decode_audio(path, sr, mono=True):
    """Decode any audio/video file to float32 numpy samples with ffmpeg."""
    import numpy as np
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(sr)]
    if mono:
        cmd += ["-ac", "1"]
    cmd.append("-")
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        die(f"ffmpeg could not decode {path}:\n{r.stderr.decode(errors='replace')[-600:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def attack_index(snd, rel=0.05):
    """First sample louder than `rel` of the peak (about -26 dB): where the sound is heard."""
    import numpy as np
    peak = float(np.max(np.abs(snd))) if len(snd) else 0.0
    return int(np.argmax(np.abs(snd) > rel * peak)) if peak > 0 else 0


def attack_seconds(path, sr=48000):
    """Seconds of near-silence before a sound file's attack."""
    return attack_index(decode_audio(path, sr)) / sr


def scene_spans(html):
    """(start, duration or None) of every live <section> with a numeric data-start, sorted by start;
    a second section with the same start is dropped."""
    live = re.sub(r"<!--.*?-->", "", html, flags=re.S)

    def number(tag, name):
        m = re.search(rf"""\b{name}\s*=\s*(["'])(.*?)\1""", tag)
        try:
            v = float(m.group(2)) if m else None
        except ValueError:
            v = None
        return v if is_number(v) else None

    spans = {}
    for tag in re.findall(r"<section\b[^>]*>", live):
        start = number(tag, "data-start")
        if start is not None:
            spans.setdefault(start, number(tag, "data-duration"))
    return sorted(spans.items())


def scene_windows(spans, duration):
    """(start, lo, hi) of each scene in `spans` (scene_spans). Its clean window runs from the later
    of its start and the end of the scene before it, to the earlier of the next start and its own
    end; a window can be empty (lo >= hi)."""
    ends = [min(s + d, duration) if d is not None else duration for s, d in spans]
    windows = []
    for i, (start, _) in enumerate(spans):
        lo = max(start, ends[i - 1]) if i else start
        hi = ends[i] if i == len(spans) - 1 else min(spans[i + 1][0], ends[i])
        windows.append((start, lo, hi))
    return windows
