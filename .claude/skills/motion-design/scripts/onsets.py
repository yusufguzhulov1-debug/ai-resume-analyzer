#!/usr/bin/env python3
"""Word timings for a voice-over: Whisper word by word, then word starts snapped onto the real
sound onsets found in the audio energy.

Why: Whisper's word timestamps drift by a few hundred milliseconds, while a motion design reveals
each word 0 to 2 frames before it is spoken. The energy of the signal tells exactly when sound
starts again after a silence, so the first word of every phrase is moved onto that onset.

Energy logic: mono 16 kHz, RMS over 10 ms slices, slices louder than the threshold are "sound",
silences shorter than --min-silence (120 ms) are merged into the sound around them, sound runs
shorter than --min-sound are dropped (clicks). Each remaining run is a phrase.

Usage (from the repository root):
  python3 .claude/skills/motion-design/scripts/onsets.py <project>/assets/audio/voix-montage.wav \
      --out <project>/onsets.json [--model small] [--language fr] [--script <project>/SCRIPT.md]
  python3 .../onsets.py voice.wav --no-whisper            # phrases and silences only (to choose cut points)
  python3 .../onsets.py voice.wav --transcript onsets.json --window 14.50 17.36   # frame-local cues, no re-transcription

Output: JSON (--out) with "phrases" and "words" ({"w","s","e","whisper_s"}), and a readable listing
on stdout with the cues in the STORYBOARD format (word@seconds) and a suggested cut point in the
middle of every silence.

Requires: ffmpeg on PATH; openai-whisper (pip install -U openai-whisper) unless --no-whisper or
--transcript is used.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from array import array

SR = 16000
HOP = 160  # 10 ms at 16 kHz


def decode(path):
    """Decode any audio file to mono 16 kHz float32 samples with ffmpeg."""
    try:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
            check=True, capture_output=True).stdout
    except FileNotFoundError:
        sys.exit("onsets.py: ffmpeg not found on PATH")
    except subprocess.CalledProcessError as err:
        sys.exit(f"onsets.py: ffmpeg could not read {path}: {err.stderr.decode(errors='replace').strip()}")
    samples = array("f")
    samples.frombytes(raw[: len(raw) - len(raw) % 4])
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def rms_db(samples):
    """RMS level in dBFS of every 10 ms slice."""
    out = []
    for i in range(0, len(samples) - HOP + 1, HOP):
        chunk = samples[i:i + HOP]
        power = sum(x * x for x in chunk) / HOP
        out.append(10 * math.log10(power) if power > 1e-12 else -120.0)
    return out


def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return -120.0
    return ordered[min(len(ordered) - 1, int(q / 100 * len(ordered)))]


def sound_runs(levels, threshold, min_silence, min_sound):
    """Return merged [start, end] runs (seconds) of slices above the threshold."""
    step = HOP / SR
    runs, start = [], None
    for i, level in enumerate(levels):
        if level > threshold and start is None:
            start = i
        elif level <= threshold and start is not None:
            runs.append([start * step, i * step])
            start = None
    if start is not None:
        runs.append([start * step, len(levels) * step])
    merged = []
    for run in runs:  # fusion: a silence shorter than min_silence is not a pause
        if merged and run[0] - merged[-1][1] < min_silence:
            merged[-1][1] = run[1]
        else:
            merged.append(run)
    return [[round(a, 2), round(b, 2)] for a, b in merged if b - a >= min_sound]


def whisper_words(path, model_name, language, script_path):
    try:
        import whisper
    except ImportError:
        sys.exit("onsets.py: openai-whisper is not installed (python3 -m pip install -U openai-whisper), "
                 "or run with --no-whisper / --transcript")
    prompt = None
    if script_path:
        text = open(script_path, encoding="utf-8").read()
        prompt = re.sub(r"\[[^\]]*\]", " ", text)  # drop ElevenLabs tags such as [pause]
        prompt = re.sub(r"\s+", " ", prompt).strip() or None
    model = whisper.load_model(model_name)
    result = model.transcribe(path, language=language, word_timestamps=True, fp16=False,
                              initial_prompt=prompt, verbose=None)
    words = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            text = word["word"].strip()
            if text:
                words.append({"w": text, "s": round(float(word["start"]), 2), "e": round(float(word["end"]), 2)})
    return words


def load_transcript(path):
    data = json.load(open(path, encoding="utf-8"))
    items = data.get("words", []) if isinstance(data, dict) else data
    words = []
    for item in items:
        start = item.get("whisper_s", item.get("s", item.get("start")))
        words.append({"w": item.get("w", item.get("word", "")).strip(), "s": float(start),
                      "e": float(item.get("e", item.get("end", start)))})
    return words


def merge_elisions(words):
    """Whisper sometimes splits French elisions ("Aujourd" + "'hui", "l" + "'ordinateur"): glue them back."""
    merged = []
    for word in words:
        if merged and word["w"][:1] in "'’":
            merged[-1]["w"] += word["w"]
            merged[-1]["e"] = word["e"]
        else:
            merged.append(dict(word))
    return merged


def snap(words, phrases, tolerance):
    """Move the first word of each phrase onto the phrase's real onset.

    A word cannot start in a silence: a word whose Whisper start falls in the silence just before a
    phrase is that phrase's first word, whatever the distance. Otherwise the first word starting at
    or after the onset (within the tolerance) is taken. Words that start inside the previous sound
    run are never candidates (they belong to the previous phrase).
    """
    for word in words:
        word["whisper_s"] = word["s"]
    used = set()
    for k, (onset, _end) in enumerate(phrases):
        prev_end = phrases[k - 1][1] if k else 0.0
        free = [i for i in range(len(words)) if i not in used]
        in_silence = [i for i in free if prev_end - 0.02 <= words[i]["whisper_s"] < onset]
        after = [i for i in free if onset <= words[i]["whisper_s"] <= onset + tolerance]
        pick = in_silence or after
        if pick:
            best = min(pick, key=lambda i: words[i]["whisper_s"])
            used.add(best)
            words[best]["s"] = onset
    for i, word in enumerate(words):  # keep the timeline monotonic and every word inside its neighbours
        if i and word["s"] < words[i - 1]["s"]:
            word["s"] = words[i - 1]["s"]
        if i + 1 < len(words) and word["e"] > words[i + 1]["s"] and words[i + 1]["s"] > word["s"]:
            word["e"] = words[i + 1]["s"]
        word["e"] = max(word["e"], word["s"])
    return words


def attach(words, phrases):
    """Group word indices by phrase (the phrase that contains the word start, else the nearest)."""
    groups = [[] for _ in phrases]
    for i, word in enumerate(words):
        if not phrases:
            break
        inside = [k for k, (a, b) in enumerate(phrases) if a - 0.05 <= word["s"] <= b + 0.05]
        k = inside[0] if inside else min(range(len(phrases)),
                                         key=lambda j: min(abs(word["s"] - phrases[j][0]), abs(word["s"] - phrases[j][1])))
        groups[k].append(i)
    return groups


def cue_token(text):
    token = re.sub(r"[.,;:!?…«»\"()]+", "", text).strip()
    return token.replace(" ", "-") or text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--out", help="write the JSON result here")
    ap.add_argument("--model", default="small", help="Whisper model: base, small (default), medium, large")
    ap.add_argument("--language", default="fr")
    ap.add_argument("--script", help="text of the script, given to Whisper as a spelling hint (tags in [] are ignored)")
    ap.add_argument("--transcript", help="reuse the words of a previous onsets.json (or a [{w,s,e}] list) instead of running Whisper")
    ap.add_argument("--no-whisper", action="store_true", help="energy only: phrases, silences and cut points")
    ap.add_argument("--threshold-db", type=float, default=-40.0, help="sound threshold in dBFS (default -40; raise to -35 if breaths count as sound)")
    ap.add_argument("--min-silence", type=float, default=0.12, help="shorter silences are merged (default 0.12 s)")
    ap.add_argument("--min-sound", type=float, default=0.05, help="shorter sound runs are dropped (default 0.05 s)")
    ap.add_argument("--snap", type=float, default=0.30, help="max distance between a Whisper start and an onset to snap (default 0.30 s)")
    ap.add_argument("--window", nargs=2, type=float, metavar=("START", "END"),
                    help="only list phrases starting in [START, END) and print cues relative to START (frame-local)")
    args = ap.parse_args()

    if not os.path.exists(args.audio):
        sys.exit(f"onsets.py: {args.audio} not found")
    samples = decode(args.audio)
    duration = round(len(samples) / SR, 2)
    levels = rms_db(samples)
    phrases = sound_runs(levels, args.threshold_db, args.min_silence, args.min_sound)
    stats = {"p10_db": round(percentile(levels, 10), 1), "p50_db": round(percentile(levels, 50), 1),
             "p95_db": round(percentile(levels, 95), 1)}

    words = []
    if args.transcript:
        words = load_transcript(args.transcript)
    elif not args.no_whisper:
        words = whisper_words(args.audio, args.model, args.language, args.script)
    if words:
        words = snap(merge_elisions(words), phrases, args.snap)
    groups = attach(words, phrases)

    out_phrases = []
    for k, (a, b) in enumerate(phrases):
        nxt = phrases[k + 1][0] if k + 1 < len(phrases) else duration
        out_phrases.append({
            "start": a, "end": b, "silence_after": round(nxt - b, 2),
            "cut_point": round((b + nxt) / 2, 2) if k + 1 < len(phrases) else None,
            "text": " ".join(words[i]["w"] for i in groups[k]),
            "words": groups[k],
        })
    result = {"audio": args.audio, "duration": duration, "threshold_db": args.threshold_db,
              "min_silence": args.min_silence, "stats": stats, "phrases": out_phrases,
              "words": [{"w": w["w"], "s": round(w["s"], 2), "e": round(w["e"], 2),
                         "whisper_s": round(w.get("whisper_s", w["s"]), 2)} for w in words]}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
            fh.write("\n")

    origin = args.window[0] if args.window else 0.0
    print(f"{os.path.basename(args.audio)}  {duration:.2f} s  threshold {args.threshold_db:g} dBFS  "
          f"(p10 {stats['p10_db']}, p50 {stats['p50_db']}, p95 {stats['p95_db']})  {len(phrases)} phrases, {len(words)} words")
    if args.window:
        print(f"window {args.window[0]:.2f} to {args.window[1]:.2f}: times below are relative to {origin:.2f}")
    for k, phrase in enumerate(out_phrases):
        if args.window and not (args.window[0] <= phrase["start"] < args.window[1]):
            continue
        tail = f"silence after {phrase['silence_after']:.2f} s"
        if phrase["cut_point"] is not None and not args.window:
            tail += f", cut point {phrase['cut_point']:.2f}"
        print(f"#{k + 1:02d}  {phrase['start'] - origin:6.2f} to {phrase['end'] - origin:6.2f}   {tail}")
        if phrase["words"]:
            cues = " ".join(f"{cue_token(words[i]['w'])}@{words[i]['s'] - origin:.2f}" for i in phrase["words"])
            print(f"     {cues}")
    if args.out:
        print(f"written: {args.out}")


if __name__ == "__main__":
    main()
