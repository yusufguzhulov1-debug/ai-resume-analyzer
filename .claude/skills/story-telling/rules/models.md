---
name: models
description: Every model the pipeline can use, where it is configured, and how to choose
---

# Models

Nothing is hardcoded. Every model id is read from `.env` by `cli/env.ts` and
pushed into `cli/service.ts` through `setModels()`. Changing a provider version
is an edit to one line of `.env`.

| Purpose | Variable | Default |
|---|---|---|
| Narration | `SARVAM_MODEL` | `bulbul:v3` |
| Default voice | `SARVAM_SPEAKER` | `shubh` |
| Default language | `SARVAM_LANGUAGE` | `en-IN` |
| Text to image | `FLUX_TEXT_MODEL` | `fal-ai/flux-2-pro` |
| Reference restyle | `FLUX_EDIT_MODEL` | `fal-ai/flux-2-pro/edit` |
| Image safety filter | `FLUX_SAFETY_TOLERANCE` | `2` |
| Image format | `FLUX_OUTPUT_FORMAT` | `jpeg` |
| Story drafting | `OPENAI_MODEL` | `gpt-4.1` |

`story.json` overrides `.env` for anything it sets: `.env` holds the defaults,
the story holds the decisions for that particular video.

## Narration, Sarvam AI

| Model | Voices | Notes |
|---|---|---|
| `bulbul:v3` | 37 | Default. `temperature`, 2500 characters, 30+ voices. |
| `bulbul:v2` | 7 | Legacy. `pitch` and `loudness`, 1500 characters. Different voice names. |

Switching to v2 also means switching the speaker: see `voices.md`.

## Images, FLUX 2 on fal.ai

Text to image, roughly best to fastest:

| Model | Use for |
|---|---|
| `fal-ai/flux-2-max` | Hero frames, thumbnails, anything held on screen long |
| `fal-ai/flux-2-pro` | The default. Strong quality at a sane price |
| `fal-ai/flux-2` | Base model, cheaper than pro |
| `fal-ai/flux-2-flex` | When you want to tune steps and guidance |
| `fal-ai/flux-2/turbo` | Bulk background frames, softer detail |
| `fal-ai/flux-2/flash` | Prompt iteration only, then switch back |
| `fal-ai/flux-2/klein/9b`, `.../klein/4b/base` | Small open models |

Every one of those has a matching `/edit` endpoint for reference photos:
`fal-ai/flux-2-pro/edit`, `fal-ai/flux-2-max/edit`, `fal-ai/flux-2/turbo/edit`,
and so on. Always pair the edit endpoint with the text model, otherwise the
reference frames and the scenery frames end up in visibly different styles.

There are also LoRA gallery endpoints such as
`fal-ai/flux-2-lora-gallery/digital-comic-art` and
`.../ballpoint-pen-sketch`. These lock a look far harder than a prompt can, so
they are worth it when a series needs to be visually identical across many
videos.

Workflow that saves money: set `FLUX_TEXT_MODEL=fal-ai/flux-2/flash`, generate
all images, look at them, fix the prompts in `story.json`, then delete the jpgs,
switch back to pro or max and regenerate.

## Drafting, OpenAI

Any chat completions model with JSON mode. Verified present on this account at
the time of writing:

```
gpt-5.5      gpt-5.5-pro   gpt-5.4      gpt-5.4-mini  gpt-5.4-nano
gpt-5.2      gpt-5.1       gpt-5        gpt-5-mini    gpt-5-nano
gpt-4.1      gpt-4.1-mini  gpt-4.1-nano gpt-4o        gpt-4o-mini
o3           o3-mini       o4-mini
```

Re-check rather than trusting this list:

```bash
curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" \
  | python3 -c "import sys,json;print('\n'.join(sorted(m['id'] for m in json.load(sys.stdin)['data'])))"
```

Drafting is one call per story and is the cheapest step by far, so a stronger
model here is good value. It is also entirely optional: writing `story.json`
by hand produces better narration and removes any risk of invented facts.

## Adding a provider

`cli/service.ts` is the only file that talks to an API. To swap in a different
TTS or image provider:

1. Add a wrapper function with the same shape as `generateVoice` or
   `generateImage`, writing to the same output path.
2. Add its model id to the `models` object and to `cli/env.ts`.
3. Document it in `.env.example`.

Nothing in `src/` changes: the composition only ever reads `story.json` and the
files in `public/<slug>/`.
