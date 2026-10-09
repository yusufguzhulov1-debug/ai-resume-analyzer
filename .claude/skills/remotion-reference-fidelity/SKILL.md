---
name: remotion-reference-fidelity
description: 基准片 风格保真层：参考片分析、复刻、语法泛化。触发词：基准片、风格复刻、参考对齐、保真闸。无参考设计走 rd-noref。
---

# 基准片 MG Style

Build a transferable motion system, not a one-off drawing. Preserve the reference's information logic, evidence hierarchy, timing, and editorial role before polishing visual details.

## Position in the current system

This skill is the reference-fidelity methodology layer, not a parallel production line. The koubo pipeline and its truth sources own the concrete numbers; this file only owns "how to faithfully read a reference and reproduce its argument logic." Defer to them and never restate their values here:

- fps / resolution / frame counts → `remotion-assembly` SKILL §0 (合成 fps/分辨率匹配素材, ffprobe 先查, 勿默认 60fps) + `remotion-design-system` references/motion.md §0 (先秒后帧, 合成实际 30fps) + specs.md (实测规格真源). Do not hardcode 60 fps or 4K here.
- design tokens (color / type / grid / radius / safe-area) → `remotion-design-system` SKILL §1 + typography.md / texture.md.
- takeover model → layout.md (A 级素材接管；B 级压暗升格与 PiP 已被用户否决，接管一律人物整段退场).
- persistent micro-motion → motion.md §8/§9 (主角必包 Breathe；每章 ≥1 个肉眼可辨运动).

Production line: the current koubo delivery is **baked** — OffthreadVideo 铺底 + MG 烤入单合成 (Koubo071501.tsx / scenes/SceneNN.tsx), reviewed as baked 段渲 mp4 and finished via 母带链 (assembly §4/§6). The "transparent alpha overlay / checker preview / alpha master" language below describes an **optional alpha-delivery mode only**; when delivering into the koubo line, read "checker preview" as "baked 段渲 preview" and "alpha master" as "baked master + 母带链."

## Non-negotiable principle

Treat the MG as an argument layer attached to speech:

1. Identify the sentence's claim.
2. Choose the minimum visual structure that proves or clarifies it.
3. Keep the speaker visually dominant unless the edit deliberately becomes a media takeover.
4. Change state only when the spoken meaning changes.

Do not invent a prettier but semantically different scene. A visually polished redesign is a failed replica when its evidence, state sequence, or editorial function differs from the source.

## Select a scene grammar

Use one of these validated grammars, then adapt content and timing:

- Persistent diagnosis + transient evidence: keep risk/checklist cards stable while a real screenshot appears briefly and leaves.
- Stable process + successor sentence: show the complete pipeline as a settled state, then replace it with one short conclusion at the phrase boundary.
- Evidence + delayed verdict: let a real evidence card leave first; introduce the verdict stamp only after the audience has read the numbers.
- Multi-shot explanation: use `composition -> chapter only -> identity -> media takeover`; do not flatten distinct shots into one dashboard.
- Quote proof + quantitative punch: real quote screenshot, annotation, measured count, emphasized keyword, then speaker/source chip.
- System state + progressive credentials: hold the core matrix and reveal only the credentials mentioned by speech.

These six are reference-reproduction grammars. The koubo assembly's own native beat system (侧标体系 / 红绿阵营 / 重锤时机 / hook·CTA / 判词升格) lives in `remotion-assembly` references/narrative.md — use it when authoring a new koubo video, don't duplicate it here.

## Analyze before coding

For every reference segment:

1. Verify the correct source file and exact time range. Cross-check candidates when filenames are ambiguous.
2. Extract frames at the start, every semantic boundary, every transition midpoint, and the end.
3. Write a motion map with absolute source time, local frame, visible layers, entering/leaving layers, and the spoken phrase causing the change.
4. Separate actual MG from subtitles, host footage, B-roll, and the next editorial shot.
5. Measure anchors, bounds, opacity, and duration from source frames. Mark estimates explicitly.
6. Use real screenshots, people, logos, articles, and news clips when the reference relies on evidence. Do not hand-draw fake evidence UI.

If the motion map is uncertain, stop before implementation and gather more frames.

## Build the overlay

- Match the project's fps and resolution — koubo 基准 1080p, 合成 30fps; ffprobe 先查, 勿默认 60fps/4K (Position note; 错题 #19). 4K output is ×2 of the 1080p base per design-system §1.
- Delivery mode decides the background: baked (default koubo) composites MG over the OffthreadVideo 铺底 into one composition; alpha mode keeps the render background transparent and ships a separate checkerboard preview composition.
- Protect the subtitle zone and the speaker's face and hands (SAFE tokens: 常驻卡不越 x55%, 字幕禁区 y>82%, 左区元素底边 ≤y840 更严 — design-system §1; 人物禁入区/右区坐标见 layout.md).
- Reuse project typography, color, grid, radius, and safe-area tokens from `src/design/tokens.ts` (design-system SKILL §1); do not introduce a parallel design system or restate token values here.
- Store scene content and timing in data objects when the pattern will be reused.
- Require traceable `evidenceRef` metadata for real material. Gate important source assets with SHA-256 when silent replacement would invalidate fidelity.
- Prefer short opacity, position, or scale changes tied to meaning (motion.md §6 三档动效词汇). Reject decorative loops, gratuitous fly-ins, and spring overshoot (motion.md §11). This is **not** a ban on persistent micro-motion — the reference does breathe: 主角元素必包 `<Breathe>`, 相位错开, 小件不包 (motion.md §9), and every chapter carries ≥1 legible ongoing motion (motion.md §8). (The earlier "avoid ambient breathing" reading was wrong against the source and is superseded by motion.md §9.)
- Preserve editorial opacity hierarchy: chapter HUD is crisp; supporting names, portraits, timelines, and contextual evidence may be dimmer; the current proof or verdict receives the highest contrast.
- A full-screen source clip is an opaque editorial takeover (A 级素材接管, layout.md), not a translucent overlay. Model it as its own shot/Scene, with the speaker exiting for its full duration (人物整段退场、不带 PiP — layout.md; PiP 已否决).

