# Style elements — the à-la-carte prompt library

Distilled from a real before/after CTR comparison ("Image 13", 2026-08: flat/low-contrast/no
hierarchy vs bold/high-contrast/hierarchical — the after-frame won ~4.4x on views) plus the
prompt language that actually survived render-verify loops on video-1. Every block below is
**copy-paste prompt text** with `<slots>`; compose only the blocks the interview selected.

**Creator calibration (2026-08): default text budget is MINIMAL.** The full layered kit
(headline + sticker + checkstrip + tag) was tried and rejected as too much text. High
contrast, vibrant color, and clear hierarchy stay always-on. Ask; don't stack.

---

## Base axes (always included)

Open the prompt with one of the environment blocks below, and close with:

> STYLE: bold, premium, clickable — high contrast, vibrant <accent>-on-<ground> energy, crisp
> edges, clear hierarchy, uncluttered; every text element perfectly spelled and razor sharp.

The identity block, always first:

> REFERENCE ROLES: Image 1 is the identity reference — render this exact man with an
> identical face, beard, hair and skin tone; do not stylize his face.

Face energy (pick per concept): *ecstatic* — "mouth wide open in a huge amazed grin, eyebrows
raised high, wide bright eyes, looking straight into the lens" · *natural-candid* — "big
genuine amazed open-mouthed grin, raised eyebrows, caught mid-moment". Hands only when they
have a job: "his right index finger pointing at <target>; that hand correctly formed with
five fingers; his left hand <rests on the desk>; no other hands anywhere."

## Environments

### dark-studio
> SETTING & LIGHTING: a dark, moody, softly blurred studio office — deep blacks, faint desk
> silhouettes — lit almost entirely by the <accent> energy glow <of the hero object>; a vivid
> <accent> rim light wraps his hair, cheek and shoulders so he sits inside the scene's grade.
> Sharp on his face and the hero; saturated, high dynamic range, cinematic.

### real-office (candid DSLR)
> A bright, authentic DSLR photograph used as a YouTube thumbnail, 16:9 — one genuinely
> captured, candid-looking moment in a real office. The photo looks completely real; only the
> overlay text is added.
>
> …and match the real office visible behind him in Image 1: the soft grey-blue wall and the
> tall green dracaena plant. [environment anchoring — keeps renders in HIS room, not a stock office]
>
> LIGHTING & CAMERA: soft natural window daylight, realistic white balance and skin tones,
> gentle shadows; shot like a candid 35mm photo at f/2.8, shallow depth of field, sharp on
> his face and the screen; natural, believable color grade — a real photo, not a composite.
> Warm skin tones preserved; the screen adds only a faint cool glow. [prevents color-cast hands]

### bright-graphic (the classic loud composite)
> A high-energy, photorealistic YouTube thumbnail, 16:9, in a bold saturated modern-tech
> style. …a deep <blue> softly blurred studio backdrop with a strong <accent> key-glow and a
> crisp warm rim light that separates and relights him so he sits naturally in the scene and
> matches its color grade. Shot on an 85mm lens at f/2, shallow depth of field, bokeh
> background, bright, high contrast.

## Text elements

### single-hook (default)
> TEXT: exactly ONE overlay element — "<WORD>" (characters <W-O-R-D>) in huge vivid-<accent>
> condensed capitals with a subtle grunge texture and a hard drop shadow, across the
> <top-left> — the single dominant focal element. Absolutely no other text, numbers, badges,
> strips or logos anywhere else in the image.

### tiered-headline
> TEXT: the headline is two stacked lines in the top-left corner. Line one: "<CONTEXT LINE>"
> (letters <spell each word>) in clean heavy white italic capitals, medium size. Line two,
> directly below and much bigger: "<POWER LINE>" (letters <spell>) in huge vivid-<accent>
> condensed capitals with a subtle grunge texture, a soft outer glow and a hard drop shadow —
> the largest text in the frame.

Context line = quiet setup (CREATE / MY CONTENT / I CLONED). Power line = the promise
(UNLIMITED / WRITES ITSELF / MYSELF). The color contrast IS the hierarchy.

### sticker (max 2 short words — long words garble)
> …a small tilted bright-yellow sticker badge with the words "<TXT>" (letters <spell>) in
> heavy black capitals with a red underline, and a short white hand-drawn arrow from the
> badge pointing at <the hero object>.

### checkstrip (3 benefits, 1–2 words each)
> Along the very bottom edge, one slim semi-transparent dark strip containing three small
> items, each item a green circular checkmark immediately followed by short white capitals:
> first checkmark then "<ONE>", second checkmark then "<TWO>", third checkmark then "<THREE>"
> — all three items get their own checkmark.

[the "each item… immediately followed by" phrasing fixed a dropped-checkmark render]

### brush-tag
> at the right end of the strip, a <green> brush-stroke tag with dark bold italic capitals
> "<TAG>" (letters <spell>).

Always close any text section with:
> Absolutely no other text, numbers or logos anywhere else in the image.

## Hero-object elements

### glow-burst
> a <accent> energy glow with fine light particles radiates from <the hero> and spills onto
> <the desk / the space between them>.

### results-fan (busy-frame risk — pairs best with full-kit, never with single-hook + props)
> a dynamic fan of <n> small rounded cards bursting outward from <the hero>, each card
> showing a different vivid image — <examples> — every card pure imagery only, with no
> lettering, no words and no logos inside any card. [the one earned negation]

### real-logo (extra --ref)
Pass the actual logo file; explicit refs REPLACE the default face kit, so include both:
`--ref media/library/faces/<face>.jpg --ref media/library/logos/<logo>.png`
> Image 2 is the <name> logo — reproduce it faithfully as <a glossy rounded-square app icon
> on the screen / the badge>, crisp and undistorted.
For realistic environments use the full-color logo asset, not a monochrome variant
(`media/library/logos/claude-1024.png` for Claude).

### real-app-screen (extra --ref)
Source the screenshot from the video itself: ffmpeg a frame out of the baked preview at the
app beat, crop to the window, save to `media/projects/<p>/<name>-ref.jpg` (committed,
reusable). Then:
> Image 2 is a web app interface — reproduce this exact app on the laptop screen: <describe
> layout + colors>. Keep the layout, colors and shapes faithful; all small interface text
> stays tiny and softly unreadable at this distance, and no large readable words appear on
> the screen.

Caveat: micro-text still garbles on close zoom (invisible at browse size). If it matters:
blur-text reroll, or perspective-warp the real screenshot onto the screen in post.

### hardware rule (always, any laptop/phone/monitor)
> a generic slim laptop with a plain dark bezel, no logos or lettering on the hardware.

## Clone / double (for self-facing concepts)
> BOTH men in this image are this exact man, with an identical face, beard, hair and skin
> tone. …his DIGITAL CLONE: the same man's face and build in three-quarter view — but clearly
> a hologram: translucent, tinted <accent>, built from fine glowing wireframe mesh,
> horizontal scanlines and drifting light particles, shoulders dissolving into particle
> streams. [material difference keeps it honest + prevents stranger-face]

## Composition recipes (proven full assemblies)

- **Bright-graphic + full-kit + real-logo** → `videos/video-1/packaging/thumbs/A2.txt`
- **Dark-studio outcome scene** (self-typing laptop) → `…/B.txt`
- **Dark-studio clone face-off** → `…/C.txt`
- **Real-office + full-kit + price-tag prop** → `…/D2.txt`
- **Real-office + single-hook + real-app-screen** → `…/D3.txt`

Read one before assembling a new prompt; they encode the hierarchy language (three focal
steps: headline → hero → face) that keeps layered frames from going busy.
