---
name: narration
description: Writing the spoken script, word counts, and TTS-safe phrasing for Sarvam bulbul
---

# Narration

The script is the video. Artwork supports it, it does not carry it.

## Length

At `pace: 1.05` on bulbul:v3, English narration runs at roughly 165 words per
minute. Budget:

| Target | Words | Scenes |
|---|---|---|
| 30 seconds | 80 to 90 | 3 |
| 60 seconds | 160 to 175 | 6 |
| 90 seconds | 250 to 265 | 9 |

Per scene: 24 to 32 words, which lands between 8 and 11 seconds. Shorter than
20 words and the cut feels abrupt; longer than 35 and the images go stale.

Measured example, the six scene Jhunjhunwala story: 168 words produced 55.6
seconds of audio, plus a 3.1 second outro card for 58.7 seconds total.

If the total comes in short and a round minute matters, add outro frames rather
than padding the script. Never stretch a scene past its audio: the subtitles
are spread across the scene duration and would drift out of sync.

## Shape

- Scene 1 is a hook: the single most striking fact, stated flat, no throat
  clearing. Not "today we will look at".
- The middle scenes each carry exactly one idea. If a scene needs two numbers,
  it is two scenes.
- The last narrated scene lands the payoff the hook promised.
- The outro card is a title, not a sentence. Three to five words.

## TTS-safe phrasing

Sarvam reads what you write, literally.

- Spell numbers as words: "thirty four thousand crore", "nineteen eighty five",
  "two hundred fifty times". Digits get read inconsistently. If you must keep
  digits, the Sarvam docs ask for commas above four digits, "10,000" not "10000".
- No hyphens, ampersands, brackets, slashes, asterisks or emoji. Write "and",
  and split the sentence instead of using a dash.
- Avoid abbreviations that are read as words: write "CA" only if you want the
  letters, write "chartered accountant" if you want the phrase.
- For API and code names, write them the way they should sound: "client dot
  place order", not "client.placeorder()".
- Percentages: "six point five percent" is safer than "6.5%".
- Keep sentences under about 25 words. Long clauses make the model rush.

## Facts

- Every claim comes from the given context. Nothing is inferred, rounded or
  "commonly known".
- When the context conflicts with itself, prefer the body text over the
  headline, and tell the user which figure was used. The Jhunjhunwala article
  says 34,384 crore in the title and 34,387 crore in the body: the narration
  uses 34,387 and the title card keeps the headline figure.
- Dates carry their source: "Forbes, three July twenty twenty one", not "today".
- Do not describe a living person's current state from a dated source.

## Stat cards

The card shows what the voice cannot: exact digits.

- `value` short and numeric: `Rs 5,000`, `250x`, `6.50%`, `Rs 34,387 cr`.
- `label` upper case, under seven words, and carries the qualifier or date:
  `NET WORTH, FORBES, 3 JULY 2021`.
- At most one card per scene, and not on every scene. Four cards in six scenes
  is already busy.
- A card that repeats the narration word for word is noise. It should add the
  precision the spoken line deliberately rounded off.

## Subtitles

Subtitles are generated from `narration`, not authored separately. The text is
split into word groups (6 landscape, 4 vertical) spread evenly across the scene.
This tracks the voice closely enough without word level timestamps, which is why
scene duration must equal audio duration exactly.

Consequence: one very long word or a 40 word scene makes groups flash by. Keep
scenes inside the word budget and the subtitles stay readable.
