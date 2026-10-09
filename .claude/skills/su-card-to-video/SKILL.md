---
name: su-card-to-video
description: Create a minimal AI card video from HTML/CSS cards and a prepared audio file. Use when the user wants a simple local workflow for 16:9 card-based videos without Jianying/CapCut, without appearing on camera, and without image generation APIs; supports HyperFrames/GSAP rendering and FFmpeg audio-video muxing, and can be adapted for other agents.
---

# su-card-to-video

Use this skill to create a simple local AI card video:

```text
script/captions -> HTML/CSS cards -> HyperFrames/GSAP render -> FFmpeg mux -> MP4
```

## Boundaries

- Do not call image generation APIs by default.
- Do not require the user to appear on camera.
- Do not require Jianying/CapCut.
- Do not include or assume a voice-cloning API.
- Accept any prepared audio: recorded speech, TTS, voice clone, or a silent placeholder.
- Keep the workflow simple enough to copy into other agents.

## Default Output

- Aspect ratio: 16:9
- Video format: MP4
- Source: `examples/basic-16x9/index.html`
- Final output: `examples/basic-16x9/output/final.mp4`

## Workflow

1. Turn the user's script into a small number of card scenes.
2. Edit `examples/basic-16x9/index.html` with clear, readable HTML/CSS cards.
3. Use GSAP animations sparingly: scene fades, small y movement, subtle scale.
4. Render the HTML with HyperFrames when available.
5. Use FFmpeg to mux the rendered video with the user's audio.
6. If no audio is provided, use a silent placeholder only for demo/testing.

## Dependency Policy

Assume users install dependencies themselves:

```bash
brew install node
brew install ffmpeg
npm install
```

HyperFrames can be used through the local dependency or with `npx hyperframes`.

## Other Agent Prompt

When adapting this skill to a non-Codex agent, give it this instruction:

```text
请按 su-card-to-video 的工作流帮我生成一条最小 AI 图卡视频：用 HTML/CSS 制作 16:9 图卡画面，用 GSAP 或你可用的网页动效方式制作简单转场，用 FFmpeg 把画面和我提供的音频合成为 MP4。不要调用图像模型，不要要求真人出镜，不要使用剪映。优先保持流程简单、可本地运行、可复用。
```

## Quality Rules

- First frame must not be blank.
- Text must be readable at video size.
- Keep card count modest; prefer 4-6 scenes for a short demo.
- Use exact user-facing captions as the spoken text when possible.
- Match visual duration to audio duration; do not stretch audio to fit visuals.
- Make the final frame feel complete, not abruptly cut off.

