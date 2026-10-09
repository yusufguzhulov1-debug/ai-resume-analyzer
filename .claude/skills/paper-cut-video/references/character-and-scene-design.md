# Character and scene design

Design from the locked narration, not from a reusable decoration kit. Every character, pose, prop, and background must help the current sentence land.

## Script-to-visual pass

Split the narration into semantic beats. For each beat, answer:

1. What should the viewer understand or feel?
2. Who can physically demonstrate that idea?
3. What action proves it?
4. Which prop makes the action obvious without extra text?
5. Is the shot a wide establishment, medium action, close explanation, comparison, or process?
6. What belongs in the background, rear, hero, and foreground layers?

Choose concrete metaphors for abstract subjects:

| Narration job | Character treatment | Useful action or prop |
| --- | --- | --- |
| Define a concept | One recurring guide or apprentice | Open a labeled task slip or point to one object |
| Explain a process | The same character in successive poses | Carry, sort, assemble, inspect |
| Compare two ideas | Mirrored versions of one character | Talk-only pose versus tool-using pose |
| Show a risk | Character near a visible consequence | Wrong target, oversized key, broken route |
| Show permission | Character pauses before a gatekeeper | Approval stamp, locked door, handoff |
| Summarize | Character presents the completed result | Checklist, finished object, sealed folder |

For an Agent explainer, a dependable paper intern is more legible than a generic robot: it can read the request, plan, use tools, check the result, and ask before crossing a boundary.

## Character bible

Define a stable identity before generating poses:

- Narrative role and personality.
- Age range and body silhouette.
- Historical period or modern occupation.
- Hair, headwear, face shape, and one recognizable feature.
- Costume silhouette and two or three stable colors.
- Paper treatment: printed linework, collage grain, warm edge, white keyline.
- Default facing direction and which way the character should look into frame.
- Scale class: hero, support, or rear.

Change only the action, expression, facing direction, and prop between poses. Do not accidentally change clothing, face, hairstyle, or palette.

## Pose manifest

Plan poses before image generation:

```json
{
  "character": "AI intern",
  "identity_anchor": "young paper apprentice, red vest, cream shirt, round ink glasses",
  "poses": [
    {"id": "reads-task", "facing": "right", "action": "reads a task slip", "prop": "paper brief"},
    {"id": "uses-tools", "facing": "left", "action": "opens a small toolbox", "prop": "toolbox"},
    {"id": "checks-work", "facing": "right", "action": "compares result with checklist", "prop": "clipboard"}
  ]
}
```

Write each scene to use an explicit pose ID. Avoid generating a large sheet first and deciding what the poses mean afterward.

## Generation prompt structure

Describe identity, action, visual language, framing, and exclusions in that order. Example template:

```text
生成【角色身份】的【全身/半身】剪纸人物素材，身体朝【方向】，正在【动作】，手持【道具】。
保持【发型、服装、主色、识别特征】与角色设定一致。
中国古籍线描、手工宣纸拼贴、印刷颗粒、清晰白色剪纸描边，人物完整且手脚不被裁切。
纯色背景或透明背景，只出现一个角色和指定道具；不要场景、文字、水印、额外人物和投影。
```

Generate a people-free environment separately. Match the shot's perspective, ground line, empty character zones, palette, and lighting. Do not ask an image model for a complete scene containing all people when the goal is layered animation.

## Asset extraction

- Prefer one character per generated file when consistency is reliable.
- Use a pose sheet only when every cell is separated cleanly and can be extracted without cutting hair, hands, clothing, or props.
- Remove the solid background or preserve true alpha.
- Export every person and movable prop as its own RGBA PNG.
- Check the alpha edge over both red and cream backgrounds.
- Keep at least 12–20 px of transparent padding around white keylines and shadows.
- Record source prompt, model, date, license/provenance, pose ID, and target scene.

Never reuse a reference article's characters as distributable assets unless the rights holder explicitly permits redistribution.

## Static staging

Approve still compositions before motion.

Use this bottom-to-top stack:

1. People-free background plate.
2. Rear characters and distant architecture fragments.
3. Midground support characters and props.
4. Hero character.
5. Foreground character or paper framing.
6. Caption rail and essential labels.

Size by narrative importance, not by equal spacing. As a starting ratio, set the hero's visible height to `1.0`, support characters to `0.45–0.70`, and rear characters to `0.25–0.45`. Break the ratio when the shot purpose requires it, then verify that the intended subject remains obvious at thumbnail size.

Check:

- All feet meet a believable ground line unless the character intentionally floats.
- Faces, hands, and important props remain visible.
- Characters look into the frame or toward the action.
- Foreground occlusion creates depth without hiding meaning.
- The background has enough quiet space for the cast and captions.
- Cards do not become larger or more important than the hero.

## Motion by depth

Use different movement for different depth classes:

| Layer | Entrance | Settle | Idle |
| --- | --- | --- | --- |
| Background | 0.8–1.5% slow push or 8–18 px drift | None | Continue slowly |
| Rear | 12–30 px travel, low opacity change | Small | 1–2 px |
| Support | 30–60 px from the side | Mild rotation correction | 2–4 px |
| Hero | 55–100 px, clear direction, 0.88–1 scale | Strongest paper landing | 2–5 px |
| Foreground | 35–70 px, slightly faster | Medium | 3–6 px |

Reveal the hero first, support cast 6–12 frames later, then rear or foreground groups. Reverse that order only when the story intentionally reveals context before the subject.

Derive motion from the current frame. Keep randomness seeded or avoid it. Give characters different idle phases so the whole cast does not bob in sync.

## Character scene acceptance

A character scene passes only when:

- The selected identity and action make sense for the spoken sentence.
- Face, costume, and palette remain consistent across poses.
- No character is fused into the background.
- Scale, facing, eye line, and ground line support the shot.
- Layer order creates readable depth.
- Entrances build the scene instead of appearing all at once.
- The final pose holds long enough to read.

## Method reference

These production principles were informed by the user-provided article [《用 Codex + Remotion 做一条唐朝纸片分层动画》](https://mp.weixin.qq.com/s/6cT91QcSMTwuKMQAF6tIfw). The skill paraphrases the workflow and does not redistribute the article's images.
