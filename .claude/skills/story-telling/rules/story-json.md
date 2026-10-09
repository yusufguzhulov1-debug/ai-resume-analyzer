---
name: story-json
description: The story.json schema, field by field, with a complete example
---

# story.json

One file describes a whole video. It lives at `public/<slug>/story.json` and is
validated by `src/lib/schema.ts` (zod) on both sides: the CLI refuses to
generate an invalid story, and `calculateMetadata` refuses to render one.

## Top level

| Field | Type | Notes |
|---|---|---|
| `slug` | lowercase-hyphen string | Folder under `public/`. Also the default output name. |
| `compositionId` | PascalCase string | Id in the Studio and in `remotion render`. |
| `orientation` | `landscape` \| `vertical` | 1920x1080 or 1080x1920. Drives image size and type scale. |
| `fps` | number | 30 unless there is a reason. |
| `title` | object | Opening card. `eyebrow`, `headline`, `subline`. |
| `voice` | object | `speaker`, `pace`, `temperature`, `languageCode`. |
| `style` | object | `artPrompt`, `accent`, `background`, `displayFont`, `textFont`. |
| `scenes` | array | One per voice file. See below. |
| `outro` | object or null | Silent closing card after the narration. |
| `references` | map | Name to local photo path, relative to the project root. |
| `music` | object or null | `file` in `public/<slug>/`, and `volume` 0 to 1. |

## Scene

| Field | Type | Notes |
|---|---|---|
| `id` | number | 0 based. Becomes `voice-<id>.wav`. |
| `narration` | string | 24 to 32 words. See `narration.md`. |
| `images` | array | One or two. Two cross fade inside the scene. |
| `stat` | object or null | `value` (digits) and `label` (upper case, under seven words). |
| `audioDurationInSeconds` | number | Written by the generator. Do not hand edit. |
| `durationInFrames` | number | Written by the generator. Do not hand edit. |

## Image

| Field | Type | Notes |
|---|---|---|
| `id` | number | Unique across the whole story. Becomes `image-<id>.jpg`. |
| `prompt` | string | Scene direction only. The house style is prepended automatically. |
| `reference` | string or array | Optional. One key from `references`, or several. Switches to the edit model. |

Image ids are global, not per scene, because the outro points at one by id and
because a frame can be reused in more than one scene.

Passing several references holds a likeness far better than one, because the
model sees the face from more than one angle:

```json
{ "id": 9, "reference": ["face", "portrait"], "prompt": "Keep his face ..." }
```

## Voice

```json
"voice": {
  "speaker": "shubh",
  "pace": 1.05,
  "temperature": 0.6,
  "languageCode": "en-IN"
}
```

- `pace` 0.5 to 2.0 on bulbul:v3. 1.05 is a natural narration pace. Raise it to
  fit more words into a fixed length, but past about 1.2 it starts to sound rushed.
- `temperature` 0.01 to 2.0, bulbul:v3 only. 0.6 is stable. Higher is more
  expressive and more likely to produce artefacts.
- `languageCode` is BCP-47: `en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `kn-IN`,
  `ml-IN`, `mr-IN`, `bn-IN`, `gu-IN`, `pa-IN`, `od-IN`. Match the font: use
  `AnekDevanagari` for Hindi or Marathi.

## Style

`artPrompt` is the single most important field for a coherent video. It is
prepended to every image prompt. Be explicit about medium, line, colour and
the people in frame:

```json
"artPrompt": "flat vector cartoon illustration, bold clean black outlines, vibrant saturated colours, expressive caricature faces, warm Indian skin tones, simple graphic shapes, subtle cel shading, modern editorial cartoon poster style, no text, no lettering, no numbers, no watermark, no signature"
```

Fonts available in `src/lib/fonts.ts`: `BricolageGrotesque`, `Poppins`,
`Inter`, `SpaceGrotesk`, `PlayfairDisplay`, `AnekDevanagari`. Add a family
there to make it selectable. `SpaceGrotesk` stops at weight 700, the others
carry 800.

## Minimal example

```json
{
  "slug": "repo-rate",
  "compositionId": "RepoRate",
  "orientation": "vertical",
  "fps": 30,
  "title": {
    "eyebrow": "IN SIXTY SECONDS",
    "headline": "What the repo rate really does",
    "subline": "The lever behind your EMI"
  },
  "voice": { "speaker": "shubh", "pace": 1.05, "temperature": 0.6, "languageCode": "en-IN" },
  "style": {
    "artPrompt": "flat vector cartoon illustration, bold outlines, vibrant colours, no text, no lettering",
    "accent": "#7FD1FF",
    "background": "#04060A",
    "displayFont": "BricolageGrotesque",
    "textFont": "Poppins"
  },
  "references": { "founder": "../photo/founder.jpg" },
  "scenes": [
    {
      "id": 0,
      "narration": "Every loan you hold is priced off one number that a committee in Mumbai resets a few times a year. Most borrowers never see it move.",
      "stat": { "value": "6.50%", "label": "REPO RATE, FEB 2026" },
      "images": [
        { "id": 1, "prompt": "A vast marble central bank hall seen from below, tall pillars, a single lit desk at the centre, cool morning light" },
        { "id": 2, "reference": "founder", "prompt": "Keep the face and features recognisable. Standing at a bank counter looking at a loan statement, warm interior light" }
      ]
    }
  ],
  "outro": {
    "headline": "One number, every EMI",
    "subline": "FOLLOW FOR MORE",
    "imageId": 1,
    "durationInFrames": 92
  },
  "music": null
}
```

## Editing an existing story

- Changed a `narration` string: `npm run generate -- --slug <slug> --only voice`.
  The voice file is regenerated only with `--force`, so delete that one
  `voice-N.wav` first, or pass `--force` and accept regenerating all of them.
- Changed an `image.prompt`: delete that `image-N.jpg` and rerun `generate`.
- Added a scene: give it the next `id`, give its images unused ids, rerun
  `generate`. Existing files are skipped, so only the new assets are billed.
- Changed `orientation` after generating: every image is now the wrong shape.
  Delete the jpgs and rerun, the voices are unaffected.
