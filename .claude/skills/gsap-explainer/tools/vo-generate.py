#!/usr/bin/env python3
"""Generate per-scene ElevenLabs voiceover clips for an explainer + report fit vs SCENES.

Usage:
  python3 vo-generate.py <script.md> <outdir> <voiceId>

Reads `- VO: "..."` lines (one per scene, in order) from the script markdown, synthesizes
each with the given ElevenLabs voice, writes s<i>.mp3 to <outdir>, and prints each clip's
duration against the SCENES array found in the sibling .html (same basename minus -script).

API key: taken from the ELEVENLABS_API_KEY environment variable, or from an
`ELEVENLABS_API_KEY=...` line in ./.env . Never hardcode a key.

Rules learned in production:
- A cloned voice reads ~2.6 words/sec; WRITE scripts at ~2.5 words/sec x scene duration.
- A clip must fit SCENES[i] - 0.6s. On overrun, EXTEND the scene (clip + 1.5-2s) rather
  than trimming beats: extending never strands choreography, only trims do.
- Every added phrase should narrate an on-screen beat (count the reveals as items land),
  never pad for time.
"""
import re, sys, json, subprocess, urllib.request, os

if len(sys.argv) < 4:
    sys.exit('usage: vo-generate.py <script.md> <outdir> <voiceId>')
md_path, outdir, voice = sys.argv[1], sys.argv[2], sys.argv[3]

key = os.environ.get('ELEVENLABS_API_KEY')
if not key and os.path.exists('.env'):
    for line in open('.env'):
        if line.startswith('ELEVENLABS_API_KEY='):
            key = line.split('=', 1)[1].strip()
            break
assert key, 'set ELEVENLABS_API_KEY in the environment or in ./.env'

lines = re.findall(r'^\- VO: "(.*?)"$', open(md_path).read(), re.M)
assert lines, 'no `- VO: "..."` lines found in ' + md_path

html = md_path.replace('-script.md', '.html')
scenes = None
if os.path.exists(html):
    m = re.search(r'var SCENES=\[([^\]]+)\]', open(html).read())
    if m:
        scenes = [int(x) for x in re.findall(r'\d+', m.group(1)) if int(x) < 900]

os.makedirs(outdir, exist_ok=True)
overs = []
for i, text in enumerate(lines):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}).encode()
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_64',
        data=body, headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    audio = urllib.request.urlopen(req, timeout=120).read()
    p = f'{outdir}/s{i}.mp3'
    open(p, 'wb').write(audio)
    d = float(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                              '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip())
    if scenes and i < len(scenes):
        pct = round(d / scenes[i] * 100)
        tag = 'OK' if d <= scenes[i] - 0.6 else 'OVER -> extend scene to %d' % (int(d) + 2)
        if 'OVER' in tag:
            overs.append(i)
        print(f'S{i}: {d:.1f}s / {scenes[i]}s = {pct}%  {tag}')
    else:
        print(f'S{i}: {d:.1f}s ({len(audio)//1024}KB)')
print('OVERRUNS:', overs or 'none')
