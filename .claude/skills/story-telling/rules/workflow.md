---
name: workflow
description: Commands, environment, cost and timing, and troubleshooting
---

# Workflow

## Setup, once

```bash
npm install
cp .env.example .env      # then fill in SARVAM_API_KEY and FAL_KEY
```

`cli/env.ts` reads `.env` from the project root and from the parent folder, so
a shared bootcamp-level `.env` also works. Keys in the project file win.
`SARVAM_API_KEY` and `SARVAM_KEY` are both accepted.

Check the keys before a long run:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
curl -s -X POST https://api.sarvam.ai/text-to-speech \
  -H "api-subscription-key: $SARVAM_API_KEY" -H "Content-Type: application/json" \
  -d '{"text":"key test","language_code":"en-IN","speaker":"shubh","model":"bulbul:v3"}' \
  -o /dev/null -w "%{http_code}\n"
```

fal has no free ping. Posting an empty body to the model endpoint returns
`IN_QUEUE` when the key is valid, then fails validation on the missing prompt,
which costs nothing.

## Everyday commands

```bash
npm run story    -- --slug big-bull --context ./article.md --seconds 60 [--render]
npm run draft    -- --slug big-bull --context ./article.md --orientation vertical
npm run generate -- --slug big-bull [--only voice|images] [--force] [--logs]
npm run studio
npm run typecheck
npx remotion render BigBull out/big-bull.mp4 --codec h264
```

`--context` takes either a file path or the text itself.

## What each step costs

| Step | Time | Notes |
|---|---|---|
| draft | 10 to 30s | One OpenAI call. Optional. |
| voices | about 5s per scene | Sarvam, cheap. |
| images | 20 to 60s each | The bulk of the cost. 12 images for a 60s story. |
| render | 2 to 4 min for 60s at 1080p | Local, CPU bound. |

Everything is resumable. `generate` skips any file already on disk, so a failed
run picks up where it stopped and an edit to one scene only regenerates that
scene's assets.

## Troubleshooting

**`story.json is invalid`**
The zod issues are printed with paths. Common causes: a scene image id reused
across scenes, `stat` present but missing `label`, `slug` containing uppercase
or spaces.

**`Story "x" has scenes without a durationInFrames`**
The composition was opened before assets were generated. Run
`npm run generate -- --slug x`.

**`export 'Logging' was not found in 'mediabunny'`**
Mixed Remotion versions. `npx remotion versions`, then `npx remotion upgrade`,
then install the exact list it prints. All `@remotion/*` on one version, and
`mediabunny` on the version that release expects.

**`The font X does not have a weight 800`**
That family does not ship the weight. Check with
`node -e "console.log(Object.keys(require('@remotion/google-fonts/X').getInfo().fonts.normal))"`
and lower the weight in `src/lib/fonts.ts`.

**Sarvam 400 on a request that used to work**
`sarvamai` 1.1.5 switched the request keys to snake_case: `language_code`,
`speech_sample_rate`. `temperature` is bulbul:v3 only; `enable_preprocessing`,
`pitch` and `loudness` are bulbul:v2 only. `cli/service.ts` already branches on
the model, so this only bites custom code.

**Subtitles drift from the voice**
A scene's `durationInFrames` no longer matches its audio. Regenerate that voice
file, or delete it and rerun `generate` so the duration is measured again.

**Faces look nothing like the reference**
The scene prompt buried the likeness clause. Put "keep the face, spectacles and
features clearly recognisable" first, scene direction second. See `images.md`.

**Render is slow or runs out of memory**
Lower concurrency: `npx remotion render <id> out/x.mp4 --concurrency 4`. For
very long stories raise the heap:
`NODE_OPTIONS=--max-old-space-size=8192 npx remotion render ...`.

## Housekeeping

`public/**/*.wav`, `*.mp3`, `*.jpg` and `*.png` are gitignored: `story.json` is
the artefact worth committing, since it regenerates everything else. Never
commit `.env`, and never paste a key into `.claude/settings.local.json`
permission rules, where it would be stored in plain text.
