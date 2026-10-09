---
name: fake-screencast
description: Turn static SCREENSHOTS into a simulated screen recording (TSX) — a fake screencast with an animated cursor that eases to targets and clicks, a browser URL bar that updates per page, hard-cut navigations, in-page filter crossfades, smooth scroll, and a ken-burns zoom onto the payoff. Use when a beat needs to show a walkthrough of a web app / dashboard / settings page and you'd rather build it from screenshots than get (or ask for) a real screen recording — "fake a screen recording", "turn these screenshots into a screencast", "simulate clicking through the dashboard", "animate this UI walkthrough", "cursor moving through the app". Built on remotion/src/lib/screencast.tsx. This is a technique WITHIN step 2 (make-tsx): defer timeline/render/bake orchestration to make-tsx and raw crash-free TSX rules to vidtsx-2d-generator. Not for a single static page clone (use WebBrowserFrame directly) and not when the point is genuine proof of real speed/output (use a real recording).
---

# fake-screencast — screenshots → simulated screen recording

Make a screenshot walkthrough look like a real screen recording: persistent browser chrome with a **URL bar that changes per page**, a **custom cursor** that eases along a bezier path to each click target and **ripples on click**, page **navigation as a hard cut** (URL path changes), an in-page **filter as a short crossfade** (URL query changes), smooth **scroll**, a slow **ken-burns zoom** onto the payoff element, and a constant **drift** so it never looks like a slideshow. TSX-first: controllable, re-renderable, reusable across videos.

This is a beat-building technique inside **`make-tsx`** (step 2). Use `make-tsx` for the timeline.json / render / bake mechanics and the sync-to-words principles; use **`vidtsx-2d-generator`** for the low-level rules that keep a Remotion file from crashing (frame-based only, monotonic `interpolate`, `Easing.bezier`, no `useState`/`useEffect`). The shot you write here follows those rules.

## When this is the right tool (decision gate)

- **Fake screencast (this skill)** — you have or can capture screenshots of the states, and you want a *controlled* walkthrough (cursor path, highlight, zoom, timing synced to narration). This is P4 "real UI for config", just simulated. Best when the walkthrough is about *where things are* / *the steps*, not raw speed.
- **Real screen recording** — only when the point is genuine **proof**: real latency, a live result appearing, something you can't fake credibly. Leave a clearly-noted `pending_recording` placeholder slot until it lands (see `make-tsx`).
- **Single static page clone** — if it's one page with no navigation/cursor (e.g. a pricing page you just highlight/scroll), use `WebBrowserFrame` from `lib/browser.tsx` directly. Don't reach for the screencast machinery.

## Step 1 — get the screenshots (ask the user)

Tell the user the exact shot list you need (one screenshot per **page or state** the cursor lands on), then wait for them. Requirements:

- **Logged in / real data**, the actual product UI, captured at a consistent window size (ideally ~1920-wide).
- **One per state**, including intermediate states: an unfiltered list AND its filtered result count as two screenshots (the crossfade sells the "search applied").
- For a **real scroll-through of a long page**, you need a **tall** capture (full page, below the fold) — a single-viewport screenshot can't truly scroll (you can only fake a few px of drift). Say so and ask for the tall one if the beat needs it.
- Ask for any **missing view** by name (e.g. "the models list filtered to X", "the settings page after toggling Y").

