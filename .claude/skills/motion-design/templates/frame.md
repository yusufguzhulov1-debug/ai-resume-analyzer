---
version: 2
name: "{{BRAND}}: launch frame"
description: >
  Video-first frame spec for the {{BRAND}} launch motion design, built on ../patterns/PATTERNS.md. {{METAPHOR_IN_ONE_SENTENCE}}.
  Two worlds: the PROBLEM lives on a warm near-black stage, the SOLUTION on a light ground; the end card returns to the
  dark stage. One accent only, {{ACCENT_NAME}}, kept for what matters: the key-word box of each subtitle and 3 or 4
  peak strokes. The sentence of the voice is a subtitle at the bottom center that arrives word by word.
  Complete film written this way: examples/ligne-du-temps-v8/frame.md.
  Template of the motion-design skill: replace every {{...}} placeholder (grep -n "{{" frame.md must print nothing).
  Reference values in the comments are those of the Entrepreneurs 2.0 example films (terracotta on warm black and paper).
unit: 1920×1080
principle: readable without sound · one thing to look at at a time · one accent, one highlight mechanism · the voice cues every reveal

colors:
  canvas: "{{CANVAS}}"                # dark world (problem + end card), ref "#0d0b0a"
  canvas-2: "{{CANVAS_2}}"            # ref "#141010"
  paper: "{{PAPER}}"                  # light world (solution) full-bleed ground, ref "#f6f1e9"
  paper-2: "{{PAPER_2}}"              # secondary light surface, ref "#efe7dc"
  card-light: "{{CARD_LIGHT}}"        # cards on the light world, ref "#fffdf9"
  ink: "{{INK}}"                      # text on dark, ref "#f5efe7"
  ink-soft: "{{INK_SOFT}}"            # ref "#cdbfb2"
  ink-mute: "{{INK_MUTE}}"            # ref "#9b9289"
  ink-dark: "{{INK_DARK}}"            # text on light, ref "#1a1612"
  ink-dark-soft: "{{INK_DARK_SOFT}}"  # ref "#5a5348"
  hairline-light: "{{HAIRLINE}}"      # ref "#e2d9cc"
  accent: "{{ACCENT}}"                # THE brand accent, ref "#c25b28"
  accent-light: "{{ACCENT_LIGHT}}"    # ref "#d4703f"
  accent-deep: "{{ACCENT_DEEP}}"      # ref "#a84d22"
  accent-glow: "{{ACCENT_GLOW}}"      # ref "#e08a5c"

# Local woff2 files only, never a network @import (fetch commands: references/method.md, step 2).
# Default trio of the method (all SIL Open Font License): swap only if the brand has its own fonts.
fonts:
  Instrument Sans: { files: ["assets/fonts/InstrumentSans-400.woff2 (400)", "assets/fonts/InstrumentSans-500.woff2 (500)", "assets/fonts/InstrumentSans-600.woff2 (600)", "assets/fonts/InstrumentSans-700.woff2 (700)"] }
  Space Mono: { files: ["assets/fonts/SpaceMono-400.woff2 (400)", "assets/fonts/SpaceMono-700.woff2 (700)"] }
  Big Shoulders: { files: ["assets/fonts/BigShoulders-800.woff2 (800)"] }

typography:
  subtitle:   { fontFamily: "Instrument Sans", px: 62, weight: 600, lineHeight: 74, tracking: "-0.015em", note: "the sentence of the voice at the BOTTOM CENTER (top at y 896, inside the band y 890 to 980 that carries nothing else), 60 to 64 px, 45 characters at most per chunk (a longer sentence splits into chunks that replace each other), word by word on its timestamps; a light shadow detaches it from the ground; ink on the light world, ink on dark on the dark world. Never at the top left" }
  type:       { fontFamily: "Instrument Sans", px: 84, weight: 600, lineHeight: 1.12, tracking: "-0.025em", note: "ONLY the 2 or 3 typographic moments named in the storyboard (the diagnosis, the pivot): the sentence IS the image, centered, never bigger than 84 px, no subtitle at the bottom meanwhile" }
  numeral-jumbo: { fontFamily: "Instrument Sans", px: 300, weight: 600, lineHeight: 0.9, tracking: "-0.02em", tabularNums: true }
  ui:         { fontFamily: "Instrument Sans", px: 28, weight: 500, lineHeight: 1.3 }
  title:      { fontFamily: "Instrument Sans", px: 44, weight: 600, lineHeight: 1.1, tracking: "-0.02em" }
  code:       { fontFamily: "Space Mono", px: 26, weight: 400, lineHeight: 1.5, note: "only if the film shows code; keywords in accent-light" }
  price:      { fontFamily: "Space Mono", px: 30, weight: 700, tabularNums: true }
  micro:      { fontFamily: "Space Mono", px: 18, weight: 400, tracking: "0.2em", upper: true }
  wordmark:   { fontFamily: "Big Shoulders", px: 64, weight: 800, upper: true, note: "{{WORDMARK_RULE}}, e.g. 'BRAND' in ink + ' 2.0' in accent-light" }
  cta:        { fontFamily: "Big Shoulders", px: 34, weight: 800, upper: true }

