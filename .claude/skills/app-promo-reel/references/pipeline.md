# Pipeline — commands per stage

`S=<skill>/scripts`, `P=<out>/<app>-<variant>` (the project folder). `PY` = a Python with
`requirements.txt` (and, for step 3, `requirements-gen.txt` + CUDA torch).

## Beat addressing (used everywhere)

`D(bar, beat=0)`: `bar` is 0-based from the first downbeat of `beats.json` (negative bars are
pickup beats before it); `beat` is 0-based inside the bar; `beats_per_bar` is in project.json
(default 4). `E(bar, beat)` is the "and": halfway to the next beat.

- Template tokens: `{{D 3}}`, `{{D 3 2}}`, `{{E 3 1}}`, `{{LEN 2 6}}` (= D(6) − D(2)),
  `{{TO_END 12}}`, `{{calc D(2)-0.3}}` (numbers, + − * /, parentheses, D, E, DURATION only),
  `{{BEFORE_END 1.1 D(13, 3)}}` (renders nothing; the build fails when the time is less than
  1.1 s before the end),
  `{{BEATS}}`, `{{DOWNBEAT_INDEX}}`, `{{BEATS_PER_BAR}}`, `{{DURATION}}`, `{{STORES}}`.
- In the page script the same `D()` / `E()` exist in JavaScript.
- `cues.json` `"at"` fields and `make_bed.py --drop-bar k` use the same `D()`.

## 1. Scaffold

```bash
SFX_DIR=~/my-sfx $PY $S/new_project.py --app myapp --variant a --lang en --stores <STORES> --format 9:16
```
`<STORES>` is the stores the app is really on: `app_store`, `google_play`, or
`app_store,google_play`. The default (both) is wrong for a single-store app: its end card
would show a badge for a store the app is not in.
Default out folder `~/app-promo-reels`. Refuses a folder inside a git work tree (use `--force`
if you are sure) and always refuses the app-promo-reel repo itself. project.json is the one
place for duration, fps, format, beats per bar and stores.
`--format`: `9:16` (1080x1920; Reels, TikTok, Shorts, Stories; the default) or `4:5` (1080x1350; a
feed post). The format sets the frame size: width and height in project.json must match it, and
`16:9` (1920x1080; a silent web-hero loop, see `hero.md`) is a different product, not a wider
copy of the others. finish.py fails a render of another size. The template is the same for both: a `4:5` layer at the
end of its CSS moves only what depends on the frame height (the phone at 0.79, the hook card, the
captions). Pixel distances in motion (the camera shake) scale with `{{FRAME_SCALE}}`. A new
format for an existing variant is a new project: its copy of the template was built for its size.

## 2. Research

```bash
$PY $S/store_assets.py --out $P/work/store --app-store-id 123456789 --play com.example.app --country us --lang en
$PY $S/sample_colors.py $P/work/store/screens/01.png points.json   # relative coords 0-1
git -C <app-repo> fetch origin
git -C <app-repo> symbolic-ref refs/remotes/origin/HEAD            # -> origin/<branch>
git -C <app-repo> show origin/<branch>:<path/to/strings>
```
store_assets.py first removes an old metadata.json and screens/NN.png from `--out`. Exit 2 = no App Store data: ask the user for screenshots, or build from the
website only. Play facts are best-effort and never guessed.

## 3. Music