## Timing language

- Start from the source's current state. Do not replay construction animation when the reference begins already assembled.
- Hold information long enough to read; the style is state-driven, not constantly moving.
- Small entrances/exits are ~0.1-0.3s; convert to frames at the composition's real fps (先秒后帧, motion.md §0 — koubo 30fps → ~3-9 帧). Measure from source when possible (specs.md 规格真源). Never carry a 60 fps frame count into a 30 fps composition (错题 #19).
- Allow stagger only when it maps to spoken enumeration.
- Let old evidence leave before a verdict or successor sentence when the reference does so.
- Preserve overlaps and delayed reveals. Never replace a fade/overlap sequence with a hard cut for convenience.
- End at the true MG boundary. Do not stretch a 1.2-second graphic across unrelated B-roll.

## Mandatory fidelity gates

Pass every gate in order:

1. Motion map: source-verified state sequence and boundaries.
2. Static gate: 3-6 source-versus-replica frames at matching times.
3. Dynamic gate: a small H.264 side-by-side — source on the left, our render on the right (baked 段渲 for koubo; checker preview in alpha mode).
4. Independent audit: another reviewer checks timing, geometry, opacity hierarchy, real assets, and extra/missing states. 任一维 <7 或存在 FAIL 级违规 = 打回 (mg-judge + rubric.md, assembly §2.5).
5. Master release: render the final master only after the dynamic comparison **and 用户动态终审** pass (动效手感是 AI 静帧盲区，master release 前置含用户终审 — assembly §2.5 闸③; baked mp4 → 母带链 for koubo, assembly §6; transparent master in alpha mode).

The implementation thread must not self-certify. A still-image match cannot approve motion timing.

## Render discipline

- Use `--bundle-cache=false` after code edits when stale Remotion bundles could hide changes (错题 #02: `○` = 复用旧图).
- Render small previews for review — 1080p `--scale=0.5`, or the 段渲 service `node scripts/render-service.cjs segment|stills|qc` (assembly §6); a checker composition only in alpha mode.
- For a narrow timing repair, render only the affected frame range (`--frames=a-b`), not the full composition.
- Keep review previews small; never render a large master speculatively (雷区「自动跑 4K render」；渲染只按用户/方案确认的范围起).
- Render the final master only for an approved composition and the requested delivery codec; long renders go `nohup … & disown`, 认日志 `+` 行 (错题 #09).

## Failure patterns to reject

- Semantic redesign presented as replication.
- Abstract cards replacing real screenshots or news evidence.
- Correct-looking first frame with wrong later states.
- Identity, verdict, or conclusion appearing before its spoken cue.
- Whole groups exiting when the reference keeps an anchor layer persistent.
- New labels, taxonomies, stamps, or conclusions absent from the reference. (Persistent 主角 Breathe is mandated by motion.md §9 and is not counted as an invented element — do not strip it to match a static-looking still.)
- Evidence enlarged until it competes with the speaker.
- Subtitles or host footage accidentally baked into an asset intended for reuse.
- A pass declared without source-versus-output comparison.

## Generalize for a new talking-head video

**Scope guard**: this section generalizes the six validated *reference-reproduction* grammars — it applies only when a reference exists to select grammars from. Designing beats with **no reference** is a different path: `remotion-assembly` 端到端流程第 4 步 (selection.md 句型对号表) + `references/rd-noref.md` (语法缺口时的多方案生成→judge panel→用户定稿). Do not force one of the six grammars onto content it doesn't fit.

Convert the transcript into semantic beats. For each beat, fill:

```ts
type MgBeat = {
  claim: string;
  grammar:
    | "diagnosis-evidence"
    | "pipeline-successor"
    | "evidence-verdict"
    | "multi-shot"
    | "quote-punch"
    | "system-credentials";
  startFrame: number; // all *Frame fields at composition fps (先秒后帧, motion.md §0); never a 60fps count
  endFrame: number;
  cueFrame: number;
  persistentLayers: string[];
  transientLayers: string[];
  evidenceRef?: string;
};
```

Choose the grammar from the claim, not from surface keywords. Replace copy, assets, and cue frames while preserving the grammar's state logic. If no validated grammar fits, analyze a new reference and add a new grammar only after it passes the same gates.

## Completion contract

Deliver:

- The delivered composition — baked Scene(s) into the koubo composition by default; a Transparent Overlay + Checker Preview pair only in alpha mode.
- Evidence metadata and asset gates where applicable.
- Matching-time static comparisons.
- Dynamic side-by-side comparison.
- Independent PASS (任一维 ≥7 且无 FAIL 级违规 — mg-judge + rubric.md, assembly §2.5) plus 用户动态终审 passed.
- A concise note explaining which grammar was used and why.
