# Seedance 2.0 — Master Reference

## What Seedance 2.0 Actually Is

ByteDance's cinematic AI video family accepts text, image, video, and audio as inputs
simultaneously. Seedance 2.0 generates up to 15 seconds in one clip; Seedance 2.5 generates up to
30 seconds in one clip.
The engine that went viral for clips that look like real Hollywood productions.

## MODEL-AWARE DURATION AND CLIP COUNT

Determine the selected model version before budgeting clips:

| Model | Maximum duration in one clip | Planning consequence |
|---|---:|---|
| Seedance 2.0 | 15 seconds | A request of 15 seconds or less is one clip. |
| Seedance 2.5 | 30 seconds | A request of 30 seconds or less is one clip. |

Use the minimum supported clip count. Do not split a 30-second Seedance 2.5 request into two
15-second clips merely because Seedance 2.0 has a shorter limit. Split within a model's limit only
when the user asks for separate clips or an approved creative/technical constraint requires it.

---

## TWO GENERATION MODES — Know Which You're Writing For

### TEXT-TO-VIDEO (T2V)
- Pure text prompt. No reference image.
- Character is described entirely in words within the prompt.
- Best for: viral content, action, anime, comedy, cinematic scenes
- Character consistency challenge: harder — use strong anchor words every shot

### IMAGE-TO-VIDEO (I2V)
- Upload reference image(s) + write prompt
- `@image1` tags the primary character reference
- `@image2` tags secondary character or environment
- Best for: consistent characters across scenes, personal videos, branded content
- Character consistency: much better — @image anchors the face/body geometry

---

## THE OMNI REFERENCE FORMAT (@image system)

This is the heydin.ai / professional creator standard for I2V prompts.

```
[HEADER: CHARACTER & SET DETAILS]

@image1: [Full description of what's in the reference image —
         physical traits, clothing with fabric details, props,
         demeanor. Write it as if describing the image to someone
         who can't see it.]

@image2: [Second reference if applicable]

SFX & ENVIRONMENT: [Location, time, atmosphere, lighting conditions]

SHOT 1: [Shot Type Name]
@image1 [action]. [Camera type + movement]. [Speed]. [Depth of field].
[Sound description]. [Music: yes/no]

SHOT 2: [Shot Type Name]
@image1 [action]. [Camera]. [Speed]. [Sound]. [Music]

[Continue...]
```

**Key rules for @image prompts:**
- Describe the reference image accurately — Seedance reads this as the consistency anchor
- Specify speed as fps: "slow motion (approx. 60fps rendered at 24fps)"
- Always state "No Music" or "Music: [describe tempo and feel]" — Seedance generates audio
- Camera shake: "handheld with aggressive camera shake" vs "handheld, subtle"
- Every shot = its own paragraph with all 5 elements

---

## THE VIRAL T2V FORMULA

Structure that consistently produces viral Seedance videos:

```
VISUAL STYLE: [One sentence — render quality + camera aesthetic + genre mood]

CHARACTERS: [Precise physical description of everyone on screen —
            age, build, skin, hair, clothing with texture, props,
            personality/demeanor that comes through visually]

ENVIRONMENT: [Where + when + atmosphere + active elements (rain, fire, destruction)]

EMOTIONAL TARGET: [The arc from first frame to last — what escalates]

COLOR LOGIC: [Grade name + description]

TIMELINE:
00:00.0–00:01.5: [SECTION NAME — e.g. "HOOK / ENTRY"]
[Camera angle]. [Exact action]. [Lens note if relevant].
SFX: [specific sounds — be precise: "heavy squelching mud, rhythmic breathing"]
Music: [describe or "No Music"]

00:01.5–00:04.0: [SECTION NAME]
[Description] SFX: [sounds]

[Continue to end]
```

---

## THE HOOK RULE — First 2 Seconds

Every viral Seedance prompt starts mid-action. Never at the beginning.

**Bad hook:** "A warrior stands in a field. He looks at the horizon. Then a monster appears."
**Good hook:** "Camera opens on the warrior already mid-air, a stone column fragment passing one centimeter past his face in slow motion — he grabs it, uses it as a springboard."

**Hook types that work:**
- Character crashes through something into frame
- Already mid-fight — impact just landing
- POV drop into chaos with zero setup
- Environmental destruction happening right now
- Character already running from something enormous

---

## NATIVE CAMERA CONTROLS

Always use exact names — Seedance recognizes these:

