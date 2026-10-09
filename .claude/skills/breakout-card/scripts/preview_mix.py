#!/usr/bin/env python3
"""Quick review mix: dialogue + event-matched SFX from a cue sheet. Your editor timeline stays the deliverable;
this is for judging a cut before (or without) assembly.

    preview_mix.py <cues.json> <dialogue.wav> <out.wav>

cues.json: {"fps": 30, "sources": {"pop": "<path>", ...}, "cues": [{"frame": 46, "cue": "pop", "gainDb": -13, "purpose": "..."}, ...]}
Relative source paths resolve against the cue sheet's folder, then its parent (the run root when the sheet sits in analysis/).
"""
import json, subprocess, sys
from pathlib import Path

sheet, dialogue, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
cfg = json.loads(sheet.read_text())
src = {k: Path(v) if Path(v).is_absolute() else next(p for p in (sheet.parent / v, sheet.parent.parent / v) if p.exists())
       for k, v in cfg['sources'].items()}
args, chains = ['ffmpeg', '-v', 'error', '-y', '-i', dialogue], []
for k, c in enumerate(cfg['cues']):
    args += ['-i', src[c['cue']]]
    ms = round(c['frame'] / cfg['fps'] * 1000)
    chains.append(f'[{k + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={c["gainDb"]}dB,adelay={ms}|{ms}[s{k}]')
n = len(cfg['cues'])
graph = ';'.join(chains) + f';{"".join(f"[s{k}]" for k in range(n))}amix=inputs={n}:normalize=0:duration=longest[fx];[0:a][fx]amix=inputs=2:normalize=0:duration=first[out]'
subprocess.run(args + ['-filter_complex', graph, '-map', '[out]', '-c:a', 'pcm_s16le', out], check=True)
loud = subprocess.run(['ffmpeg', '-v', 'info', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
print(out, n, 'cues |', ' '.join(l.strip() for l in loud.split('Summary:')[-1].splitlines() if l.strip().startswith(('I:', 'Peak:'))))
