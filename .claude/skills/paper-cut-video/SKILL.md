---
name: paper-cut-video
description: Create or edit vertical Chinese paper-cut and paper-collage explainer videos with script-driven, content-matched paper characters; separate background, rear, hero, and foreground layers; staged character entrances; cropped screen recordings; semantic Chinese captions; Remotion motion graphics; and a paper-cut outro. Use this skill for 剪纸风视频、纸片分层动画、国风剪纸讲解、人物剪纸动画、真人口播加录屏、右下角圆形画中画、剪纸流程图、剪纸片头片尾, or when converting an educational or AI tutorial into a red-and-ink-wash paper world.
---

# Paper Cut Video

Build a paper-cut explainer from the narration outward. Treat characters and environments as the primary storytelling system. Use Remotion to animate the designed layers and add functional text; do not substitute a stack of cards for character and scene design.

Use `paper-collage-ad` instead when the user wants a narrative product advertisement built around commercial keyframes and brand assets.

## Required outcome

When the user asks for a finished video, deliver:

1. A locked narration script split into semantic beats.
2. A shot plan and character bible describing who appears, why, facing direction, action, prop, scale, and layer.
3. Separate approved assets for the people-free background, rear characters, hero characters, foreground characters, and props.
4. Static scene boards that prove hierarchy, eye lines, ground lines, and occlusion before animation.
5. An editable Remotion or equivalent motion project with layered character animation.
6. Final narration, matching semantic Chinese captions, a rendered H.264/AAC MP4, a contact sheet, and a QC report.

Do not stop at a style prompt or storyboard when the user asked for an edited MP4.

## Inputs

Reuse existing project material before asking questions:

- Topic, draft, transcript, or presenter recording.
- Screen recording when the tutorial demonstrates software or files.
- Reference image or prior episode that establishes the paper language.
- Brand name, closing line, or recurring character identity when already established.
- Existing narration audio and word timestamps when available.

Ask only for a missing input that materially changes the result. Never package private presenter footage, voice samples, desktop screenshots, personal avatars, or credentials inside the installed skill.

## Read the right references

- Read `references/character-and-scene-design.md` before generating any background or character.
- Read `references/scene-routing.md` before deciding shot types or filling negative space.
- Read `references/visual-system.md` before laying out a paper-cut scene.
- Read `references/remotion-template.md` before adapting the layered character template.
- Read `references/editing-and-captions.md` before speech edits, subtitles, retiming, or assembly.
- Read `references/quality-control.md` before delivery.

## Workflow

### 1. Lock the narration copy

Start with the complete wording. If the input is a presenter recording, transcribe it and mark clear mistakes, abandoned starts, duplicate takes, and distracting pauses. Preserve the user's meaning and speaking style. Produce a final script split into scene-sized semantic beats before designing visuals.

Do not generate final TTS yet. Use the locked wording to decide what each shot must communicate. The same wording will later become the subtitle source of truth.

### 2. Design shots and characters from the script

For every beat, choose a shot size, environment, character, action, prop, and layer plan. Design a recurring hero when continuity helps, but change the pose and prop to match the sentence. An abstract topic still needs a concrete visual role: for example, explain an Agent as a dependable paper intern who reads a task slip, searches, uses tools, checks results, and asks for approval.

Create scene-plan entries shaped like:

```json
{
  "beat": "Agent checks the result and continues",
  "shot": "medium",
  "environment": "paper workshop",
  "hero": {
    "identity": "AI intern",
    "facing": "right",
    "action": "compare a checklist with the finished object",
    "prop": "clipboard"
  },
  "layers": ["background", "rear", "hero", "foreground"],
  "support_text": "观察 → 计划 → 行动 → 检查"
}
```

Make cards secondary. Use them for an exact command, path, short definition, or step label that the characters and environment cannot show clearly.

### 3. Generate separate scene assets

Generate the people-free background after the shot plan is fixed. Then generate the character pose sheet or individual poses from a stable character brief. Keep face, hair, costume, palette, and paper treatment consistent across poses.

Require full bodies or intentionally framed busts, explicit facing direction, readable hands and props, a simple removable background or real alpha, no text, no watermark, and no unrelated scenery. Extract every person and prop to an independent transparent PNG. Never bake people into the background plate.

Keep project-specific people and generated assets in the project directory. Record the prompt, model, date, source, and intended scene in an asset manifest.

### 4. Approve static staging before motion

Build a still frame for every shot. Confirm that the hero is largest and easiest to read, supporting characters do not hide faces, hands, or props, feet share a believable ground line, and all eye lines point into the scene.

Build depth from this bottom-to-top order:

