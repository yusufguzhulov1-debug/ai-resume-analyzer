#!/usr/bin/env python3
"""Build several music options for one film (template of the motion-design skill).

Same voice, same picture, several soundtracks: each option is a full mix, so the user can pick the music by ear
without rendering the video again (--mux swaps the soundtrack of a rendered MP4 in a second).

Every option follows the same edit, locked on the picture:
- the music is cut to silence on the pivot (PIVOT) with a low impact, an optional riser crests exactly there;
- it comes back on the light flash (LIGHT) with its drop landing on it;
- it ducks under the voice (sidechain compressor) and breathes in the silences;
- it fades out on the end card; the mix is normalized for the web (-16 LUFS, -1.5 dBTP).

Copy into <project>/, fill the settings, then from anywhere:
  python3 <project>/build-music-options.py                 # all options -> assets/audio/mix-<id>.wav, then a check
  python3 <project>/build-music-options.py M1 M3           # some options only
  python3 <project>/build-music-options.py --mux renders/video.mp4   # also renders/video-<id>.mp4 (no re-render)
Environment: MUSIC_DIR (folder of the tracks, default <project>/assets/music), SFX_DIR (sound effects, default the
Pixabay set shipped with HeyGen's media-use skill). Find the drops with scripts/analyze-music.py (--drop-at LIGHT).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- settings -------------------------------------------------------------------------------------------------------
DUR = 45.0          # film duration (s) = TOTAL in assemble.sh
PIVOT = 14.02       # the pivot word or silence where the music stops (e.g. « Stop. »)
LIGHT = 14.30       # the light flash where the music comes back, drop on it (LEAK_AT + 0.05 in assemble.sh)
VOICE = "assets/audio/voix-montage.wav"        # voice montage from build-audio.sh
SFX_EVENTS = "assets/audio/sfx-events.json"    # [["name", seconds, gain], ...] of the film (build-audio.sh format)
OUT = "assets/audio/mix-{id}.wav"
MUSIC_DIR = os.environ.get("MUSIC_DIR", os.path.join(HERE, "assets", "music"))
SFX_DIR = os.environ.get("SFX_DIR", os.path.join(HERE, "..", ".claude", "skills", "media-use", "audio", "assets", "sfx"))

# Music segments: (file in MUSIC_DIR, track_start, film_start, film_end, gain, fade_in, fade_out).
# Pattern 1: two tracks, tension until PIVOT, then elan from LIGHT (track_start = its drop time, so the drop hits LIGHT).
# Pattern 2: one track with a drop: same file twice, the second segment starts at (first track_start + LIGHT).
OPTIONS = {
    "M1": {"name": "tension then elan", "riser": 0.18, "segments": [
        ("tension-waiting-tttt.mp3", 0.0, 0.0, PIVOT, 0.42, 0.4, 0.02),
        ("elan-dear-mr-super-computer.mp3", 5.59, LIGHT, DUR, 0.30, 0.0, 2.4),
    ]},
    "M2": {"name": "one track, drop on the light", "riser": 0.0, "segments": [
        ("complet-retro-synths.mp3", 1.62, 0.0, PIVOT, 0.34, 0.6, 0.02),
        ("complet-retro-synths.mp3", 1.62 + LIGHT, LIGHT, DUR, 0.30, 0.0, 2.4),
    ]},
}

# Sound effects of the pivot, on top of SFX_EVENTS: (name in SFX_DIR, time, gain).
PIVOT_SFX = [("impact-bass-1", PIVOT, 0.34), ("sparkle", LIGHT - 0.04, 0.18), ("whoosh", LIGHT - 0.04, 0.22)]
RISER = "riser"            # media-use riser: a 10 s build that crests at its very end
RISER_LEN = 3.2            # seconds of riser kept before the pivot
DUCK = "threshold=0.035:ratio=5:attack=25:release=420:makeup=1"   # music under the voice
LOUDNESS = "I=-16:TP=-1.5:LRA=11"                                   # web delivery
LIMIT = 0.79                 # final limiter ceiling (linear, -2 dBFS) so the true peak stays under -1.5 dBTP
# ---------------------------------------------------------------------------------------------------------------------


def path(rel):
    return rel if os.path.isabs(rel) else os.path.join(HERE, rel)


def sfx_file(name):
    for ext in (".wav", ".mp3"):
        f = os.path.join(SFX_DIR, name + ext)
        if os.path.exists(f):
            return f
    sys.exit(f"build-music-options: sound effect '{name}' not found in {SFX_DIR} (.wav or .mp3)")


def duration(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def build(oid):
    opt = OPTIONS[oid]
    inputs = ["-i", path(VOICE)]
    fc = ["[0]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[v][vsc]"]
    idx, bus = 1, []
    for i, (f, ts, fs, fe, g, fi, fo) in enumerate(opt["segments"]):
        src = os.path.join(MUSIC_DIR, f)
        if not os.path.exists(src):
            sys.exit(f"build-music-options: {src} not found (set MUSIC_DIR)")
        inputs += ["-i", src]
        d = fe - fs
        chain = f"[{idx}]atrim=start={ts:.3f}:duration={d:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=stereo"
        if fi > 0:
            chain += f",afade=t=in:d={fi}"
        ms = int(round(fs * 1000))
        chain += f",afade=t=out:st={max(d - fo, 0):.3f}:d={fo},volume={g},adelay={ms}|{ms},apad=whole_dur={DUR}[m{i}]"
        fc.append(chain)
        bus.append(f"[m{i}]")
        idx += 1
    if opt.get("riser", 0) > 0:
        riser = sfx_file(RISER)
        inputs += ["-i", riser]
        ms = int(round((PIVOT - RISER_LEN) * 1000))
        fc.append(f"[{idx}]atrim=start={duration(riser) - RISER_LEN:.3f},asetpts=PTS-STARTPTS,"
                  f"aformat=sample_rates=44100:channel_layouts=stereo,afade=t=in:d=1.2,"
                  f"afade=t=out:st={RISER_LEN - 0.03:.3f}:d=0.03,volume={opt['riser']},adelay={ms}|{ms},apad=whole_dur={DUR}[mr]")
        bus.append("[mr]")
        idx += 1
    fc.append("".join(bus) + f"amix=inputs={len(bus)}:normalize=0:duration=longest,asplit=2[mbus][mraw]")
    fc.append(f"[mbus][vsc]sidechaincompress={DUCK}[mduck]")
    fc.append("[mduck]asplit=2[mmix][mcheck]")
    labels = ["[v]", "[mmix]"]
    events = json.load(open(path(SFX_EVENTS), encoding="utf-8")) if os.path.exists(path(SFX_EVENTS)) else []
    for j, (name, t, g) in enumerate(list(events) + PIVOT_SFX):
        inputs += ["-i", sfx_file(name)]
        ms = int(round(float(t) * 1000))
        fc.append(f"[{idx}]aformat=sample_rates=44100:channel_layouts=stereo,volume={g},adelay={ms}|{ms}[e{j}]")
        labels.append(f"[e{j}]")
        idx += 1
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,atrim=0:{DUR},"
              f"loudnorm={LOUDNESS},alimiter=limit={LIMIT}:level=disabled[out]")
    out = path(OUT.format(id=oid))
    music_only = out.replace(".wav", ".music-only.wav")   # music after ducking (pivot check)
    music_raw = out.replace(".wav", ".music-raw.wav")     # music before ducking (tension against elan)
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc),
           "-map", "[out]", "-ar", "44100", "-t", str(DUR), out, "-map", "[mcheck]", "-t", str(DUR), music_only,
           "-map", "[mraw]", "-t", str(DUR), music_raw]
    subprocess.run(cmd, check=True)
    print(f"{oid} ({opt['name']}) -> {out}")
    check(out, music_only, music_raw)
    os.remove(music_only)
    os.remove(music_raw)
    return out


def level(f, start, end, lowpass=None):
    """Mean level (dBFS) of a window, optionally under a low-pass (energy under 150 Hz shows the bass and kicks)."""
    af = f"atrim={max(start, 0):.3f}:{end:.3f}" + (f",lowpass=f={lowpass}:p=2,lowpass=f={lowpass}:p=2" if lowpass else "") + ",volumedetect"
    err = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", f, "-af", af, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[0-9.]+|-inf) dB", err)
    return float(m.group(1)) if m and m.group(1) != "-inf" else -120.0


def loudness(f, start, end):
    """Integrated loudness (LUFS) of a window."""
    err = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", f, "-af",
                          f"atrim={max(start, 0):.3f}:{end:.3f},ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    found = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
    return float(found[-1]) if found else -70.0


def check(mix, music_only, music_raw):
    """The pivot must be heard: bass gone between PIVOT and LIGHT (except the impact), back after the flash, and the
    music well under the voice just before the pivot. The tension must not sit far under the elan: taken from a sparse
    intro, 10 dB under, it made the start of a film feel soft; keep it 2 to 3 dB under at most."""
    before = level(mix, PIVOT - 1.0, PIVOT - 0.05, 150)
    gap = level(music_only, PIVOT + 0.05, LIGHT - 0.02, 150)
    after = level(mix, LIGHT + 0.1, LIGHT + 1.1, 150)
    voice = level(path(VOICE), PIVOT - 1.5, PIVOT)
    music = level(music_only, PIVOT - 1.5, PIVOT)
    print(f"   under 150 Hz: before the pivot {before:.1f} dB | music alone, pivot to flash {gap:.1f} dB | after the flash {after:.1f} dB")
    print(f"   1.5 s before the pivot: voice {voice:.1f} dB, music {music:.1f} dB (margin {voice - music:+.1f} dB)")
    tension = loudness(music_raw, 0.0, PIVOT - RISER_LEN)
    elan = loudness(music_raw, LIGHT, DUR - 3.0)
    print(f"   music before ducking: tension {tension:.1f} LUFS, elan {elan:.1f} LUFS "
          f"(tension {tension - elan:+.1f} dB, aim -3 to -2 dB)")
    if gap > -60:
        print("   warning: the music is not silent between the pivot and the flash")
    if voice - music < 8:
        print("   warning: less than 8 dB between the voice and the music before the pivot: lower that segment's gain")


def mux(video, mixes):
    base, _ = os.path.splitext(path(video))
    for oid, wav in mixes:
        out = f"{base}-{oid}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path(video), "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
        print(f"{oid} -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    video = None
    if "--mux" in args:
        k = args.index("--mux")
        video = args[k + 1] if k + 1 < len(args) else sys.exit("--mux needs a video path")
        del args[k:k + 2]
    unknown = [a for a in args if a not in OPTIONS]
    if unknown:
        sys.exit(f"build-music-options: unknown option(s) {', '.join(unknown)} (known: {', '.join(OPTIONS)})")
    built = [(oid, build(oid)) for oid in (args or list(OPTIONS))]
    if video:
        mux(video, built)
