---
name: images
description: FLUX 2 models on fal.ai, prompt recipe, reference photos, and what actually goes wrong
---

# Images

Two models, both wrapped in `cli/service.ts`, both selected from `.env`.

| Purpose | Env var | Default |
|---|---|---|
| Text to image | `FLUX_TEXT_MODEL` | `fal-ai/flux-2-pro` |
| Restyle a reference photo | `FLUX_EDIT_MODEL` | `fal-ai/flux-2-pro/edit` |

Other text to image endpoints, roughly best to fastest: `fal-ai/flux-2-max`,
`fal-ai/flux-2-pro`, `fal-ai/flux-2`, `fal-ai/flux-2-flex`,
`fal-ai/flux-2/turbo`, `fal-ai/flux-2/flash`. Each has a matching `/edit`
endpoint. Use `flash` while iterating on prompt wording, then switch back.

## Text to image

```ts
await generateImage({
  prompt,                              // artPrompt + scene prompt, joined by the generator
  path: "public/slug/image-1.jpg",
  imageSize: { width: 1920, height: 1080 },   // or 1080x1920 for vertical
  logs: true,
});
```

`image_size` takes an explicit `{width, height}` or a preset such as
`landscape_4_3`. The generator always passes explicit pixels matched to the
composition, so nothing is cropped at render time.

## Editing a reference photo

The edit model needs public URLs, so local files are uploaded to fal storage
first. `uploadToFal` does that once per reference and caches the URL.

Pass more than one photo of the same person when you have them. The model sees
the face from several angles and the likeness holds across far more frames:

```json
{ "id": 9, "reference": ["face", "portrait"], "prompt": "Keep his face ..." }
```

```ts
const url = await uploadToFal("../photo/portrait.png");
await editImage({
  prompt,
  imageUrls: [url],
  path: "public/slug/image-9.jpg",
  imageSize: { width: 1920, height: 1080 },   // "auto" keeps the input ratio
});
```

`"auto"` is accepted by the edit endpoint only, never by text to image. Prefer
explicit pixels: a portrait reference at `"auto"` produces a portrait frame,
which `objectFit: cover` then crops through the subject's face. The generator
tries explicit size first and falls back to `"auto"` only if the endpoint
rejects it.

## Prompt recipe

Final prompt = `style.artPrompt` + `". "` + the scene's `prompt`.

Keep the style string in `story.json`, never in the scene prompt. The scene
prompt describes subject, action, setting, light and mood, and nothing else.

```
subject doing something, in a place, with this light, this mood
```

Good: "A small neat stack of vintage Indian rupee notes and a few coins on a
wooden table beside a leather ledger and a fountain pen, single warm desk lamp,
dramatic shadows, sense of a tiny beginning."

## Likeness

To keep a real person recognisable through the edit model, say so explicitly:

> Keep his face, moustache, spectacles and Indian features clearly
> recognisable, but make him look younger, in his mid twenties, in a plain
> white shirt. Place him ...

Without that clause the model drifts to a generic face within one or two
sentences of scene description. One reference photo can drive many frames with
different age, wardrobe and setting: upload once, reuse the URL.

Never put a real person's name in a prompt. Either supply a reference photo the
user owns, or describe the person generically ("a veteran investor in a black
Nehru jacket").

## What goes wrong in practice

- **Garbled signage.** FLUX paints text-like shapes even with "no text, no
  lettering, no numbers" in the style string. Compose so boards, screens and
  posters sit at the frame edges where the crop and vignette hide them.
- **Western default faces.** Crowd and background characters drift western
  unless ethnicity is stated in the style string, not just the scene prompt.
- **Unprocessable Entity.** A transient fal error. The wrapper retries with
  backoff; a single retry usually clears it.
- **Aspect mismatch after an orientation change.** Images are generated at the
  composition size. Change `orientation` and every jpg is stale: delete them
  and rerun. Voices are unaffected.
- **Safety filter.** `FLUX_SAFETY_TOLERANCE` runs "1" strictest to "5" most
  permissive; the default is "2". Raise it only when a legitimate prompt is
  being blocked, and never to produce content of a real person that they did
  not consent to.

## How many images

Two per scene is the default: each gets half the scene, cross fades over 22
frames, and a slow Ken Burns push that alternates direction so consecutive
scenes do not feel mechanical. One image per scene is calmer and cheaper.
Three or more in a 10 second scene flickers.

At 12 images a 60 second story is the bulk of the cost. Draft the prompts, show
them to the user, then generate.