1. Background plate.
2. Rear people and distant architecture.
3. Midground support people and props.
4. Hero character.
5. Foreground people, paper scraps, or framing elements.
6. Captions and essential labels.

Do not animate until the still composition passes at phone size.

### 5. Animate the paper layers

Give each depth class a different motion character. Keep the background to a slow 1% push or drift. Move rear people only slightly. Give the hero the largest entrance distance, a small scale settle, and a clear landing. Bring support and foreground characters from the sides with medium travel.

Stagger entrances: hero first, support cast next, crowd or foreground last. Derive every motion from frames. Use subtle frame-based idle movement only after a character settles; avoid identical bobbing on every layer.

### 6. Build the Remotion project

Scaffold the starter:

```bash
node <SKILL_DIR>/scripts/init-project.mjs --output ./paper-cut-remotion
cd ./paper-cut-remotion
npm install
npm run start
```

Start concept scenes with `PaperCharacterScene`, which accepts a separate background and per-character layer, position, width, entrance, timing, and rotation. Use `PaperExplainer` for cropped software demonstrations with a circular presenter PiP, `PaperFlow` for diagrams that truly need nodes and arrows, and `PaperOutro` for the close.

Keep Chinese labels as real HTML/React text. Preserve a readable hold after the final reveal.

### 7. Generate final narration and retime scenes

After the visual scenes work, generate or select the final narration. When the user requests Volcengine Doubao TTS, require their own `VOLCENGINE_TTS_APP_ID`, `VOLCENGINE_TTS_ACCESS_TOKEN`, and `VOLCENGINE_TTS_VOICE_TYPE` in the local environment. Never hard-code, log, echo, package, or commit these values.

Generate one audio file per semantic scene when practical. Use the measured audio duration to set each composition length, entrance delays, and reading holds. Do not hard-cut inside a sentence. When the project already has approved presenter audio, use that track instead of synthesizing a replacement.

### 8. Build captions from the same script

Use the locked narration text as caption wording. Measure timing from word timestamps on the final audio; use ASR only for timing, never to rewrite the approved words.

```bash
node <SKILL_DIR>/scripts/semantic-captions.mjs \
  --input ./transcript.json \
  --output ./captions.srt
```

Review every cue with `references/editing-and-captions.md`. Never leave `吗`, `呢`, `吧`, `对吧`, or a single punctuation mark as its own cue. Keep captions in one bottom rail and prevent them from fighting with scene text.

### 9. Assemble sound and picture

Render scenes separately, then assemble them. Default delivery is 1080×1920, 30 fps, H.264 High, AAC stereo at 48 kHz. Keep narration dominant, background music below speech, and entrance effects matched to the actual entrance frame.

If the user requests faster pacing, use pitch-preserving audio tempo. Treat 1.10× as a safe whole-video adjustment and review intelligibility before exceeding about 1.12×.

### 10. Validate before delivery

Run:

```bash
node <SKILL_DIR>/scripts/verify-video.mjs ./final.mp4 --width 1080 --height 1920 --fps 30
```

Inspect a contact sheet containing every scene and character pose, the last spoken sentence, the first outro frame, and the final frame. Delivery is complete only when character crops, facing directions, proportions, occlusion, staggered entrances, subtitle wording, final-word tail, streams, and full-file decode all pass.

## Project conventions

- Keep generated projects, characters, voices, and media outside the skill directory.
- Preserve original source media and generated asset prompts.
- Keep background, rear, midground, hero, foreground, cards, captions, and outro layers separable.
- Use project-relative media paths inside a generated Remotion project.
- Cache scene renders and invalidate only scenes whose inputs changed.
- Never redistribute reference-article images or unlicensed third-party characters.

## Resources

- `assets/paper-bg-vertical.png` — neutral 9:16 red and ink-wash paper field.
- `templates/remotion/` — Remotion starter with layered character, screen/PiP, flow, and outro scenes.
- `scripts/init-project.mjs` — copies the starter and background into a new project.
- `scripts/semantic-captions.mjs` — creates first-pass semantic SRT cues from word timestamps.
- `scripts/verify-video.mjs` — validates streams, dimensions, frame rate, duration agreement, and full decode.
- `references/character-and-scene-design.md` — script-to-character, asset, staging, depth, and motion rules.
- `references/visual-system.md` — palette, paper materials, safe zones, typography, and cutout treatment.
- `references/scene-routing.md` — content-to-shot routing and card decisions.
- `references/editing-and-captions.md` — speech, subtitle, assembly, and pacing rules.
- `references/remotion-template.md` — starter usage and extension points.
- `references/quality-control.md` — final character, visual, audio, and technical checklist.
