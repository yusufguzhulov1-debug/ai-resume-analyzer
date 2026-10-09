# Variants: several directions on the same voice

Once a film is validated, the next request is usually "can you do better, give me options". Make them on the **same
voice montage and the same word timings**: the frame boundaries and every cue stay identical, so every music option
(`music.md`) fits every picture option, and the user chooses the picture and the music independently (3 directions x 4
musics = 12 films for the price of 3 renders and a few muxes).

## Three kinds of variant

| Kind | What changes | What stays | Example (film C) |
|---|---|---|---|
| **Polished** | only what the user pointed at, plus one stronger peak | everything else, file by file | « Poli »: the stressed persona redrawn so it reads at thumbnail size (hands on the head, eyebrows, sweat drop), and « libre. » becomes the peak in a giant pill while the struck quote flies away |
| **Restyle, same choreography** | the look: grounds, lights, cards, colors (`frame.md` and the world lines of `STORYBOARD.md`) | frames, Scene lines, cues, motion | « Nuit »: the whole film dark (the solution on a warm night stage, terracotta glow, warm glass cards) so it melts into a dark landing page, no paper bed, a warm flash |
| **New direction** | `frame.md`, the Scene lines, most frame files | the voice, the frame boundaries, the word cues, the pivot and the iris times | « Le bureau »: the film seen from above a real desk, with objects (paper quote, terracotta pen, torn sticky note, SUR DEVIS stamp, tear-off calendar, pile of invoices, morning light, laptop, the zero drawn in a notebook) |

Offer the three kinds at once: the polished one is the safe choice, the restyle answers a context (the page it will
sit on), the new direction shows what else is possible.

## Folders and commands

One folder per variant at the repository root, copied from the validated project:

```bash
cp -R <project> <project>-nuit && rm -rf <project>-nuit/renders <project>-nuit/snapshots <project>-nuit/.hyperframes
```

Keep `assets/` (voice montage, fonts, icons, mixes) and `onsets.json`. In each variant, `assemble.sh` reads the mix
from the environment, so one command renders any direction with any music:

```bash
MIX=mix-M1.wav bash <project>-nuit/assemble.sh
cd <project>-nuit && npx hyperframes render --quality high --output renders/nuit-M1.mp4
```

(`templates/assemble.sh` reads `MIX`, default `mix.wav`.) Then swap the other musics in with the mux command of
`music.md`. The restyle usually changes the orchestrator layer too: the all-dark variant drops the paper bed
(`PAPER=""`) and gives the flash a warm radial instead of a paper white; the desk variant puts the day desk color under
the light world (`PAPER="#e7dccd"`).

## Build order: recurring objects first

A new direction has objects that come back from frame to frame (the desk, the quote sheet, the pen, the laptop). If
every worker draws its own, the pen changes shape at every cut.

1. **Wave 1**: dispatch only the frames that **introduce** a recurring object (in film C « Le bureau »: 01 the desk and
   the quote sheet and the pen, 02 the sticky note and the calendar, 03 the stamp and the pile, 04 the day desk and
   the laptop). Ask each worker to wrap every recurring object in named HTML comments:
   `<!-- quote-sheet -->` ... `<!-- /quote-sheet -->`.
2. **Wave 2**: dispatch the other frames with one more line in the dispatch context: "Copy the block
   `<!-- quote-sheet -->` ... `<!-- /quote-sheet -->` from `compositions/frames/01-devis.html` verbatim (markup and its
   CSS), then animate it; do not redraw it."
3. Check the seams on the contact sheet: the same object must look the same on both sides of every cut.

## Resume after a session cut

Long nights of parallel workers get cut (usage limit, crash, closed laptop). Before relaunching anything:

```bash
python3 .claude/skills/motion-design/scripts/check-frames.py <project>
```

It lists every frame of the storyboard as OK, MISSING or BROKEN: a file that is not one complete
`<template>...</template>` was half-written by a worker that died; a script that fails `node --check` has a syntax
error. Re-dispatch **only** the frames that are not OK (with the reason in the dispatch context), never the frames that
are OK. Then `bash <project>/assemble.sh` (it skips frames that are still missing) and continue.

## Delivery

One folder with every combination, named `<direction>-<music>.mp4`, plus one line per direction (what it is, what it is
for) and one line per music. Say which combination you would pick and why, then let the user choose.
