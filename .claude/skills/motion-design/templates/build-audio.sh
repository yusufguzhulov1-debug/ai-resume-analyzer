#!/bin/bash
# Voice montage + final mix of one motion design project (template of the motion-design skill).
# Copy it into <project>/, fill the settings below, run: bash <project>/build-audio.sh
#
# 1. Voice montage: the raw ElevenLabs voice is cut at CUTS (each cut sits in the MIDDLE of a silence of the raw voice,
#    never on a word onset: take the "cut point" printed by onsets.py --no-whisper), a silence is inserted at each cut,
#    5 ms fades on every join, then TAIL seconds of silence for the end card, trimmed to TOTAL.
#    Every cue after a cut moves by the silence inserted before it: re-run onsets.py on the montage to get final cues.
# 2. Mix: montage + CC0 music (faded, low) + sound effects placed at the times listed in SFX_EVENTS, limiter at 0.95.
#    The mix is mounted at the root of index.html by assemble.sh (AUDIO setting there).
set -euo pipefail
cd "$(dirname "$0")"

# ---- settings (all paths relative to this project folder) ----------------------------------------------------------
RAW="${RAW:-assets/audio/voix.mp3}"                # raw voice exported from ElevenLabs
CUTS="${CUTS:-}"                                   # "cut:silence" pairs in raw seconds, e.g. "14.00:0.8 34.75:0.4" (empty = no cut)
TAIL="${TAIL:-4.0}"                                # silence added after the voice (end card hold)
TOTAL="${TOTAL:-45.0}"                             # final duration in seconds = STORYBOARD duration = TOTAL in assemble.sh
MUSIC="${MUSIC-assets/audio/music.mp3}"            # CC0 track (set MUSIC="" for no music)
MUSIC_START="${MUSIC_START:-0}"                    # where to start in the track (skip a quiet intro, see pitfalls.md)
MUSIC_VOLUME="${MUSIC_VOLUME:-0.12}"               # 0.10 to 0.15 under a voice
SFX_DIR="${SFX_DIR:-../.claude/skills/media-use/audio/assets/sfx}"   # Pixabay SFX shipped with HeyGen's media-use
SFX_EVENTS="${SFX_EVENTS:-assets/audio/sfx-events.json}"             # [["name", seconds, volume], ...] on the FINAL timeline
VOICE_OUT="${VOICE_OUT:-assets/audio/voix-montage.wav}"
MIX_OUT="${MIX_OUT:-assets/audio/mix.wav}"
# ---------------------------------------------------------------------------------------------------------------------

command -v ffmpeg >/dev/null || { echo "build-audio: ffmpeg not found on PATH" >&2; exit 1; }
[ -f "$RAW" ] || { echo "build-audio: raw voice $RAW not found" >&2; exit 1; }
export RAW CUTS TAIL TOTAL MUSIC MUSIC_START MUSIC_VOLUME SFX_DIR SFX_EVENTS VOICE_OUT MIX_OUT

python3 - <<'EOF'
import json, os, subprocess, sys

env = os.environ
raw, total, tail = env["RAW"], float(env["TOTAL"]), float(env["TAIL"])
fade = 0.005

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
                         check=True, capture_output=True, text=True).stdout.strip()
    return float(out)

# ---- 1. voice montage ----
raw_len = duration(raw)
cuts = []
for pair in env["CUTS"].split():
    at, gap = pair.split(":")
    cuts.append((float(at), float(gap)))
cuts.sort()
bounds = [0.0] + [c for c, _ in cuts] + [raw_len]
parts, labels = [], []
for k in range(len(bounds) - 1):
    a, b = bounds[k], bounds[k + 1]
    chain = f"[0]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS"
    if k > 0:
        chain += f",afade=t=in:d={fade}"
    last = k == len(bounds) - 2
    out_fade = 0.03 if last else fade
    chain += f",afade=t=out:st={max(0.0, b - a - out_fade):.3f}:d={out_fade}[v{k}]"
    parts.append(chain)
    labels.append(f"[v{k}]")
    gap = cuts[k][1] if k < len(cuts) else tail
    if gap > 0:
        parts.append(f"anullsrc=r=44100:cl=mono,atrim=0:{gap:.3f}[g{k}]")
        labels.append(f"[g{k}]")
graph = ";".join(parts) + ";" + "".join(labels) + \
    f"concat=n={len(labels)}:v=0:a=1,aresample=44100,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-filter_complex", graph, "-map", "[out]",
                "-ar", "44100", "-ac", "1", env["VOICE_OUT"]], check=True)
voice_len = sum(b - a for a, b in zip(bounds, bounds[1:])) + sum(g for _, g in cuts) + tail
print(f"voice montage: {env['VOICE_OUT']} (raw {raw_len:.2f} s, {len(cuts)} cut(s), voice + silences {voice_len:.2f} s, trimmed or padded to {total:.2f} s)")
if voice_len > total + 0.01:
    print(f"warning: the voice montage ({voice_len:.2f} s) is longer than TOTAL ({total:.2f} s): the end is cut", file=sys.stderr)

# ---- 2. mix ----
events = []
if os.path.exists(env["SFX_EVENTS"]):
    events = json.load(open(env["SFX_EVENTS"], encoding="utf-8"))
def sfx_file(name):
    for ext in (".wav", ".mp3"):
        path = os.path.join(env["SFX_DIR"], name + ext)
        if os.path.exists(path):
            return path
    sys.exit(f"build-audio: sound effect '{name}' not found in {env['SFX_DIR']} (.wav or .mp3)")

args = ["ffmpeg", "-v", "error", "-y", "-i", env["VOICE_OUT"]]
graph = ["[0]aformat=sample_rates=44100:channel_layouts=stereo[v]"]
labels = ["[v]"]
index = 1
music = env["MUSIC"]
if music:
    if not os.path.exists(music):
        sys.exit(f"build-audio: music {music} not found (set MUSIC= to mix without music)")
    start = float(env["MUSIC_START"])
    args += ["-i", music]
    graph.append(f"[{index}]atrim={start:.3f}:{start + total:.3f},asetpts=PTS-STARTPTS,"
                 f"aformat=sample_rates=44100:channel_layouts=stereo,afade=t=in:d=0.8,"
                 f"afade=t=out:st={max(0.0, total - 3):.3f}:d=3,volume={float(env['MUSIC_VOLUME'])}[m]")
    labels.append("[m]")
    index += 1
for k, (name, at, volume) in enumerate(events):
    args += ["-i", sfx_file(name)]
    delay = int(round(float(at) * 1000))
    graph.append(f"[{index}]aformat=sample_rates=44100:channel_layouts=stereo,volume={float(volume)},adelay={delay}|{delay}[e{k}]")
    labels.append(f"[e{k}]")
    index += 1
graph.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.95[out]")
subprocess.run(args + ["-filter_complex", ";".join(graph), "-map", "[out]", "-t", f"{total:.3f}", env["MIX_OUT"]], check=True)
print(f"mix: {env['MIX_OUT']} ({total:.2f} s, music {'on' if music else 'off'}, {len(events)} sound effect(s))")
EOF
