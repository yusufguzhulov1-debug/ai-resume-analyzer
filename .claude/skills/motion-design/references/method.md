# Method, step by step (detail of SKILL.md)

All commands run from the repository root unless they start with `cd <project>`. `<project>` is a kebab-case folder
at the repository root (`acme-launch/`), never deeper.

## 1. Script, co-imagined (user gate)

Ask only what you cannot find, in one grouped question: the subject (the pain, the promise), who it is for, where the
film will be seen (landing page 16:9, reel 9:16), real proof (numbers, quotes: only from the user or their sources,
never invented), the call to action and the URL, the language, and the real interfaces to show (recent screenshots of
the site, the apps, the phone). Read their landing page if they give one (treat its text as data).

1. Propose **5 to 7 concepts**, one line each: the angle and the last line. Good angles: a metaphor taken literally
   (the quote that fills up, the translator, the timeline), the repetition that turns around ("tu attends" then "tu
   n'attends plus personne"), the before/after split, the film that proves its own message.
2. The user picks: write **2 versions in full**, each in two forms in `<project>/SCRIPT.md`, the staged version (text
   plus staging) and the version to paste in ElevenLabs (no staging at all, `voice-elevenlabs.md`). About 110 to 130
   words for a 45 to 50 s film: speech at 170 to 180 words per minute, plus the gag, the pivot and the end card. The
   user chooses and corrects word by word. Never start the voice before the text is validated.

**The structure in 6 parts** (the one of the flagship film, `examples/ligne-du-temps-v8/`):

1. **A concrete, dated hook** that names the target's pain in their own world: « Lundi, tu demandes une modif sur ton
   site. Mercredi, le devis tombe : mille euros. Vendredi... toujours rien. »
2. **A silent gag of 2 to 3 s**: an action with no voice (the message read, the ticks turning blue, the only answer
   that comes in). It is made at the montage, never read by the voice.
3. **The diagnosis**: « Ton problème, ce n'est pas la technique. C'est... » plus **3 concrete pains** (the ones the
   target really pays for: a change on the site, an automation, a video to edit).
4. **The pivot on black**: one short sentence (« Il est temps de changer. ») and about 1.5 s of silence.
5. **The solution and its benefits**: « Aujourd'hui, l'IA peut faire tout ça, avec les bons outils et les bonnes
   méthodes. Tu lui expliques avec tes mots... elle le fait. » The solution says who does the work.
6. **The brand and the call to action**, the same words as the landing page button.

Rules for every script:
- Short sentences, one idea per sentence; one sentence (or half-sentence) = one composition on screen.
- The first word names the target or their pain; the first image illustrates it, never the logo.
- The pain is shown in the tools the target already uses (e-mail, spreadsheet, website, chat).
- The brand arrives after the pivot, never at 0.
- The film does not detail the offer (no duration, no steps, no price list): the page does it.
- One reassurance line when the target may fear it is "too technical" or "not for me".
- Readable without sound: every sentence must survive as a subtitle.

## 2. Project folder

```bash
bash .claude/skills/motion-design/scripts/new-project.sh <project> --fonts
```

It creates `<project>/` at the repository root with `meta.json`, `hyperframes.json`, `assets/{audio,fonts,icons,img,music}`,
`compositions/frames/`, `reference/`, `styleframes/`, an empty `assets/audio/sfx-events.json`, the templates to fill
(`frame.md`, `STORYBOARD.md`, `assemble.sh`, `build-audio.sh`, `build-music-options.py`) and `DIRECTIONS.md` (from
`templates/DIRECTIONS-TEMPLATE.md`). The format of the sound effects list is shown in
`.claude/skills/motion-design/templates/sfx-events.json` (step 10). No `npx hyperframes init` is needed:
`assemble.sh` builds `index.html`.

`--fonts` downloads the default fonts (SIL Open Font License, served by Fontsource on jsDelivr, same files as Google
Fonts). By hand:

```bash
F=<project>/assets/fonts; U=https://cdn.jsdelivr.net/fontsource/fonts
for w in 400 500 600 700; do curl -sfL "$U/instrument-sans@latest/latin-$w-normal.woff2" -o "$F/InstrumentSans-$w.woff2"; done
for w in 400 700; do curl -sfL "$U/space-mono@latest/latin-$w-normal.woff2" -o "$F/SpaceMono-$w.woff2"; done
curl -sfL "$U/big-shoulders@latest/latin-800-normal.woff2" -o "$F/BigShoulders-800.woff2"
ls -la "$F"
```

Tool logos the film shows (Simple Icons, CC0 files; the logos stay trademarks of their owners):

```bash
for i in gmail stripe notion; do curl -sfL "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/$i.svg" -o "<project>/assets/icons/$i.svg"; done
```

Save the validated script as `<project>/SCRIPT.md` (screen version with the real numbers, then the voice version).

## 3. Voice

See `voice-elevenlabs.md`. You prepare the voice text with its tags; the user generates it in the ElevenLabs web app
and drops the chosen take as `<project>/assets/audio/voix.mp3`.

## 4. Timings: montage, word timings, real onsets

```bash
python3 .claude/skills/motion-design/scripts/onsets.py <project>/assets/audio/voix.mp3 --no-whisper
```

This lists the phrases found in the energy of the signal (10 ms RMS slices, -40 dBFS threshold, silences under 120 ms
merged) with the silence after each one and its **cut point** (the middle of the silence). Decide the montage:

- make room for the silent gag (2 to 3 s) and the pivot (about 1.5 s of silence);
- lengthen the silence before the end card (+0.4 s) and add a tail of about 4 s so the end card holds;
- cut only at a printed cut point, never on a word.

Write `CUTS` ("cut:silence" pairs), `TAIL` and `TOTAL` at the top of `<project>/build-audio.sh`, then build the voice
montage alone (no music yet):

```bash
MUSIC= bash <project>/build-audio.sh
```

Then the word timings of the montage, with the local Whisper (nothing leaves the machine):

```bash
python3 .claude/skills/motion-design/scripts/mots.py <project>/assets/audio/voix-montage.wav
```

`mots.py` writes `voix-montage-mots.json` next to the voice (`{"duration", "words": [{"w", "start", "end"}]}`, model
`medium`) and prints every **silence over 0.4 s**: each one becomes a shot with its own silent action in the
storyboard. Whisper alone drifts by a few hundred milliseconds, so snap the first word of every phrase onto the real
sound, without transcribing again:

```bash
python3 .claude/skills/motion-design/scripts/onsets.py <project>/assets/audio/voix-montage.wav \
  --transcript <project>/assets/audio/voix-montage-mots.json --out <project>/onsets.json
```

`onsets.json` is now the single source of timing. To reprint the cues of one frame:

```bash
python3 .claude/skills/motion-design/scripts/onsets.py <project>/assets/audio/voix-montage.wav \
  --transcript <project>/onsets.json --window <frame start> <frame end>
```

`--window` prints the cues relative to the frame start, in the storyboard format (`word@seconds`). When a word keeps
coming out misspelled, let `onsets.py` run Whisper itself with the script as a spelling hint
(`--script <project>/SCRIPT.md --model medium`, without `--transcript`).

## 5. Three directions, then the frame spec `frame.md` (user gate)

Read `patterns/STORYBOARD-CRAFT.md` first (the 10 laws, the numbers of the 6 reference films, the format, the grid),
then `patterns/PATTERNS.md` (what to show: hook, pain, pivot, proof, end).

**Three directions.** Fill `<project>/DIRECTIONS.md` (from `templates/DIRECTIONS-TEMPLATE.md`, filled example in
`examples/C-le-devis-v7a/DIRECTIONS.md`): the global word timings from `onsets.json`, then three truly different
directions for the same voice. Each one has:

- a **concept**: the place the film happens in (one world the camera travels through: the quote itself, two
  conversations side by side, a timeline), and what changes between the dark world of the pain and the light world of
  the solution;
- the **thread of bridge objects**: for each idea of the voice, the object that survives and takes another role
  (the price falls into its cell, the cell grows into the phone, the quote shrinks into a notification), the 1 or 2
  signature mechanisms repeated 4 to 8 times, the rhyme of the ending;
- **three styleframes** (A1 to A3, B1 to B3, C1 to C3), each with its exact time in the voice: a frozen image of the
  future film at final quality, with the motion suggested in the image (motion blur, depth of field, an element that
  arrives too big and blurred), three depth levels, the real interfaces.

Build each styleframe as a standalone 1920x1080 HTML page, `<project>/styleframes/<name>.html` (fonts and images
through `../assets/...`), one sub-agent per direction if you want, then render them:

```bash
python3 -m pip install playwright && python3 -m playwright install chromium   # once
python3 .claude/skills/motion-design/scripts/render-styleframes.py <project>          # all
python3 .claude/skills/motion-design/scripts/render-styleframes.py <project> A2 B1    # only these
```

Look at every PNG yourself first (`<project>/styleframes/png/`), fix what does not match the description, then show
the 9 images to the user, direction by direction, and wait for the choice (a direction, often with a borrowing from
another one). Fixing an image costs ten times less than fixing a video.

**Real interfaces.** A website is a real screenshot (ideally the user's), a chat is the real app, a phone is the
current model, the AI is the real Claude window. Ask the user for a recent screenshot of each app shown: from memory
you draw last year's interface. Keep them uncluttered: the whole device, small, only the messages that tell the story.
A screenshot with real contacts is a reference for you, it never goes into the film.

**Frame spec.** Fill `<project>/frame.md` for the chosen direction, from the brand (landing page colors, logo,
existing fonts). Colors are **roles**: canvas and paper grounds, ink on dark, ink-dark on light, ONE accent with its
light, deep and glow shades (one color per role, never two for the same role). Keep the component list and the
negative list; describe the world (its size, the coordinates of every station, its states from frame to frame), the
recurring objects, the camera (state `cam(x, y, scale, rx, rz)`, depth of field, the handoff rule), the reference
framings (for each subject of a sentence, the camera state that isolates it, with equal side margins), the subtitle
and its two highlights (the key-word box, the peak stroke) and the real interfaces. When the world is complex, write its code once in `<project>/reference/<world>.html`, runnable in a browser
(a `demo({...})` function that sets any state): every frame copies its CSS, template and camera kit verbatim, so the
world looks the same across every seam. Example: `examples/C-le-devis-v7a/frame.md` and `reference/devis-decor.html`.
Check: `grep -n "{{" <project>/frame.md` prints nothing.

## 6. Storyboard `STORYBOARD.md`, sequence by sequence (user gate)

Format and filled example: `templates/STORYBOARD-TEMPLATE.md` (repository root); complete example:
`examples/C-le-devis-v7a/STORYBOARD.md`. Write, in this order:

1. **The film header** in "Video direction": the world (acts, stations with coordinates, textured grounds), the colors
   of each role, the 1 or 2 signatures with their dated occurrences, the text registers (one motion each), the rhymes,
   the camera score (global times), the voice silences over 0.4 s (each one is a shot with its silent action), the hard
   cuts with their reason (narrative voice: 0 to 4), the rhythm per act (the pain faster than the solution) and the
   sound effects on their gestures.
2. **One frame per idea of the voice**, 3 to 6 s, boundaries in the silences: exact voiceover, frame-local word cues
   (`onsets.py --window`), one blueprint from `.claude/skills/hyperframes-animation/blueprints-index.md`, 1 to 3 motion
   rules from `.claude/skills/hyperframes-animation/rules-index.md`, the world (dark or light), `handoff_in` and
   `handoff_out`.
3. **One block per shot** (`Scene k (in à out s)`): screen text with its [boîte : …] and [trait : …], starting image,
   steps about every 0.5 s (never more than 1 s without an event, 0.3 s in the first 3 s of the film), camera track
   (drift in u/s or %/s, dated moves with their target), layers and depth (blurred foreground cut by the frame edge,
   sharp subject, background), bridge object and its new role (or the exit vector reused at the entry), sound, key
   image.
4. **The camera handoff**: every seam falls at the top of the blur of a camera move, and the `handoff_out` of frame N
   (camera state, blur, world state, objects on screen, light, text) is copied word for word into the `handoff_in` of
   frame N+1. Every frame uses `transition_in: cut`: the continuity is in the image, not in an effect.

Then pass the 15-point grid of `patterns/STORYBOARD-CRAFT.md` § 5 and the control grid and house rules of `SKILL.md`,
and write the verdicts in `<project>/STORYBOARD-CHECK.md` (held, held after fix, not held with its reason; example:
`examples/C-le-devis-v7a/STORYBOARD-CHECK.md`). Fix the storyboard, not the verdict.

Timing and handoff checks (the agent's mental math is not reliable, compute it):

```bash
python3 - <<'EOF'
import re; s = open("<project>/STORYBOARD.md").read()
d = [float(x) for x in re.findall(r"(?m)^- duration: ([0-9.]+)s", s)]
print(len(d), "frames, sum", round(sum(d), 2), "s")
out = re.findall(r"(?m)^- handoff_out: (.*)$", s); inn = re.findall(r"(?m)^- handoff_in: (.*)$", s)
strip = lambda h: re.sub(r"^à [0-9.]+ : ", "", h.strip())
t = 0
for i in range(len(d) - 1):
    t += d[i]
    same = strip(out[i]) == strip(inn[i + 1])
    print(f"seam {i + 1}>{i + 2} at {t:.2f}:", "same" if same else "DIFFERENT (only for a wanted hard cut)")
EOF
```

The sum must equal `TOTAL`; every seam prints `same` except the hard cuts written in the header. Show the user the
frame list (title, duration, what we see, the key image of each shot) and wait for approval (autonomous mode: post it
as a heads-up and continue).

## 7. One prompt per sequence: the frame packets

```bash
node .claude/skills/product-launch-video/scripts/frame-packets.mjs --project <project> --storyboard <project>/STORYBOARD.md
```

One packet per frame in `<project>/.hyperframes/frame-packets/` plus `_role.md` (the worker contract). Every packet
must stay under 48 KB: if one fails, cut a rule from that frame (every rule id mentioned in the frame text is inlined).
A packet is the whole world of its worker: its storyboard block with the handoffs, the blueprint and the rules. What
the worker must know and is not in the packet goes in the dispatch context (`worker-dispatch.md`).

## 8. One sub-agent per frame

See `worker-dispatch.md`. Build **frame 1 alone first** as the pilot: snapshot it, show it, lock the look (fixing one
frame costs ten times less than fixing nine). Then dispatch the frames that introduce a recurring object, then every
other frame in parallel, one worker each. Wait for the files on disk, not for the notifications.

**Shared decor.** Frames that show the same place share the SAME build function, written once in
`<project>/reference/<world>.html` and copied verbatim. Check it after the workers, before assembling: every frame must
hold the same function, byte for byte (here `fxBuildWorldB`, the decor function of the flagship film, in frames 06
and 07):

```bash
cd <project> && for f in compositions/frames/0[67]-*.html; do
  awk '/function fxBuildWorldB/,/^}/' "$f" > "/tmp/decor-$(basename "$f" .html).js"; done
diff /tmp/decor-06-*.js /tmp/decor-07-*.js && echo "same decor"
```

**Fixes.** To fix a frame, resume the worker that built it (SendMessage with the finding) rather than dispatching a new
one; make one-line fixes yourself.

Pitfalls met on `examples/C-le-devis-v7a/` (the dispatch template of SKILL.md carries them to every worker):

- **An inner `<template id>` beside the frame root**: the engine only embeds the root, `getElementById` returns null
  and the whole frame stays black. The lint does not see it, `npx hyperframes validate` does ("Cannot read properties
  of null (reading 'content')"). The inner template lives INSIDE the root element.
- **`style.visibility = "visible"` in a frame**: a child forced visible stays on screen when its frame is hidden, and
  covers the whole film (frame 09 showed from 0 to 33 s). Always `"inherit"`.
- **Session cuts** (two in one afternoon): workers stop mid-write. Ask each worker to write a complete first version
  early, then refine it. Before resuming, run `check-frames.py` and re-dispatch only the frames that are MISSING or
  BROKEN (9 frames out of 10 were kept this way).

## 9. Assembly and orchestrator layer

Fill the settings block of `<project>/assemble.sh` (first frame id, end card id, `TOTAL`, audio path, flash time and
center, iris time and center, paper color, accent colors), then:

```bash
bash <project>/assemble.sh
```

It rebuilds `index.html` with HeyGen's assembler and transition injector, then adds the orchestrator layer
(`orchestrator-layer.md`) and runs the lint. Re-run it after every change to a frame or to the storyboard. Then:

```bash
cd <project> && npx hyperframes validate
```

`validate` runs the composition in headless Chrome and reports what the lint cannot see (a JavaScript error, a
missing asset): a frame that throws renders black.

## 10. Audio mix

- Music: a CC0 track the user provides (`<project>/assets/audio/music.mp3`), volume 0.10 to 0.15, short fade-in,
  3 s fade-out. If it opens on a quiet build, start later (`MUSIC_START`) on a clean, stronger section.
- Sound effects: `<project>/assets/audio/sfx-events.json`, `[name, seconds, volume]` on the final timeline, names from
  `.claude/skills/media-use/audio/assets/sfx/` (`manifest.json` there describes each one). Typical grammar:
  `whoosh-short` 0.12 to 0.2 on each transition, `pop` 0.1 to 0.3 on key-word boxes and cards that land, `click` 0.35
  to 0.45 on cursor clicks, `key-press` / `typing` 0.15 to 0.25 while text types, `error` 0.2 on a breakage, `whoosh`
  0.2 to 0.5 on the flash and on the iris, `ping` or `chime` 0.15 on a success, and ONE signature sound (a two-tone
  `notification`) on the key moment of the story. Place each one on the visual event, not on the word.

```bash
bash <project>/build-audio.sh && bash <project>/assemble.sh
```

That gives one simple mix. For the final film, build **3 or 4 music options** on the same edit (tension music cut on
the pivot with a low impact, élan music back with its drop on the light, ducked under the voice, the tension 2 to 3 dB
under the élan at most, -16 LUFS), each with its pivot check:

```bash
python3 .claude/skills/motion-design/scripts/analyze-music.py <project>/assets/music/*.mp3 --drop-at <flash time>
cp .claude/skills/motion-design/templates/build-music-options.py <project>/
python3 <project>/build-music-options.py && MIX=mix-M1.wav bash <project>/assemble.sh
```

Where to find commercial-safe tracks, the edit in detail and the checks: `music.md`.

## 11. Checks before the render

```bash
cd <project> && npx hyperframes check
cd <project> && npx hyperframes snapshot --at <frame midpoints, and each cut -0.1 and +0.2, comma-separated>
```

Open `<project>/snapshots/contact-sheet.jpg`. Midpoints: layout failures, the subtitle band (y 890 to 980) free of
anything else, no element cut by the frame edge (no sliver of a card), balanced side margins, one thing to look at.
Around every seam: a continuing element must keep its position, scale, opacity, blur and direction, the camera must be
in the same move, nothing is doubled and nothing is missing. Seam times (the cumulative durations):

```bash
python3 -c "import re,itertools; d=[float(x) for x in re.findall(r'(?m)^- duration: ([0-9.]+)s', open('<project>/STORYBOARD.md').read())]; print(' '.join(f'{t:.2f}' for t in itertools.accumulate(d[:-1])))"
```

For each seam time T, snapshot `T-0.033,T,T+0.033` (the last image of frame N, the first of frame N+1, the next one).

## 12. Render and control of the real video

```bash
cd <project> && npx hyperframes render --quality high --output renders/video.mp4
bash .claude/skills/motion-design/scripts/contact-sheets.sh <project>/renders/video.mp4
```

`contact-sheets.sh` reports black segments (exit code 2 when there is one) and writes 4 images/s sheets (4 x 6, 6 s
per sheet, timestamped) in `<project>/renders/contact-sheets/` (`FPS=2` for exactly one image every 0.5 s). Open every
sheet. Then the frozen segments, the decoding errors, the loudness and the duration:

```bash
V=<project>/renders/video.mp4
ffmpeg -i $V -vf freezedetect=n=0.001:d=0.9 -an -f null - 2>&1 | grep freeze_   # no hold that the storyboard does not write
ffmpeg -v error -i $V -f null -                                                 # prints nothing
ffmpeg -i $V -vn -af ebur128=peak=true -f null - 2>&1 | tail -12                # about -16 LUFS, true peak under -1.5 dBTP
ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 $V        # a video and an audio stream, as long as the voice montage
``` Then check every seam on the real file, image by image, one strip of 6 images (3 before, 3 after) per seam:

```bash
for T in <seam times>; do
  ffmpeg -v error -y -ss "$(python3 -c "print(max(0, $T - 0.1))")" -i <project>/renders/video.mp4 \
    -vf "scale=480:-1,tile=6x1" -frames:v 1 "<project>/renders/contact-sheets/seam-$T.jpg"
done
```

Run the control grid of `patterns/PATTERNS.md` on the render, fix the frame concerned (the cheapest edit in its HTML),
re-assemble, re-render. For a stray element whose origin is unclear, hide the frames one by one in `index.html` until
it disappears. Never report the film as done before this control.

For a waveform drawn from the real voice inside a frame:

```bash
python3 .claude/skills/motion-design/scripts/waveform.py <project>/assets/audio/voix-montage.wav --start 12.4 --duration 2.6 --bars 48
```

## 13. Delivery

Give the MP4 path, its duration (`ffprobe -v error -show_entries format=duration -of csv=p=0 <project>/renders/video.mp4`),
the contact sheets and the frame ids, so the next revision can target one frame. Swap the other music options into
the same render (`python3 <project>/build-music-options.py --mux <project>/renders/video.mp4`) and deliver one MP4 per
option. For a website: web encode, poster, muted autoplay and a framed player (`landing-integration.md`); also offer
the silent loop (8 to 18 s, no audio track, readable without sound) cut from the same project. When the user asks for
other versions: `variants.md`.
