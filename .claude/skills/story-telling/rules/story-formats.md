---
name: story-formats
description: Story format catalog with scene skeletons, stat placement and art direction per format
---

# Story formats

Pick the format first: it decides the scene count, where the stat cards go and
what the outro says. Ready made starting points live in `assets/`.

| Format | Template | Best length | Scenes |
|---|---|---|---|
| Biography | `assets/biography/story.json` | 60s | 6 |
| Concept explainer | `assets/explainer/story.json` | 60s | 6 |
| Vertical short | `assets/reel/story.json` | 30s | 3 |
| Numbered list | `assets/listicle/story.json` | 60s | 6 |
| News or event | `assets/news/story.json` | 45s | 5 |
| Myth versus fact | `assets/myth-buster/story.json` | 45s | 5 |

Copy a template to `public/<slug>/story.json`, change `slug` and
`compositionId`, rewrite the narration and prompts, then generate.

## Biography

The arc that made the Jhunjhunwala video work.

| Scene | Job | Stat |
|---|---|---|
| 0 | Hook: the end state as a number, and where it started | starting figure |
| 1 | Origin: the moment or person that started it | none |
| 2 | First move: the first real bet and what it returned | first return |
| 3 | Setback or contrarian turn | none |
| 4 | The big win, with the multiple | the multiple |
| 5 | Where it ended up, sourced and dated | final figure |

Art direction: one recurring character across the scenes. Use a reference photo
through the edit model so the face stays the same, and vary age, wardrobe and
setting per scene. Alternate character frames with object or place frames so it
does not feel like a slideshow of one person.

## Concept explainer

| Scene | Job |
|---|---|
| 0 | The symptom the viewer already recognises |
| 1 | Name the thing, plainly |
| 2 | The mechanism, part one |
| 3 | The mechanism, part two |
| 4 | What changes when it moves |
| 5 | What the viewer should now do or watch |

Stats belong on scenes 1 and 4: the current value of the thing, and its effect.
Art direction: metaphor over literal. A lever, a valve, a dam, a set of scales.
Avoid charts as artwork, since the stat card already carries the number.

## Vertical short

Three scenes, about 30 seconds, `orientation: "vertical"`.

| Scene | Job |
|---|---|
| 0 | Hook in the first three seconds, stated as a claim |
| 1 | The one piece of evidence |
| 2 | The turn, plus a reason to follow |

Rules that differ from landscape: subtitles group 4 words, not 6; the stat card
sits top centre; keep the title card to two lines. Put nothing important in the
bottom 260px, where platform UI overlays sit.

## Numbered list

Scene 0 sets the promise ("five things ..."), scenes 1 to N carry one item
each, and the last scene closes. Every item scene gets a stat card whose value
is the item number or its headline figure, so the viewer can track position.
Keep item scenes the same length: uneven items make a list feel disorganised.

## News or event

| Scene | Job |
|---|---|
| 0 | What happened, and when |
| 1 | The number that makes it matter |
| 2 | Background needed to understand it |
| 3 | Who is affected |
| 4 | What happens next, and by when |

Every claim carries its date in the narration, not only on the card. News
stories age: a video that says "today" is wrong within a day, one that says
"on the third of July" stays correct.

## Myth versus fact

Alternate: myth stated flat, then the correction with the number. Use the
accent colour on the fact scenes only, so the visual rhythm matches the
argument. `style.accent` red for myths and green for facts is heavy handed:
better to keep one accent and let the stat card carry the correction.

## Choosing length

| Platform | Orientation | Length | Scenes |
|---|---|---|---|
| YouTube | landscape | 60 to 90s | 6 to 9 |
| YouTube Shorts, Reels, TikTok | vertical | 30 to 45s | 3 to 5 |
| LinkedIn, X | landscape | 45 to 60s | 5 to 6 |
| Website hero | landscape | 20 to 30s | 2 to 3, often no narration |

Scene count is roughly seconds divided by ten. `npm run draft` applies exactly
that rule and clamps between 3 and 10.