| What You Write | What It Does |
|----------------|-------------|
| `static camera` | Zero movement — locked tripod |
| `locked off` | Same as static |
| `handheld, subtle` | Light organic sway — intimacy |
| `handheld with aggressive camera shake` | Fight impact feel |
| `slow dolly in` | Tension build |
| `fast dolly in` | Urgency/attack |
| `slow dolly out` / `pull back` | Isolation/endings |
| `pan left` / `pan right` | Follow/reveal |
| `tilt up` / `tilt down` | Power/defeat |
| `low-angle tracking shot` | Ground-level action follow |
| `side-profile tracking shot` | Classic action side view |
| `slow orbit left` / `orbit right` | Product/wonder |
| `tracking shot` | Follows at same distance |
| `slow crane up` | Transcendence/endings |
| `whip pan` | Energy shift/time cut |
| `speed ramping: real-time → slow-motion → real-time` | Impact emphasis |
| `Speed ramping: real-time approach, transitioning into extreme slow motion during [peak], then returning to real-time` | Phil Franco format |

---

## SPEED — WRITE IT PRECISELY

**Bad:** "slow motion"
**Good:** "slow-motion (approx. 20-25% speed)" or "approximately 60fps rendered at 24fps"

Speed categories:
- Normal: real-time
- Light slow: 50% speed (approx. 48fps → 24fps)
- Medium slow: 30% speed
- Heavy slow: 20-25% speed (approx. 120fps → 24fps)
- Extreme slow: 10-15% speed (approx. 240fps → 24fps)

---

## AUDIO — ALWAYS SPECIFY

Seedance generates audio with video. You must direct the sound design.

**Sound design layers:**
1. Ambient environment (wind, rain, crowd, machine hum)
2. Action SFX (footsteps on specific surface, impact type, weapon sound)
3. Character audio (breathing, grunt, dialogue)
4. Music: "No Music" OR describe: "low industrial hum" / "playful light piano" / "sub-bass thump"

**Critical:** Write `No Music` explicitly if you don't want music. Seedance will add music if you don't specify.

---

## CHARACTER CONSISTENCY RULES

### For @image (I2V) mode:
- **Best reference image:** Front-facing, full body, neutral pose, plain background
- **Anchor words:** Pick 5 physical descriptors and repeat in every shot containing this character
- **Safe angles:** Front, 3/4, side profile
- **Risky angles:** Extreme bird's eye, extreme dutch angle (avoid for face shots)
- **Forbidden words:** "realistic", "photographic", "normal proportions" — these override style

### For pure text (T2V) mode:
- Describe character ONCE in the CHARACTERS block
- In each shot, reference by name + 2-3 anchor words minimum
- Use `@image1` tag even in text descriptions to signal the AI which character
- Keep clothing identical across shots unless explicitly changed

---

## SMART CUTS — WHEN TO USE

**ON:** Any video over 8 seconds needing multiple camera angles
**OFF:** Single continuous shot (macro pour, ECU hold, product orbit)

With Smart Cuts ON, describe your shot sequence:
`"Wide establishing shot transitioning to medium close-up, then cutting to extreme close-up on [detail]"`

---

## WHAT SEEDANCE 2.0 DOES BEST

1. Multi-shot sequences with Smart Cuts — coherent camera logic automatically
2. Cloth and hair physics — robes, capes, fabric movement exceptional
3. Fluid dynamics — water, tea, fire, smoke, blood
4. Action choreography — fights, chases, impacts
5. Speed ramping — slow-mo on impact is a Seedance signature
6. Facial expressions — emotional micro-reactions
7. Environment destruction — collapsing, shattering, crumbling
8. Character consistency with @image reference

## WHAT TO AVOID

- "Zoom in" → use `slow dolly in` or `fast dolly in`
- "Slow motion" → use "approximately 20% speed"
- "Show the scene" → describe exactly what the camera sees
- Too many effects stacked (4+ degrades quality)
- Starting at the beginning of a story (start mid-action)
- Forgetting audio direction (always specify)

---

## WHERE TO ACCESS SEEDANCE 2.0 (FREE)

| Platform | Free Access | Notes |
|----------|------------|-------|
| Little Skylark app | Unlimited (promo) | Best free option right now |
| jimeng.jianying.com | Douyin account | Free credits |
| Higgsfield.ai | Free tier | Cinema Studio + Seedance |
| Dreamina (Picsart Flow) | Free tier | Good for action content |
| ImagineArt | 100 credits/day | Multiple models one place |
| WaveSpeed.ai | Free signup credits | API access |

**Credit strategy:** Generate hero shot first (best credits + most attention).
Spread other shots across platforms when daily limits hit.