One source per session (SKILL.md step 3 says which). ACE-Step 1.5, with its own Python:
```bash
$ACESTEP_DIR/.venv/bin/python $S/music_gen_ace.py --bpm 122 --duration 30 --seeds 5,17,23 \
  --out $P/work/music --prompt "upbeat indie pop, punchy four on the floor kick, crisp handclaps on the backbeat, bright synth hooks, energetic from the first bar"
```
MusicGen (needs an NVIDIA GPU):
```bash
$PY $S/music_gen.py --duration 30 --seeds 5,17,23 --out $P/work/music \
  --prompt "upbeat indie pop, punchy four on the floor kick, crisp handclaps on the backbeat, 118 bpm, clear steady beat, energetic from the first bar"
```
The user's own track, downloaded by hand (writes `bgm_user.wav` and `bgm_user.source.txt`):
```bash
$PY $S/music_import.py ~/Downloads/track.mp3 --out $P/work/music --source "<page URL, licence>" --start 12.5
```
Then, for every source, rank the files of this batch by name (`bgm_user.wav` for an own track).
Never a `bgm_*.wav` glob: it also ranks the tracks left by an earlier source or batch.
```bash
$PY $S/music_rank.py --duration 30 --json $P/work/music/rank.json $P/work/music/bgm_{5,17,23}.wav
$PY $S/beat_grid.py $P/work/music/bgm_5.wav $P --bpm 122
$PY $S/make_bed.py $P/work/music/bgm_5.wav $P --drop-bar 6
```
- One music generator at a time (either script); exit 2 = a hard failure, no file written.
- `music_gen_ace.py` exit 3 = the GPU ran out of memory: run the same command once with
  `--device cpu` (about 85 s per seed on a 32-thread CPU, 15 GB RAM). Each seed is made 10 s
  longer than `--duration`, because ACE-Step ends the song inside the length it is given.
- Tempo: 118-128 bpm; the 30 s template needs about 116 bpm or more (see storyboard.md). At
  ~120 bpm a 30 s video has 15 bars — the template's scenes assume bars 0-14. ACE-Step takes the
  tempo as `--bpm`: its prompt names genre and instruments, no tempo words. A MusicGen prompt
  names the tempo, a steady kick, and "clear steady beat".
- ACE-Step, measured on 9 seeds: at 120 bpm all 3 passed the rank gate, but their first bar
  starts late (1.48-2.04 s), so the stock template's last line lands under 1.1 s before the end
  and build.py stops; at 122 bpm 2 of 3 passed and one fitted; at 124 bpm none passed (the
  tempo drifted to 125-127). Start at 122; when build.py stops with the re-map message, take
  the next seed or re-map the scenes to fewer bars.
- `beat_grid.py --bpm`: the value asked of ACE-Step; for MusicGen and an own track, the `tempo`
  column of the rank table. When beat_grid stops ("the grid came out at X BPM") it writes
  nothing: count the seed as rejected and never run make_bed on it.
- music_rank.py and beat_grid.py judge only the first `--duration` seconds, the part make_bed
  keeps; an outro after it does not count.
- An own track needs a steady tempo and no quiet passage inside that window: choose the window
  with `--start`. For a 3/4 or 6/8 track, set `beats_per_bar` in project.json first.
- Seeds with a real lift: note `lift_at` from the rank table (drop rule: storyboard.md).
- Run `make_bed.py` after `beat_grid.py` (the lift window needs beats.json).
- The template's cues.json already ends a riser tail on the drop. Use `make_bed.py --riser`
  only when you remove that cue, or the riser plays twice.

## 4. Build

```bash
$PY $S/build.py $P      # src.html.tmpl (+ motion.js) -> index.html, cues.json -> cues.realized.json
<the command after "check:">   # the last line build.py prints
cd $P
npx --yes hyperframes@0.8.78 snapshot --at 1.0,2.4,4.6,... --describe false --no-end -o snapshots/r1
```
- Always edit `src.html.tmpl`, never index.html (it is overwritten).
- The last line build.py prints is `check: <command>`. Run that command until it gives 0 errors, not a
  plain `hyperframes check`. For 9:16 and 4:5 it adds the bottom of the feed safe box as an error band
  (`--caption-zone`), read only at the settled times (`references/storyboard.md`, "Feed safe zones"). A
  `caption_zone_collision` error is a text in that band on a settled frame: move it up. For 16:9 it is
  the plain check.
