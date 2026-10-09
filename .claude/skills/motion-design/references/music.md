# Music: pick, sync, mix, and deliver several options

Music is taste: never deliver one soundtrack. Build 3 or 4 options on the same voice and the same picture, let the
user choose by ear, and swap the soundtrack of the rendered video without rendering it again.

## The edit that works (locked on the picture)

The launch film has a pivot (a word alone such as « Stop. », or a silence) followed by the light flash into the
solution. The music follows that shape:

1. **Tension until the pivot.** A dark, regular pulse or a build that rises under the problem, taken from a **full
   section** of its track (not a sparse intro) and set **2 to 3 dB under the élan at most**: lower, the start of the
   film feels soft.
2. **Cut to silence on the pivot**, with a low impact (`impact-bass-1`) on the pivot word. A riser (`riser`, 10 s
   build that crests at its very end) can climb during the last 3 s and crest exactly there.
3. **The drop lands on the light** (the flash at `LEAK_AT + 0.05` of `assemble.sh`, or the first word of the
   solution, « Aujourd'hui » in the flagship film), with `sparkle` and a soft `whoosh`.
4. **Under the voice, not on it**: the music is ducked by the voice (`sidechaincompress`) and breathes back in the
   silences between sentences.
5. **Fade out on the end card** (2.4 to 2.8 s), a `whoosh-cinematic` before the iris, a `chime` on the peak word.
6. **Web loudness**: `loudnorm` to -16 LUFS, true peak under -1.5 dBTP.

Two ways to get there:

- **Two tracks**: a "tension" track until the pivot, an "elan" track from the flash, started at its drop.
- **One track with a drop**: the same file twice, the second segment offset so the drop hits the flash. The music
  stops on the pivot and comes back on the drop, as if the film had been scored.

## Find the drop and the start time

```bash
python3 .claude/skills/motion-design/scripts/analyze-music.py <project>/assets/music/*.mp3 --drop-at <LIGHT>
```

For each track: tempo (with the half or double reading), energy jumps (6 dB or more on the full band, 8 dB under
150 Hz where bass and kick entries show), rises, bright or dark (spectral centroid), the main drop, and the sync: "start
the music at film X s" when the drop comes before the flash in the track, "start the file at X s (trim)" when it comes
after. Accurate to about 0.1 s: listen and adjust by a frame or two.

How to read a track for this edit:

| Profile | What to look for | Role |
|---|---|---|
| tension | dark or medium, regular beat, no drop, or a bass entry before the pivot | 0 to the pivot |
| elan | bright, a clean drop in the first 20 s | from the flash |
| complet | a build then a drop inside the track | the whole film, cut on the pivot |
| minimal | piano or pad, no drums, loose tempo | the whole solution, leaves all the space to the voice |

## Build the options

Copy `templates/build-music-options.py` into the project, set `DUR`, `PIVOT`, `LIGHT`, the `OPTIONS` (segments:
file, track start, film start, film end, gain, fade in, fade out; optional riser gain) and run:

```bash
MUSIC_DIR=<project>/assets/music python3 <project>/build-music-options.py
MUSIC_DIR=<project>/assets/music python3 <project>/build-music-options.py --mux <project>/renders/video.mp4
```

It reuses the voice montage of `build-audio.sh` and the film's `sfx-events.json`, adds the pivot effects, writes
`assets/audio/mix-<id>.wav` per option and prints a check (below). Starting gains: tension 0.34 to 0.42, elan 0.26 to
0.30, piano 0.6 (a solo piano is quieter); then set the tension gain from the measure below, not by ear. `SFX_DIR`
defaults to the Pixabay set of `media-use`. The mix of the flagship film, with its four tension options, is
`examples/ligne-du-temps-v8/build-audio-v8.py`.

To render the film with one option: `MIX=mix-M1.wav` in `assemble.sh` (the audio path of the orchestrator layer), or
keep one render and swap the soundtrack:

```bash
ffmpeg -i video.mp4 -i mix-M2.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k video-M2.mp4
```

The picture is copied as is (`-c:v copy`): four options take seconds, not four renders.

## Check before delivering

The script prints, for each option:

- **energy under 150 Hz** before the pivot, between the pivot and the flash (music alone), and after the flash. The
  middle value must be near silence (under -60 dB): if the bass keeps going, the pivot is not heard.
- **voice against music** in the 1.5 s before the pivot: keep 8 dB or more. The pivot is where the music is the most
  tempting to push, and where it most often covers the voice.
- **tension against élan**, music alone before ducking, in LUFS: the tension segment (0 to the riser) must sit 2 to 3
  dB under the élan segment at most. On the flagship film it was 10 dB under (the sparse intro of its track) and the
  first seconds felt soft; its four tension options, rebuilt from full sections, sit 2 dB under. Adjust the tension
  segment (its track start, then its gain) rather than the élan.

By hand, for any window:

```bash
ffmpeg -i mix.wav -af "atrim=13.0:14.0,lowpass=f=150,volumedetect" -f null -   # bass around the pivot
ffmpeg -i mix.wav -af ebur128=peak=true -f null -                              # integrated loudness and true peak
```

Note: `alimiter` applies a make-up gain by default (`level`), which cancels its own ceiling and pushes the true peak
back near 0 dBFS. The template uses `level=disabled` and a -2 dBFS ceiling after `loudnorm`.

## Where to find music you can use commercially

- **CC0 only** (public domain dedication: commercial use, editing and syncing allowed, no attribution required). On
  [Free Music Archive](https://freemusicarchive.org): [HoliznaCC0](https://freemusicarchive.org/music/holiznacc0/),
  [Loyalty Freak Music](https://freemusicarchive.org/music/Loyalty_Freak_Music/), and
  [Komiku](https://freemusicarchive.org/music/Komiku/) **only for the tracks marked CC0**. Check the license on each
  track page: album pages say "check individual tracks".
- Avoid CC BY-NC (non-commercial), tracks ripped from YouTube, and any track without a clear license page.
- Pixabay Music refuses scripted downloads (HTTP 403): download by hand if you use it, under the Pixabay Content
  License. FreePD was offline when tested.
- A courtesy credit is optional under CC0: `Music: "<Title>" by <Artist> (CC0 1.0, freemusicarchive.org)`.

## The 10 tracks used for film C

All CC0 1.0 Universal, downloaded from the Free Music Archive on 2026-09-28, license checked on each track page. The
files are not in this repository: download them from the links. Measured with the method of `analyze-music.py`
(drop times from the analysis done that night, within 0.1 s of what the script prints).

| File name used | Title, artist | BPM | Main drop | Tone | Source page | Direct file |
|---|---|---|---|---|---|---|
| tension-time-attack-research.mp3 | Action Time Attack Research, Komiku | 120 | none | dark | [page](https://freemusicarchive.org/music/Komiku/The_Binge_Watchers__Score_1/Komiku_-_The_Binge_Watchers_-_Score_1_-_02_Action_Time_Attack_Research/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/music/Music_for_Video/Komiku/The_Binge_Watchers__Score_1/Komiku_-_02_-_Action_Time_Attack_Research.mp3) |
| tension-waiting-tttt.mp3 | Waiting TTTT, Loyalty Freak Music | 160 | none (bass at 11.9 s) | medium | [page](https://freemusicarchive.org/music/Loyalty_Freak_Music/MINIMAL_AMBIENT_BOUNCE/Loyalty_Freak_Music_-_MINIMAL_AMBIENT_BOUNCE_-_05_Waiting_TTTT/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/music/Music_for_Video/Loyalty_Freak_Music/MINIMAL_AMBIENT_BOUNCE/Loyalty_Freak_Music_-_05_-_Waiting_TTTT.mp3) |
| tension-cyber-anxiety.mp3 | Cyber Anxiety, HoliznaCC0 | 160 | none (bass at 9.0 s) | medium | [page](https://freemusicarchive.org/music/holiznacc0/waves-of-nostalgia-2/cyber-anxiety/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/aMnXXiVF5hW9DxadJ8xUOsEccZjO1UAlJDl9BjOP.mp3) |
| elan-dear-mr-super-computer.mp3 | Dear Mr Super Computer, HoliznaCC0 | 130 | 5.59 s | bright | [page](https://freemusicarchive.org/music/holiznacc0/power-pop/dear-mr-super-computer/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/6mRjlU0gvJgHShEyDHlHSmlctyrROaF8dHy7qRC5.mp3) |
| elan-back-in-the-80s.mp3 | Back In The 80s, HoliznaCC0 | 120 | 7.93 s | bright | [page](https://freemusicarchive.org/music/holiznacc0/power-pop/back-in-the-80s/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/mwxiOyntd7joJQg0mRq9cJPqRq6NvnrK2Xc3QDUe.mp3) |
| complet-machines-with-feelings.mp3 | Machines With Feelings, HoliznaCC0 | 100 | 19.14 s | bright | [page](https://freemusicarchive.org/music/holiznacc0/waves-of-nostalgia-2/machines-with-feelings/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/mmejh2WUiSgYYUiVyzc8YPSrKmKpYCFg3G3mS9cj.mp3) |
| complet-retro-synths.mp3 | Retro Synths, HoliznaCC0 | 120 | 15.92 s | bright | [page](https://freemusicarchive.org/music/holiznacc0/power-pop/retro-synths/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/iWRFaLOfYZ7uoW1ugOUUUlfHkpsZnLzTQJ0CUWqr.mp3) |
| complet-feels-good-to-be-alive.mp3 | It feels good to be alive too, Loyalty Freak Music | 140 | 13.64 s | bright | [page](https://freemusicarchive.org/music/Loyalty_Freak_Music/ROBOT_DANCE_/Loyalty_Freak_Music_-_ROBOT_DANCE__-_04_It_feels_good_to_be_alive_too/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/music/Music_for_Video/Loyalty_Freak_Music/ROBOT_DANCE_/Loyalty_Freak_Music_-_04_-_It_feels_good_to_be_alive_too.mp3) |
| minimal-drifting-piano.mp3 | Drifting Piano, HoliznaCC0 | 100 | none | dark | [page](https://freemusicarchive.org/music/holiznacc0/background-music/drifting-piano/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/uGFgbWaUKc0LLRnbLShVKZ7yhiK5nsxczsKgpcvW.mp3) |
| minimal-ambiant-hope.mp3 | Ambiant Hope, Komiku | 133 | none | medium | [page](https://freemusicarchive.org/music/Komiku/The_Binge_Watchers__Score_1/Komiku_-_The_Binge_Watchers_-_Score_1_-_10_Ambiant_Hope/) | [mp3](https://files.freemusicarchive.org/storage-freemusicarchive-org/music/Music_for_Video/Komiku/The_Binge_Watchers__Score_1/Komiku_-_10_-_Ambiant_Hope.mp3) |

License: https://creativecommons.org/publicdomain/zero/1.0/ (legal code:
https://creativecommons.org/publicdomain/zero/1.0/legalcode).

## Worked example: the four options of film C (43.2 s, pivot « Stop. » at 14.02 s, flash at 14.30 s)

| Option | Segments (track start → film window, gain) | Riser |
|---|---|---|
| M1 tick-tock then elan | Waiting TTTT 0 s → 0 to 14.02 (0.42); Dear Mr Super Computer 5.59 s → 14.30 to end (0.30) | 0.18 |
| M2 retro synth, drop on the light | Retro Synths 1.62 s → 0 to 14.02 (0.34); the same track at 1.62 + 14.30 s → 14.30 to end (0.30) | none |
| M3 electro build, drop on the light | It feels good to be alive too 0 s → 0.66 to 14.02 (0.30); the same track at 14.30 - 0.66 s → 14.30 to end (0.26) | none |
| M4 cinema, dark pad then piano | Cyber Anxiety 0 s → 0 to 14.02 (0.40); Drifting Piano 4.2 s (0.62) + Ambiant Hope 14.9 s (0.30) → 14.30 to end | 0.14 |

The option on the published film is M1. The whole configuration is in
`examples/le-devis-options/poli/build-music-options.py`.
