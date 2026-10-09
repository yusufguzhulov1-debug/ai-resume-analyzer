# Text Effects — Reference

For deterministic text-animation specs (e.g., `typewriter` at exact `240ms / 46ms stagger / steps(1, end) easing`), this skill defers to the separate **`animate-text`** skill maintained by Pixel Point at [github.com/pixel-point/animate-text](https://github.com/pixel-point/animate-text). It provides a catalog of 24 named text effects with portable contracts and per-library implementation recipes (GSAP, Anime.js, WAAPI).

**We do NOT ship the catalog inside this repo.** Pixel Point's `animate-text` is the source of truth; vendoring its files here would violate the upstream's licensing (no explicit license declared upstream as of this writing). Loading the skill separately keeps the legal picture clean while giving you the same catalog.

## How to use it

**Workspace rule (motion-launch, audited 2026-09-28):** the third-party `animate-text` skill is NOT installed and must not be installed (`npx skills add pixel-point/animate-text` is forbidden here: unaudited, no license). Implement each named effect from its description with GSAP.

Sub-agents reading those files get exact GSAP timings, easing strings, DOM split rules, and stagger algorithms — no creative invention needed.

## When you don't need the upstream skill

If a beat's text animation is simple enough to describe in prose ("headline fades up word-by-word, 80ms stagger"), implement it inline using the GSAP knowledge already in these skills (`hyperframes-creative` → `references/motion-principles.md` and `references/beat-direction.md`; `hyperframes-animation` → `techniques.md`, entry #4 "Per-Word Kinetic Typography"). The upstream catalog is most valuable when:

- You want a specific NAMED effect across multiple beats (so they feel like one design system, not one-offs)
- You're choosing between several similar effects (typewriter vs per-character-rise vs bottom-up-letters) and want to see all 24 in one place
- You need layout-aware effects (`kinetic-center-build`, `short-slide-right`, `short-slide-down`) where parameters alone aren't enough — those ship with custom layout algorithms

## Effect names — vocabulary (do NOT use this as the implementation source)

For convenience while writing storyboards: the upstream skill provides 24 effects. Their IDs are listed here so you can name them in `STORYBOARD.md` even before loading the upstream skill. **The implementation specs are in the upstream skill, not here.**

- **Per-character (7):** soft-blur-in, per-character-rise, typewriter, bottom-up-letters, top-down-letters, stagger-from-center, stagger-from-edges
- **Per-word (8):** per-word-crossfade, spring-scale-in, shared-axis-y, blur-out-up, kinetic-center-build, short-slide-right, short-slide-down, depth-parallax-words
- **Per-line (2):** mask-reveal-up, line-by-line-slide
- **Whole element (7):** micro-scale-fade, shimmer-sweep, fade-through, shared-axis-z, scale-down-fade, focus-blur-resolve, shared-axis-x

For descriptions, durations and easing curves, implement from the effect name with GSAP (the upstream skill is not installed here).

## In the storyboard

Every text element in every beat can name an effect by ID, e.g.:

```markdown
**Text Animations:**

- Main headline: `kinetic-center-build`
- Eyebrow label: `soft-blur-in`
- Body copy 3 lines: `mask-reveal-up`
```

Sub-agents implement the named effect from its description (the upstream skill is not installed in this workspace).

If the upstream skill isn't available (offline build, network restrictions, agent runtime that doesn't support skill loading), sub-agents fall back to implementing the effect from the description alone — using GSAP knowledge plus the effect ID as a description of intent (e.g., "typewriter" = per-character stepped reveal with no interpolation).