components:
  ground-dark:
    background: "solid canvas + 1-2 soft radial accent halos (14-28% opacity, blur 100px+) behind the focal element + static film grain 4-6%. Painted as a full-duration class=\"clip\" layer, never on #root."
  ground-light:
    background: "solid paper + one very soft warm radial (accent at 6-10%) behind the focal element + grain 3%. Text is ink-dark. Full-duration class=\"clip\" layer."
  word-by-word:
    rule: "Each word of the subtitle appears ON its voice timestamp, grey (ink at 35 %): fromTo {opacity:0, y:8, filter:blur(6px)} → {opacity:1, y:0, blur(0)} in 0.14 s, immediateRender:false, then it turns to full ink in 0.2 s. Never the whole sentence at once. Before a seam the subtitle leaves: opacity 1 → 0 and blur 0 → 6 px in 0.14 s."
  key-word-box (THE highlight mechanism, one per sentence):
    look: "a small rectangle in the accent color, sharp corners (radius 3px), overflowing the word by 0.14em on each side; the word turns to the paper color inside. Never a black box."
    motion: "the box traces from the left (scaleX 0 → 1, transform-origin left, 0.16 s power3.out), 0 to 2 frames before the word is spoken; the word changes color as the box passes (0.1 s)."
    rule: "ONE box per sentence, on the word the storyboard names as [boîte : …]. No other colored text anywhere."
  peak-stroke (the 3 or 4 peaks of the film):
    look: "a thin accent stroke (4 px, round caps) or a tapered brush stroke (round attack, thin exit, slight rising curve) under THE key word only, never under the whole sentence."
    motion: "draws from the left (scaleX 0 → 1, 0.3 to 0.5 s power2.out) while the word is spoken."
    rule: "named [trait : …] in the storyboard. Never a big box, never a giant word, never a line of the decor crossing the sentence."
  letters-converge (only if a typographic moment needs it):
    motion: "enters with its letters converging + opacity 0→1 + blur 12px→0 over 0.5 s expo.out; may sit behind a card or object (z-order) for depth. NEVER tween letterSpacing (it snaps to device pixels under seek capture and the lint blocks it): keep letter-spacing -0.05em static, split the word into inline-block letters and tween each letter's x from (i - (n-1)/2) × 0.4em to 0. A counting number keeps only scale + blur."
  glass-card-dark:
    background: "linear-gradient(160deg, rgba(40,33,28,.92), rgba(24,20,17,.9) 45%, rgba(20,16,14,.9) 80%, rgba(30,24,20,.92)); 1px rgba(245,239,231,.10) border; inset 0 1px 0 rgba(255,255,255,.14); shadow 0 50px 120px rgba(0,0,0,.7); radius 14px (retint to canvas)"
  card-light:
    background: "card-light, 1px hairline-light border, radius 14px, shadow 0 30px 80px rgba(60,40,20,.14), 0 2px 6px rgba(60,40,20,.08)"
  counter:
    description: "numeral-jumbo number that rolls to its value (tabular digits, grows slightly with the value), with a micro unit label under it. Every number on screen rolls, none is simply posed."
  tool-tiles:
    description: "Real tool logos from assets/icons/*.svg (Simple Icons, CC0): inline SVG path in an 88px white rounded tile (radius 20px, soft shadow), filled with the tool's own brand color ({{TOOL_COLORS}}, e.g. Gmail #EA4335, Stripe #635BFF). Brand colors are the ONLY exception to the one-accent rule, only inside tool tiles."
  persona:
    description: "{{PERSONA}}: a flat vector character in inline SVG, head + shoulders, simple hair, NO detailed face (two small dot eyes max), ~340px tall, friendly and simple, not childish. The same drawing in every frame where it appears."
  pain-pills:
    description: "Small dark pills (Space Mono 20px, white text on a dark warm grey, radius 999px) that pop around the persona one by one (≈0.12 s apart), slight deterministic rotation from the index, each with a tiny ✕ in accent."
  chat-input:
    description: "Large card with micro label '{{CHAT_LABEL}}', prompt typed char by char behind an accent caret, square accent send button with a white up-arrow. card-light on the light world."
  caret:
    description: "the text caret: a 4px × 58px accent-light bar, blinks as finite on/off steps (0.5 s period, NEVER a repeat:-1 loop)."
  product-mock:
    description: "{{PRODUCT_MOCK}}: the product or the user's own tool as it looks TODAY, from a recent screenshot the user gives (never drawn from memory: that is last year's interface), placed as an image or rebuilt in HTML; the whole device, small and uncluttered, only the elements that tell the story. It sits where it makes sense: a change request on a site is an annotation linked to the selected element, not a bubble dropped on the page. Accent elements only for the thing the voice points at."
  cursor:
    description: "White macOS arrow with dark outline + drop shadow; it arrives in ONE curved move (0.4 to 0.5 s power3.out) and clicks directly: press (scale .85, 0.06 s) + accent ripple ring that expands and fades. Never a hesitation."
  light-point:
    description: "a white-hot point (radial #fff3ea → accent-glow → transparent) used where the orchestrator's light flash starts."
  end-card:
    description: "dark stage, wordmark assembled letter by letter, one-line promise in type size with its peak stroke, ONE CTA button '{{CTA_LABEL}}' (paper fill, accent-deep Big Shoulders text, soft accent glow), mono URL '{{URL}}' in small, a cursor that arrives and clicks the button directly, then 2 to 3 s of living hold (drift, a texture that moves) before the iris or the black."

