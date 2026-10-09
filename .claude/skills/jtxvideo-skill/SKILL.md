---
name: jtxvideo-skill
description: >
  Produce AI-finance and industry-analysis talking-head videos from recorded口播视频
  using a staged workflow: preprocess, transcribe SRT, wait for confirmation,
  analyze structure, storyboard, design, HyperFrames render, review, and export 2K 60fps.
  Preserve the source orientation unless the user explicitly asks to change it. Use when
  the user asks to process口播视频, make同款剪辑风格, generate AI金融黑金商务视频, or says
  to use jtxvideo-skill. Do not use for generic video editing that skips SRT/storyboard approval.
---

# JTX Video Skill

## Purpose

Turn a recorded Chinese talking-head video into the user's standard AI-finance Douyin video:

- the speaker is the visual anchor
- motion graphics explain finance/AI/product events
- the style is black-gold business, not flashy template editing
- the workflow is staged and reviewable
- final export includes a 2K 60fps version for publishing
- the source orientation is respected: horizontal input stays horizontal unless the user asks otherwise

## Non-Negotiable Workflow

Never jump straight from source video to a finished edit. Move in this order:

1. **Create project folder**
   - Use `hyperframes-runs/<project-slug>/`.
   - Keep all generated files inside the project folder.

2. **Preprocess source video**
   - Convert the input video to stable H.264 at 30fps with fixed keyframes.
   - Default command shape:
     ```bash
     ffmpeg -i input.mp4 -c:v libx264 -g 30 -keyint_min 30 -r 30 output_keyed.mp4
     ```
   - Save as `workflow/01_preprocessed_keyed.mp4` and copy/use as `assets/talk-main-keyed.mp4`.
   - Immediately run `ffprobe` and record source orientation:
     - `width > height` = horizontal workflow
     - `height > width` = portrait workflow
   - Save the orientation decision in the project notes / `design.md`. Do not choose layout rules before this decision is made.

3. **Extract audio and transcribe**
   - Extract clean audio, usually `workflow/01_audio_16k.wav`.
   - Use a Chinese-capable high-accuracy transcription model. Do not use `.en` Whisper models for Chinese.
   - First output to the user must be the SRT file path and content summary only.
   - Save SRT as `workflow/01_audio_16k.srt`.

4. **SRT 文件确认**
   - Do not analyze the script, storyboard, or render before the user confirms SRT.

5. **Analyze content structure**
   - Segment the transcript into content types:
     - 开场钩子
     - 痛点呈现
     - 正误对比
     - 流程清单
     - 方法论讲解
     - 案例 / 数据
     - 行动号召
     - 金融观点 / 市场判断
     - AI工具实测 / 产品事件
   - Save as `workflow/05_content_structure_for_review.md`.
   - Ask the user to review.

6. **文案结构确认**
   - Do not generate storyboard until confirmed.

7. **Generate storyboard**
   - Use `templates/storyboard-template.md` as the schema.
   - Include time range,口播内容,文案类型,画面策略,动效元素,音效建议,审核关注点.
   - Before writing the storyboard, branch by source orientation:
     - Horizontal: material-first split layouts are allowed for long evidence/chart explanations.
     - Portrait: the speaker must remain on screen; materials and motion graphics attach as overlays above the speaker.
   - Save as `workflow/06_storyboard_for_review.md`.
   - Ask the user to review.

8. **分镜表确认**
   - Do not generate HyperFrames code before storyboard confirmation.

9. **设计确认并生成项目 design.md**
   - Copy `templates/design-default.md` into the project as `design.md`.
   - Adapt only what the current video needs.
   - Keep the approved defaults unless the user asks otherwise.

10. **Generate HyperFrames project**
    - Use one continuous talking-head video as the base layer.
    - Do not repeatedly mount many slices of the same MP4; it can cause gray preview, freezing, or the speaker disappearing.
    - Put captions and visual explanations in separate timed overlay layers.
    - Prefer concise dynamic keywords over dense cards when there is no external material to show.
    - Use real source images/charts when they are available and relevant; do not redraw unclear symbolic diagrams.
    - Apply the orientation-specific layout rules:
      - Horizontal: may use left-material / right-speaker split scenes when materials need sustained explanation.
      - Portrait: never switch to a full-screen material scene; the speaker stays visible and materials/dynamic text are overlay layers attached to the speaker shot.
    - Main video must be muted; use a separate `<audio>` track.

