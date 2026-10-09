---
name: story-telling
description: Story video expert. Use when the user asks to make an explainer video, a story video, a reel or a short, a narrated video from an article, a cartoon explainer, or asks to add a scene, change a voice, redo an image, switch to vertical, or re-render an existing story. Also triggers for Sarvam AI voiceover, bulbul TTS, FLUX 2 image generation, flux-2-pro/edit reference photos, and Remotion narration timing.
argument-hint: "[topic or article path]"

---

# Story Telling Video Skill

## Environment

- Node 20+, npm. No bun and no ffmpeg anywhere in the pipeline
- Remotion 4.0.512, every `@remotion/*` on one version, `mediabunny` 1.50.8
- Narration: Sarvam AI `bulbul:v3`, returns WAV, played directly with no conversion
- Images: FLUX 2 on fal.ai, `fal-ai/flux-2-pro` for text to image and
  `fal-ai/flux-2-pro/edit` to restyle a reference photo the user owns
- Drafting: OpenAI, optional, one call, only used by `npm run draft`
- Durations: `@remotion/media-parser` with `nodeReader`, never ffprobe
- Keys and every model id come from `.env`, loaded by `cli/env.ts` from the
  project root and from the parent folder. `SARVAM_KEY` aliases `SARVAM_API_KEY`
- Fonts: `@remotion/google-fonts`, loaded at module level with explicit weights
- Output: 1920x1080 landscape or 1080x1920 vertical, 30fps, H.264
- Stories live in `public/<slug>/`, renders in `out/`
- Never use icons or emoji in code, prompts, logs, narration or commit messages

## Critical Rules

1. **story.json is the single source of truth.** Script, image prompts, voice,
   fonts, colours, stat cards and measured durations all live in
   `public/<slug>/story.json`. The composition reads it through
   `calculateMetadata`. Never hardcode a duration, size or asset path in a component.
2. **Audio drives length.** `npm run generate` measures every voice file and
   writes `durationInFrames` back. `durationInFrames` and
   `audioDurationInSeconds` are outputs, never hand edited. To lengthen a video,
   change the words or raise `outro.durationInFrames`, never stretch a scene.
3. **Show the narration before generating.** Voices and images cost money and
   take minutes. A wrong figure caught in review is free.
4. **Facts come only from the given context.** Nothing inferred, rounded or
   assumed. When the source contradicts itself, prefer body text over headline
   and tell the user which reading was used.
5. **Spell numbers as words in narration, digits only on stat cards.** "thirty
   four thousand crore" is spoken, `Rs 34,387 cr` is shown.
6. **Never name a real person in an image prompt.** Use a reference photo the
   user owns through the edit model, or describe the person generically.
   In an edit prompt the likeness clause comes first, scene direction second.
7. **One art style for the whole story.** `style.artPrompt` is prepended to
   every image prompt. That single string is what makes the frames feel like
   one film rather than a stock photo set.
8. **Animate with `useCurrentFrame()` and `interpolate()`,** inline in the
   `style` prop, always clamped. CSS transitions, CSS animations and Tailwind
   animation classes render as still frames.
9. **Use `scale`, `translate`, `rotate` CSS properties,** not `transform`
   strings, with `output: "perceptual-scale"` on scale animations.
10. **Respect the video safe area.** 80px from the sides, 100px from top and
    bottom at 1080 wide, scaled by composition width. Headlines at least 84px,
    supporting text at least 44px on the same scale. Take sizes from
    `getLayout()`, never typed pixel constants.
11. **Image ids are global across the story,** not per scene. A reused id
    silently overwrites a frame, and zod will not catch it.
12. **Skip work that already exists.** The generator skips any voice or image
    already on disk. Delete exactly what should change and rerun; `--force`
    should be rare.
13. **Never commit `.env`, a key, or generated media.** `story.json` regenerates
    everything else, and keys must never reach a settings file or a skill file.

## Modular Rule Files

| Rule File | Topic |
|---|---|
| [story-json](rules/story-json.md) | The schema field by field, full example, cheap edit recipes |
| [narration](rules/narration.md) | Script shape, word budget per duration, TTS-safe phrasing, stat cards |
| [voices](rules/voices.md) | Complete bulbul voice catalog, 11 languages, pace and temperature, font pairing |
| [images](rules/images.md) | FLUX 2 models, prompt recipe, reference photos, likeness, real failure modes |
| [models](rules/models.md) | Every model id, where it is configured, how to choose, cheap iteration loop |
| [story-formats](rules/story-formats.md) | Format catalog with scene skeletons and stat placement |
| [composition](rules/composition.md) | Remotion best practices the components follow |
| [workflow](rules/workflow.md) | Commands, key verification, cost and timing, troubleshooting |
| [pitfalls](rules/pitfalls.md) | The fourteen common mistakes, plus both checklists |

## Story Templates (in rules/assets/)

