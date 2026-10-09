---
name: story-render
description: Regenerate and render an existing story. Use to change a line of narration, swap a voice, redo one image, switch orientation, or re-render to mp4.
argument-hint: "[slug] [what-changed]"

---

Re-run part of an existing story without paying for the whole thing again.

## Arguments

- `$0` = slug, the folder name under `public/`
- `$1` = what changed: `narration`, `voice`, `images`, `orientation`, or
  `render` for no change at all

If no slug, list the folders under `public/` that contain a `story.json` and
ask which one.

## How the skip logic works

`npm run generate` skips any `voice-N.wav` or `image-N.jpg` already on disk.
That is the whole cost control: delete exactly what should change, leave the
rest, and rerun. `--force` regenerates everything and should be rare.

## Recipes

### Changed a line of narration

Edit `scenes[N].narration` in `public/<slug>/story.json`, then:

```bash
rm public/<slug>/voice-N.wav
npm run generate -- --slug <slug> --only voice
```

The new duration is measured and written back into `story.json`, so the scene
and its subtitles resize themselves. Never hand edit `durationInFrames`.

### Changed the voice or the language

Edit `voice.speaker` or `voice.languageCode`, then regenerate all narration:

```bash
rm public/<slug>/voice-*.wav
npm run generate -- --slug <slug> --only voice
```

Speaker names are lowercase. Check the catalog in
`story-telling/rules/voices.md`, and remember a non-Latin `languageCode` needs
a font that covers the script, added in `src/lib/fonts.ts`.

### One image is wrong

Edit that image's `prompt`, then:

```bash
rm public/<slug>/image-7.jpg
npm run generate -- --slug <slug> --only images
```

For a face that drifted from its reference, move the likeness clause to the
front of the prompt. See `story-telling/rules/images.md`.

### The whole look is wrong

Change `style.artPrompt`, delete every image, regenerate. Narration is
untouched, so this only costs the image calls:

```bash
rm public/<slug>/image-*.jpg
npm run generate -- --slug <slug> --only images
```

To iterate cheaply, set `FLUX_TEXT_MODEL=fal-ai/flux-2/flash` in `.env`, tune
the prompts, then switch back to `fal-ai/flux-2-pro` and regenerate.

### Switching landscape to vertical, or back

Images are generated at the composition size, so all of them are now the wrong
shape:

```bash
# after editing "orientation" in story.json
rm public/<slug>/image-*.jpg
npm run generate -- --slug <slug> --only images
```

Voices are unaffected. Check the result in the Studio: the stat card moves to
top centre and subtitles regroup to 4 words automatically.

### Adding a scene

Append a scene with the next `id`, give its images unused ids, then
`npm run generate -- --slug <slug>`. Only the new assets are generated.

### Just re-render

```bash
npx remotion render <CompositionId> out/<slug>.mp4 --codec h264
```

Useful options: `--concurrency 4` if memory is tight, `--frames 0-120` to check
a section quickly, `--scale 0.5` for a fast rough cut.

## Checks before reporting

- `npm run typecheck` clean
- Read the real output duration rather than assuming the planned one
- Watch the last scene: subtitle drift shows there first
- Report duration, file size and path as measured

## Example usage

`/story-render big-bull narration`
`/story-render big-bull images`
`/story-render big-bull render`
