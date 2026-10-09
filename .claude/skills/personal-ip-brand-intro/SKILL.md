---
name: personal-ip-brand-intro
description: Create original commercial-quality personal-IP brand intro videos with typography, original vector illustrations, optional user-provided images, and either uploaded-music synchronization or a self-designed silent beat grid. Use for 16:9, 9:16, or 1:1 creator openers, kinetic identity films, animated brand title sequences, and HyperFrames or Remotion production that must be designed for each brand rather than filled into a fixed template.
---

# Personal IP Brand Intro

Build a short identity film in which typography, optional images, original illustrations, graphics, and cuts express one creator's brand. Treat every request as a new design system. Use demonstration projects only to validate the workflow, never as templates.

## Hard Rules

- Do not require a logo, portrait, photo, or character image. Support text-and-illustration-only work.
- Use an uploaded image only when the user provides it or explicitly approves generation.
- Preserve every uploaded source unchanged; create separate working copies.
- Use an uploaded track when provided. When none is provided, design a silent beat grid instead of searching for or silently substituting music.
- Keep every essential brand message readable during a clean hold.
- Do not reuse demonstration-brand copy, palettes, layouts, scene orders, timing maps, portraits, logos, or motifs.
- Do not publish, upload, overwrite, or formally render without the required user authorization.

## Route the Work

- Read `references/intake-schema.md` before writing the brief or `brand-spec.json`.
- Read `references/rhythm-routing.md` to choose uploaded-music or designed-beat-grid timing.
- Read `references/music-upload-workflow.md` only when the user provides audio or a video containing audio.
- Use `$music-to-video` only for uploaded-track analysis.
- Use `$hyperframes` as the entry point for HyperFrames production, then load its creative, animation, and CLI skills as needed.
- Use Remotion for an explicitly requested React composition or dual-engine delivery.
- Use `$imagegen` only when the user asks for a new visual asset or accepts generation as a proposed fallback.

## Workflow

### 1. Collect Identity-Critical Inputs

Require:

- brand name
- creator name, handle, or public role
- creator category
- two to four services or content pillars
- tagline or permission to develop one
- aspect ratio and desired duration

Treat images, logos, and music as optional. Ask only for missing identity-critical information. Infer reversible creative details when the user requests autonomous production. Never invent certifications, results, clients, credentials, or product claims.

### 2. Select the Visual Mode

Record one mode in `brand-spec.json`:

- `text-illustration`: kinetic typography plus original SVG/CSS/vector illustration; no external image required
- `image-assisted`: one or more user-provided portraits, character images, product images, or logos carry identity
- `mixed`: typography, original illustration, and user-provided images share the system

For `text-illustration`, invent category-native visual metaphors rather than generic decorative stickers. For image modes, make the supplied media part of the identity story rather than a corner decoration.

### 3. Select the Timing Mode

Choose exactly one route:

#### Uploaded music

Preserve the upload in `assets/source/`, create a separate working track, and follow `references/music-upload-workflow.md`. Analyze the final working track with `$music-to-video`. Treat its `audiomap.json` as the only timing authority.

#### No uploaded music

Choose a BPM and accent pattern from brand personality and communication density. Create the canonical silent beat grid:

```bash
node scripts/create-beat-map.mjs \
  --duration 7 \
  --bpm 116 \
  --output audiomap.json
```

Record `music.mode` as `none` and `timing.mode` as `designed-beat-grid`. Do not add, generate, search for, or recommend music unless the user separately asks for it. A silent video can still have precise visual rhythm.

### 4. Establish the Production Mode

Default to showing one recommended visual direction and a concise storyboard before animation and formal rendering. If the user explicitly asks for autonomous execution, post the direction as a progress update and continue.

Support `hyperframes`, `remotion`, or both. Use HyperFrames when the user does not choose. Build both only when dual-engine delivery is explicitly requested.

### 5. Normalize the Brand Brief

Create `brand-spec.json` from the matching example:

- `assets/brand-spec.example.json` for text-and-illustration with no music
- `assets/brand-spec.uploaded.example.json` for user images and uploaded music

Validate:

```bash
node scripts/validate-brand-spec.mjs /absolute/path/to/brand-spec.json
```

### 6. Map Rhythm to Meaning

Use the canonical `audiomap.json`, whether analyzed or designed, to map:

- hook: interrupt attention
- identity: reveal creator, category, or brand
- proof: show services, process, tools, or knowledge
- point of view: land the tagline or belief
- ownership: resolve the final brand lockup

Do not cut on every beat. Use strong accents for hierarchy changes, weaker accents for secondary motion, and deliberate holds for reading.

### 7. Create an Original Visual System

Read `references/originality-rules.md`. Define a one-sentence visual thesis and a seven-part fingerprint:

- composition grammar
- type personality
- graphic or illustration vocabulary
- image/subject treatment
- color logic
- transition family
- rhythm behavior

Generate three internal directions: category-native, personality-native, and audience-native. Build the option with the clearest brand recognition, strongest timing fit, and lowest similarity to prior work.

### 8. Write the Beat-Synced Storyboard

Read `references/storyboard-contract.md`. For each scene record:

- exact time range from `audiomap.json`
- communication goal
- exact on-screen copy
- text, image, or illustration role
- dominant motion
- rhythmic anchor
- exit or handoff

Keep essential text complete. Cropping may occur only during an intentional entrance or exit. Give the final lockup a clean readable hold of roughly 0.8–1.2 seconds.

### 9. Build the Composition

Create an isolated project and preserve all original media.

For HyperFrames:

1. initialize or resume a clean project
2. derive all timing from the canonical map
3. implement seek-safe, frame-derived animation
4. run `hyperframes check` before rendering

For Remotion:

1. register one explicit composition per intro
2. derive timing from `useCurrentFrame()` and composition FPS
3. attach `<Audio>` only for approved uploaded music
4. keep copy, duration, timing anchors, and creative thesis aligned with the brand spec

When building both engines, share the brand spec, timing map, storyboard, copy, duration, and creative thesis. Do not mechanically copy engine-specific implementation details.

### 10. Verify and Render

Read `references/qa-checklist.md`. Validate layout, motion, contrast, exact text, optional image treatment, rhythm, final metadata, representative frames, and originality.

Verify each final MP4:

```bash
node scripts/verify-render.mjs \
  /absolute/path/to/output.mp4 \
  /absolute/path/to/brand-spec.json
```

Inspect frames extracted from the rendered MP4, not only browser previews. Render only after blocking checks pass and the user has authorized formal rendering.

## Deliver

Return:

- final MP4 or dual-engine outputs
- `brand-spec.json`
- canonical `audiomap.json`
- beat-synced storyboard
- source project
- representative frames or contact sheet
- concise QA summary

For uploaded music, identify the exact user source and selected time range without redistributing the source separately. For designed beat grids, state the chosen BPM, accent logic, and that the output is silent.