Schema-validated starting points. Copy to `public/<slug>/story.json`, change
`slug` and `compositionId`, rewrite the narration and prompts, then generate.

| Format | Path | Length | Scenes | Images |
|---|---|---|---|---|
| Biography | `assets/biography/story.json` | 60s | 6 | 12, uses a reference photo |
| Concept explainer | `assets/explainer/story.json` | 60s | 6 | 9, metaphor led |
| Vertical short | `assets/reel/story.json` | 30s | 3 | 3, 1080x1920 |
| Numbered list | `assets/listicle/story.json` | 60s | 6 | 7, numbered stat cards |
| News or event | `assets/news/story.json` | 45s | 5 | 7, dated claims |
| Myth versus fact | `assets/myth-buster/story.json` | 45s | 5 | 5, alternating |

## Companion Skills

| Skill | Use for |
|---|---|
| `story-setup` | First run: Node check, install, `.env`, key verification, version alignment |
| `story-new` | Context to finished video, with a script review step |
| `story-render` | Change one line, one image, the voice or the orientation, then re-render |

## Pipeline

```
context (article, notes, a paragraph, a page already read)
   |
   |  npm run draft            OpenAI, optional. Or write story.json yourself.
   v
public/<slug>/story.json       script, image prompts, voice, style, stats
   |
   |  npm run generate         Sarvam voices, FLUX 2 images, measured durations
   v
public/<slug>/                 voice-0.wav ... image-1.jpg ... story.json updated
   |
   |  calculateMetadata        reads story.json, sets size, fps, durationInFrames
   v
npx remotion render <CompositionId> out/<slug>.mp4 --codec h264
```

## Instructions

0. **Check the pipeline exists before anything else.** These skills drive a
   Remotion project. If the skills were installed on their own, `cli/` and
   `src/` are not present yet and must be fetched once:

   ```bash
   test -f cli/generate.ts && test -f src/Root.tsx && echo present || echo missing
   ```

   If missing, run the `story-setup` skill, which fetches the project with
   `npx --yes degit marketcalls/story-telling story-telling`, installs
   dependencies, creates `.env` and verifies the keys. Everything below runs
   from the project root.
1. Read the rules you need from the table above. `story-formats` first if the
   shape is not decided, `narration` and `images` before writing anything.
2. Confirm the environment: `.env` with `SARVAM_API_KEY` and `FAL_KEY`,
   `npm install` done. If unsure, run the `story-setup` skill.
3. Settle three things with the user if not already clear: orientation, length
   in seconds, and whether reference photos are involved.
4. Write `public/<slug>/story.json` from a template, or draft it with
   `npm run draft` and then fix the facts by hand.
5. Show the narration and wait for approval.
6. `npm run generate -- --slug <slug>`.
7. Preview with `npm run studio`, then render.
8. Run the shipping checklist in `rules/pitfalls.md`.
9. Report measured numbers: scene count, duration, image count, output path and
   size, plus any assumption made about an ambiguous fact.

## Commands

```bash
npm install                                          # once
npm run story    -- --slug big-bull --context ./article.md --seconds 60 [--render]
npm run draft    -- --slug big-bull --context ./article.md --orientation vertical
npm run generate -- --slug big-bull [--only voice|images] [--force] [--logs]
npm run studio
npm run typecheck
npx remotion render BigBull out/big-bull.mp4 --codec h264
```

`--context` accepts a file path or the text itself. Any folder under `public/`
containing a `story.json` becomes a composition automatically, named after the
slug in PascalCase, so nothing is registered by hand.

## Project Layout

```
.env                       keys and every model id
cli/
  env.ts                   loads .env from here and from the parent folder
  service.ts               Sarvam, FLUX 2 text to image, FLUX 2 edit, OpenAI
  draft.ts                 context  ->  story.json
  generate.ts              story.json  ->  assets  ->  measured durations
  story.ts                 draft, generate and optionally render in one go
src/
  Root.tsx                 story discovery, calculateMetadata
  StoryVideo.tsx           scene timeline, audio, outro
  components/              ImageLayer, Subtitle, StatCard, TitleCard, OutroCard
  lib/schema.ts            zod schema shared by the CLI and the composition
  lib/layout.ts            safe areas and type scale, both orientations
  lib/fonts.ts             module level font loading
public/<slug>/             story.json, voice-N.wav, image-N.jpg
out/                       rendered mp4
```

## Worked Example

`public/jhunjhunwala/story.json` is a complete 6 scene, 58.7 second landscape
story: cartoon art, two reference photos restyled through `flux-2-pro/edit`,
stat cards on four scenes, and a silent outro. Read it before writing a new one.
Its media files are gitignored, so regenerate them with
`npm run generate -- --slug jhunjhunwala`.

## Example Usage

`/story-telling turn this article into a sixty second explainer`
`/story-new big-bull ./article.md 60 landscape`
`/story-render big-bull images`