11. **最终视觉确认**
    - Generate preview/review renders.
    - Use screenshots/contact sheets for visual checks.
    - Apply user feedback on subtitle height, size, transparency, person brightness, card placement, and motion restraint.

12. **Final export**
    - Preserve the source orientation unless the user explicitly asks to convert.
    - Horizontal final version: `2560x1440 / 60fps`.
    - Portrait final version: `1440x2560 / 60fps`.
    - Render a high-quality master, then generate the final 2K 60fps publishing file.
    - Re-mux full original audio after HyperFrames rendering.
    - Verify with `ffprobe`.

## Editing Rules Learned From Review

Use these rules before writing the storyboard and again before rendering:

1. **Find the real topic first**
   - Do not animate every sentence.
   - Extract only the few beats that carry the video: event, key data, core contrast, bottleneck, conclusion.
   - For industry-chain videos, prioritize the event trigger, market-size numbers, margin/comparison numbers, and the true bottleneck.

2. **Use fewer, sharper words**
   - If there is no source material, show only dynamic keywords or numbers.
   - Do not use generic cards just to fill the screen.
   - A key overlay should usually be one line, one number, or one contrast.
   - Avoid stacking many explanatory lines; if everything is highlighted, nothing is highlighted.

3. **Use source material as the main visual when available**
   - Horizontal: if a chart/table/image is the evidence, make the material readable and visually dominant.
   - Portrait: source material can be shown, but only as an overlay on top of the speaker shot unless the user explicitly asks for a full-screen insert.
   - Do not crop important parts of the material.
   - Do not cover the material with duplicate text or redundant labels.
   - Put only the key prompt above or near the material.

4. **Decide horizontal vs portrait before layout**
   - Always inspect `width` and `height` before storyboard/design/code.
   - Do not reuse horizontal split-screen logic on portrait footage.
   - Do not reuse portrait overlay logic when a horizontal video needs readable long-form evidence.
   - Record the decision in `design.md` with the chosen canvas and export target.

5. **Portrait layout rules**
   - The speaker must remain visible for the entire video.
   - Materials, charts, screenshots, and keywords are overlay explanations attached to the speaker shot.
   - Do not create full-screen material takeovers in portrait unless the user explicitly asks.
   - If a source image is provided for a portrait video, use it briefly as an upper overlay, side overlay, or small evidence strip; do not let it replace the speaker.
   - Do not cover eyes, mouth, or key facial expression areas.
   - Prefer top/upper-side overlays for keywords and data; keep bottom reserved for subtitles and Douyin-safe UI.
   - If a phrase's visual emphasis feels like a distracting popup, remove that emphasis and keep the phrase in the full subtitle only.

6. **Horizontal split layout for long material explanation**
   - For horizontal videos with important material, use a two-panel layout:
     - left: large material panel
     - right: synchronized speaker panel
   - Keep material and speaker panels aligned in height.
   - Leave enough gap between title, panels, and subtitles.
   - The material is the primary visual in these sections; the speaker supports the explanation.

7. **Static blurred background in split scenes**
   - When the speaker is shown in a right-side panel, the background behind the panels must not be a live moving copy of the speaker.
   - Use a still frame from the source video as a blurred, darkened background.
   - Only the speaker panel should move.
   - This prevents the viewer from seeing two moving speakers at once.

8. **Animation must match the spoken timing**
   - Do not reveal a number or conclusion before the matching subtitle/口播.
   - Tie overlays to the exact SRT segment that says the key phrase.
   - Example: `$40 -> $60` should appear when the speaker says "从40美金涨到60美金", not when earlier context begins.

9. **Text style**
   - Use solid, heavy, high-contrast Chinese typography for key statements.
   - Avoid hollow, striped, folded, decorative, or textured type unless explicitly requested.
   - Use gold only for the most important number or conclusion.

10. **Subtitles stay independent**
   - Subtitle bars must not overlap material panels or speaker panels.
   - In horizontal split scenes, reserve a clear bottom subtitle band below the main panel.
   - In portrait scenes, subtitles remain the base layer of comprehension; overlays must not compete with the subtitle bar.
   - Subtitle background should be translucent, not fully opaque black.

