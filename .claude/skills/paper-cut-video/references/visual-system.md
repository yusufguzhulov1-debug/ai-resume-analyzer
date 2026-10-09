# Visual system

## Concept

The frame should feel assembled by hand from warm paper, red torn scraps, ink-wash landscape fragments, printed labels, and content-matched cut-out characters. It is a staged paper world, not a flat vector UI with a paper texture pasted behind it.

## Palette

| Role | Color |
| --- | --- |
| Vermilion paper | `#a92e22` |
| Dark red ink | `#6f1915` |
| Main ink | `#241d18` |
| Warm paper | `#f1e4c7` |
| Ochre tape | `#b18445` |
| Blue concept accent | `#78a8b8` |
| Mauve concept accent | `#b68bab` |
| Green completion accent | `#7ca77c` |

Keep the background mostly paper and ink. Use red for hierarchy and stamps, then one secondary accent per diagram level.

## Materials

- Use real raster paper grain or generated paper assets for the field and major cutouts.
- Give cutouts a warm 3–6 px keyline when they touch the background.
- Main cards use an irregular polygon clip and a visible paper shadow: approximately `16px 18px 0 rgba(52,25,16,.18)` plus a soft shadow.
- Tape pieces may sit at 6–15° rotations. Keep them sparse and away from text.
- Use halftone only as a supporting print texture, never over small Chinese text.

## Characters and depth

Make at least one character carry each conceptual scene unless the sentence genuinely needs only a diagram or screen recording. Design the character from the narration before generating the asset. Keep backgrounds free of people and keep every person, prop, and foreground piece on a separate transparent layer.

Stack full paper scenes from background to rear cast, support cast, hero, foreground, captions, and labels. Use scale, eye line, ground line, overlap, a light paper keyline, and a darker offset shadow to create depth. Do not rely on a title card to provide the main subject.

Read `character-and-scene-design.md` for identity, prompt, staging, and movement rules.

## Portrait 1080×1920 layout

Default hybrid scene zones:

| Zone | Suggested box | Purpose |
| --- | --- | --- |
| Header | x 46–1034, y 34–116 | Episode/chapter micro-label |
| Screen frame | x 36–1044, y 180–1020 | Cropped app, editor, folder, or terminal |
| Support card | x 70–650, y 1050–1310 | Current command, path, definition, or 2–3 steps |
| Circular PiP | x 680–1020, y 1300–1640 | Presenter, 300–340 px diameter |
| Subtitle rail | x 70–1010, y 1640–1820 | One or two semantic lines |
| Footer texture | y 1820–1920 | Decorative paper only; no required information |

The support card is the first solution when the area between the screen and presenter feels empty. It must add information. Good examples:

- Command card: `/skills` + `手动调用当前 Skill`.
- Path card: `.codex/skills/<name>/SKILL.md`.
- Three-step strip: `识别 → 读取 → 执行`.
- Definition card: one bold term plus one short sentence.

Use only one support-card idea at a time. Let it enter when the narration names the idea and leave before the next idea.

## Screen recording

- Crop to the application window or exact content region; never show desktop wallpaper.
- Keep the cursor visible only when it clarifies an action.
- Frame the crop with 12–18 px warm paper and a 3–6 px dark red outer edge.
- Enlarge important UI text before adding decoration.
- If the original screen is too dense, use a callout card rather than shrinking the screen further.

## Character and presenter treatment

- Full-screen presenter scenes may stay photographic when used as an intentional contrast.
- Hybrid scenes use a circular video PiP with a 10–14 px warm-paper ring.
- Full paper scenes use project-specific transparent characters whose identity, pose, direction, and prop match the sentence.
- Give generated cutouts a 5–10 px light paper keyline plus an offset dark shadow. Preserve transparent padding around both.
- Keep subtle idle movement under 6 px. Give different layers different phases and avoid perpetual synchronized bobbing.

## Typography

- Chinese headlines: Songti/STSong or another sturdy serif, 60–96 px.
- Chinese support cards: 32–46 px, bold, 1.2–1.35 line height.
- Commands and paths: Menlo or another monospaced face, 20–30 px.
- Captions: heavy sans/Heiti, 52–64 px, high contrast, rounded dark plate if needed.
- Micro labels: 16–22 px, uppercase Latin with 2–5 px tracking.

## Motion character

- Elements enter as physical paper: short translation, 1–4° rotation correction, and a damped scale settle.
- Bring the hero in first, then stagger support and rear/foreground layers by 6–12 frames.
- Give the hero the largest readable entrance; keep rear cast and background motion restrained.
- Draw arrows over 10–18 frames, then hold.
- Use deterministic motion; no unseeded randomness.
- Keep a 12–24 frame reading hold after the final reveal.

## Outro

Use a 3–5 second close. Reuse the background, presenter cutout, a torn paper identity card, one CTA, and a red stamp. The last frame should remain readable for at least one second.