- build.py prints a warning when the page calls `shake(` or `flash(` more than 2 times
  (`references/motion.md`). The build still succeeds.
- build.py adds the AI-generated label itself (text from `CONFIG.aiLabel`) with the last script
  of index.html: never add a label element or CSS for it to the template. A `page_error` about
  the AI-generated label in `hyperframes check` means it is empty, something hides it, or (9:16 and
  4:5) it is not fully inside the feed safe box: shorten `CONFIG.aiLabel`.
- Leftover or unknown `{{…}}` → exit 2.
- A cue whose SFX file is missing is skipped with a warning; the build still succeeds.
- Snapshots: pick every scene middle and every transition ±0.1 s. Write each round to a new
  `-o snapshots/rN` folder.

## 5. Render and finish

For `16:9` the same two commands apply, and the run has no loudness, A/V or sync step: it checks the
picture, the frame count, the seam and that the file has no audio. See `hero.md`.

```bash
cd $P && npx --yes hyperframes@0.8.78 render -o renders/raw.mp4 -q delivery --quiet
$PY $S/finish.py $P renders/raw.mp4
```
Optional motion blur (9:16 and 4:5, for fast moves; about 2.5 minutes for 30 s instead of about
25 s): render at 240 fps and let `scripts/blur.py` write `renders/raw.mp4`, then finish as usual.
```bash
cd $P && npx --yes hyperframes@0.8.78 render -o renders/sub240.mp4 -q delivery --fps 240 --quiet
$PY $S/blur.py $P renders/sub240.mp4
$PY $S/finish.py $P renders/raw.mp4
```
The input rate must be a whole multiple (4 or more) of the project fps: `--fps 240` for 30 fps,
the largest multiple up to 240 for another fps (200 for 25 fps). blur.py prints `cuts:` (the frames
whose window a cut made shorter) and `fastest:` (the frames to check for copies, `references/motion.md`,
"Motion blur"). It sets the colour tags of the render on its raw frames as well as on the output:
with tags on the output only, ffmpeg 7 converts the colour matrix and a still frame changes level.
finish.py: two-pass loudnorm to -14 LUFS / -2 dBTP (linear; the final AAC file must measure
within 1 LU of -14 and at most -1 dBTP), A/V lag check on the PCM before
AAC (< 5 ms), video stream copied and compared, sync report (each cue's own sound located by a
matched filter within ±150 ms on the audio minus the bed; fail on a cue > 1 frame off, or on
any checked cue not found — mark a cue that sits under a louder sound `"sync": false` in
cues.json), contact sheet, versioned output that never overwrites. While the checks run the file
is `…-v<N>.checking.mp4`; it becomes `…-v<N>.mp4` only when every check passed. Exit 1 → output
and contact sheet named `…-v<N>-failed.mp4` and the report lists the problems; an error or
Ctrl-C during the checks also leaves `-failed` (no report). A `.checking` file left behind was
never checked: do not deliver it.
Frame checks on the final MP4 print `warning:` lines and never fail the run: frame 0 blank (the
feed thumbnail), nothing readable by 1 s, nothing readable at all, a one-frame flash, a sudden
change near no beat and no scene start, or a still run over 0.8 s (not for 16:9; the end card may
hold 2.5 s; `"holds"` in the report). They are in the report under `"frames"`; the critique step of SKILL.md reads them.
When every check passed, finish.py also writes `…-v<N>-poster.jpg`: one frame at the full video size
(JPEG, quality 90) for a store listing, a link preview or a social cover. It is the frame with the most
detail among the settled frame of each scene (1.1 s after its start, 0.5 s before the end for the last one);
the report has `"poster"` with its time, its score and every candidate. `--poster-at <s>` names the frame
instead (0 or more, inside the video; else exit 2 before any file is written). A poster that cannot be
written fails the run like any error after the mux: `-failed`, no report. The skill never uploads it.