negative:
  - "No second highlight mechanism: the key-word box is the ONLY way a word of a subtitle is emphasized, the peak stroke marks the 3 or 4 peaks (no colored text, no glow text)."
  - "No big sentence: the subtitle is 60 to 64 px, a typographic moment 84 px at most; no giant word, no big box. Nothing but the subtitle in the band y 890 to 980; never a subtitle at the top left."
  - "One thing to look at at a time: the camera isolates the subject of the sentence. Side-by-side layouts keep equal left and right margins."
  - "No camera back-and-forth on the decor (a clear zoom in one direction is welcome). No cursor hesitation."
  - "No decor without meaning (grey bars 'to fill', abstract symbols, counters that say nothing); no line of the decor crossing a sentence."
  - "No hue other than the accent, except real brand colors inside tool tiles."
  - "No Inter, Space Grotesk, Geist, system-ui. No emoji. No icons in round pills."
  - "No bouncy/elastic/back.out eases. No breathing loops, no slow push on every scene, no repeat:-1."
  - "No visible text that is not listed in the frame's Scene lines (component labels above are allowed)."
  - "Never tween letterSpacing."
---

# {{BRAND}}: frame spec

The film has two worlds. **The problem** plays on the warm black stage: {{PROBLEM_WORLD_IN_TWO_SENTENCES}}. A single
**pivot** ({{PIVOT}}, a word alone or a caret in the dark) freezes everything, then light floods the screen and we land
on **the solution**, on the light ground: {{SOLUTION_WORLD_IN_TWO_SENTENCES}}. The iris from {{IRIS_OBJECT}} takes us
back to the dark stage for the **end card**.

Everything the viewer reads is Instrument Sans: the sentence of the voice as a subtitle at the bottom center, word by
word, with exactly one key word per sentence in a small accent box that traces itself first. A thin accent stroke
under the key word marks the 3 or 4 peaks.
Numbers, labels and code are Space Mono; the wordmark and the CTA are Big Shoulders.