Save them to `media/library/images/<service>/` with clear names (`account-home.png`, `workers-ai.png`, `models-all.png`, `models-flux.png`). Reference in a page as `library/images/<service>/<name>.png` (that's the `staticFile`-relative path the component expects).

## Step 2 — the library API (`remotion/src/lib/screencast.tsx`)

`<Screencast pages cursor clicks box glow favicon appearAt />`. **Coordinates are FRACTIONS** so they survive any resize:
- **cursor `x`/`y` and click ripples → VIEWPORT fraction** (0..1 of the page area *under* the URL bar).
- **zoom `fx`/`fy` → IMAGE fraction** (transform-origin of the push).

```tsx
import { Screencast, ScreencastPage, CursorKey } from '../../lib/screencast';

const PAGES: ScreencastPage[] = [
  { img: 'library/images/svc/home.png',  url: 'app.svc.com/…/home',        tabTitle: 'Home | Svc',    enterAt: 0 },
  { img: 'library/images/svc/list.png',  url: 'app.svc.com/…/items',       tabTitle: 'Items | Svc',   enterAt: 130, transition: 'cut' },       // navigation → hard cut + new path
  { img: 'library/images/svc/filtered.png', url: 'app.svc.com/…/items?q=x', tabTitle: 'Items | Svc',  enterAt: 262, transition: 'crossfade', transitionFrames: 5,   // in-page filter → crossfade + same path + query
    drift: 0.01, zoom: { from: 1.0, to: 1.4, fx: 0.32, fy: 0.52, range: [266, 289] } },  // ken-burns onto the payoff card
];

const CURSOR: CursorKey[] = [   // {frame, x, y} in viewport fractions; eased per segment
  { frame: 0, x: 0.60, y: 0.42 }, { frame: 128, x: 0.09, y: 0.68 }, /* … */ { frame: 294, x: 0.36, y: 0.52 },
];
const CLICKS = [130, 206, 255]; // frames a ripple fires (place at the arrival keyframe)

export const compositionConfig = { id: 'SvcRecording', durationInSeconds: 10.0, fps: 30, width: 1920, height: 1080 };
const SvcRecording = () => <Screencast pages={PAGES} cursor={CURSOR} clicks={CLICKS} />;
export default SvcRecording;
```

Page fields: `img, url, tabTitle, enterAt` (required); `transition?: 'cut'|'crossfade'` (default `cut`), `transitionFrames?` (default 5), `scroll?: {to, range:[a,b], from?}` (image px translateY), `zoom?: {from,to,fx,fy,range:[a,b]}`, `drift?` (default 0.02 — the constant slow "alive" push). Screencast props: `box?` (default `{x:60,y:63,w:1800,h:954}`), `glow?`, `appearAt?`, `favicon?` (default Cloudflare cloud — **pass your own for other services**).

## Step 3 — timing + coordinates

- **Frame 0 = the shot's `master_in_s`.** For a narration cue at `t` seconds: `frame = round((t − master_in_s) × fps)`. Grep `edited-transcript.json` for the exact word start/end (ms). Put the click / page `enterAt` a few frames **before** the word so the *result* lands on the word; end a ken-burns `zoom.range` **on** the payoff word.
- **Find a click-target fraction** from the screenshot: element's pixel position ÷ image width/height ≈ the viewport fraction (the image fills the page region, top-aligned, fit-to-width). Set the cursor's arrival keyframe there and add the click frame ~2f after arrival. Then **render and look** (Step 4) — nudge the fraction until the pointer sits on the element.
- Sequence each page/cursor move to its cue: dashboard hold on the intro line → cursor eases to a sidebar item and clicks as that item is named → next page appears → zoom to the payoff as the payoff word is spoken.

## Gotchas (each of these cost a render to find)

- **Zero-height containing block.** `WebBrowserFrame` wraps children in a `transform`ed div, which becomes the containing block for absolute descendants and collapses to 0 height. Page layers therefore need **explicit region dims** (`width/height` from the box), not `inset:0` — the lib already does this; keep it if you extend it.
- **Navigation vs filter is the realism tell.** A page change = **hard cut + different URL path**. An in-page search/filter = **short crossfade + same path (query appended)**. Mixing these up reads as fake.
- **Single-viewport screenshots can't scroll** — fake "aliveness" with `drift` + a ken-burns `zoom` instead. Only use a real `scroll` when you have a tall capture.
- **Render `--scale=1` for the preview** (1080p, correct for `bake.py`); re-render `--scale=2` for the 4K60 final.
- Cursor hotspot (the tip) is near the pointer SVG's top-left; the lib nudges for it. If a pointer looks a few px off, adjust the target fraction, not the SVG.

## Step 4 — verify, then hand back to make-tsx

- **Render + screenshot at EACH cue** (never one still): `node remotion/scripts/render-all.mjs --scale=1 <Id>`, then pull frames with ffmpeg at the **cursor-on-target** frame, each **click** frame, the **page-change** frame, and the **zoom payoff** frame. Confirm the pointer lands on the element, URLs change correctly, and the zoom frames the right thing. Iterate the fractions/frames and re-render.
- Then follow `make-tsx` for the rest: update `timeline.json` (swap/retime the span, drop any `pending_recording` note), `python tools/bake.py`, and **spot-check composited frames** of the shot over the real master at the beat + both boundaries.
- If you improve the component (per-page favicons, real typed-text-in-field, a caption layer), promote it back into `lib/screencast.tsx` so future videos inherit it.

## The canonical shape — copy this choreography

The move that reads as a real screen recording, over ~4 captured pages and ~10s:

1. **Hold** on the landing page while the narration sets it up (a beat of `drift`, never a frozen frame).
2. **Cursor eases** to a sidebar item and **clicks on the word that names it** — the click lands on the
   noun, not before it.
3. **Hard cut** to that page, **URL path changes**. This is a navigation.
4. **Type a filter** → **short crossfade**, **same path with the query appended**. This is not a
   navigation, and rendering it as one is the single biggest tell.
5. **Ken-burns zoom** onto the payoff exactly as the payoff word is spoken.

**Read `remotion/src/lib/screencast.tsx` before building one** — it's the engine, and its props are
the documentation for every move above. The pages array, the cursor keyframes, the per-page URL and
zoom are all typed there.