11. **Render stability**
   - Use one continuous main video as the base.
   - For picture-in-picture speaker panels, prefer pre-cut speaker clips as root-level media layers controlled by opacity.
   - Avoid dynamically creating nested video elements inside timed HTML scenes.
   - Prefer local bundled scripts such as `assets/gsap.min.js` over CDN scripts for renders.
   - After rendering, re-mux full original audio and verify that audio duration is close to video duration.

## Default File Contract

Use this structure:

```text
hyperframes-runs/<project-slug>/
  assets/
    talk-main-keyed.mp4
    talk-main-audio.m4a
  workflow/
    01_preprocessed_keyed.mp4
    01_audio_16k.wav
    01_audio_16k.srt
    05_content_structure_for_review.md
    06_storyboard_for_review.md
  templates/            # optional project-local copies
  design.md
  index.html
  renders/
    review.mp4
    contact-sheet.jpg
    preview-frame.jpg
    final-2k60.mp4
```

## Visual Defaults

Use `templates/design-default.md` as the source of truth for:

- AI金融黑金商务风
- transparent, readable subtitle bar
- bright speaker/person layer
- concise dynamic keywords and restrained motion
- material-first split layout when charts/tables/images are important
- portrait overlay layout when the source video is vertical
- no noisy gold line or flashy decoration
- Douyin-safe subtitles

## Quality Gates

Before telling the user a render is ready:

- Run `npx hyperframes validate`.
- Run `npx hyperframes inspect --samples 12` or denser for risky layouts.
- Use `npx hyperframes snapshot --at ... --describe false` for exact timestamps that received feedback.
- Run `ffprobe` on final MP4.
- Confirm video stream dimensions, frame rate, and duration.
- Confirm audio duration is complete and close to video duration.
- Generate at least one preview frame or contact sheet.
- For split scenes, inspect a frame while the section is active and confirm the blurred background is static.
- For portrait scenes, inspect frames where materials appear and confirm the speaker remains visible.
- For timed key numbers, inspect one frame before the cue and one frame after the cue.
- For any user-reported flicker/popup issue, extract several frames around the timestamp from the rendered MP4, not only from HyperFrames snapshots.

## Export Defaults

Review version:

- Match source orientation unless the user asks otherwise.
- Horizontal review: `2560x1440` or a fast proxy at the same aspect ratio.
- Portrait review: `1080x1920`.
- `30fps` or `60fps` depending on iteration speed
- complete audio remuxed from the original processed audio

Final publishing version:

- Horizontal: `2560x1440`
- Portrait: `1440x2560`
- `60fps`
- H.264 High Profile
- AAC audio
- `+faststart`

Recommended horizontal final encode shape:

```bash
ffmpeg -i master_horizontal_2k30.mp4 -i assets/talk-main-keyed.mp4 \
  -map 0:v:0 -map 1:a:0 \
  -vf "fps=60" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -profile:v high -level 5.2 -movflags +faststart \
  -c:a aac -b:a 192k final-horizontal-2k60.mp4
```

Recommended portrait final encode shape:

```bash
ffmpeg -i master_1080p60.mp4 \
  -vf "scale=1440:2560:flags=lanczos,fps=60" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -profile:v high -level 5.2 -movflags +faststart \
  -c:a copy final-2k60.mp4
```

## Avoid

- Do not cut before SRT confirmation.
- Do not skip storyboard review.
- Do not make the production process itself appear in the video unless that is the topic.
- Do not add full-height scrolling gold lines or flashy decorative effects.
- Do not darken the entire speaker with a heavy black overlay.
- Do not put subtitles too low where Douyin UI covers them.
- Do not make subtitle backgrounds fully opaque black.
- Do not convert horizontal source video to portrait unless the user explicitly asks.
- Do not convert portrait source video to horizontal unless the user explicitly asks.
- Do not use dense cards when a short dynamic keyword or real material is enough.
- Do not show a live moving background speaker behind a picture-in-picture speaker panel.
- Do not let a portrait video become a full-screen PPT/material video; the speaker must stay visible.
- Do not reveal key numbers before the matching口播/SRT timing.
- Do not invent financial facts, stock claims, prices, dates, or performance data.
- Do not imply investment advice or喊单.

## Response Style

When running this skill, report the current stage and next approval point. Keep the user in control of:

- SRT confirmation
- 文案结构确认
- 分镜表确认
- 设计确认
- 最终视觉确认

If the user says "继续", continue to the next unblocked stage.
