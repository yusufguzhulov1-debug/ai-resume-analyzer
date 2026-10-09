# Voice with ElevenLabs (Eleven v4)

The voice is the clock of the whole film: every reveal is cued on it. It is made by the user in the ElevenLabs web app
(https://elevenlabs.io), no API key, nothing to install. The agent prepares the text and explains the settings.

## Prepare the text (agent)

The validated script lives in `<project>/SCRIPT.md` in two forms: the **staged version** (the text with its staging:
the silent gag, the pivot on black, what the screen shows) and the **version to paste** in ElevenLabs, which carries no
staging at all (the voice reads everything it is given). Rules for the version to paste, with Eleven v4:

- **No pause tags**: v4 has none. Pauses come from punctuation (full stops, commas, `...`) and line breaks, one
  sentence per line. Long silences (the silent gag, the pivot) are made at the montage, never in the text.
- **Few acting tags**, in square brackets (`[sighs]`, `[dry amusement]`, `[lower, slower]`): one or two per film.
  More makes the voice unstable.
- **Numbers in letters** for the voice ("mille euros", "deux point zéro"); the screen keeps "1 000 €", "2.0".
- **Words written as they are**: v4 does not understand phonetic spelling. Write "l'IA", not `/li.a/`.
- A sentence that ends on a past participle ("lancées") can be read as an imperative: turn it another way.

Example (the flagship film, `examples/ligne-du-temps-v8/`):

```
Lundi, tu demandes une modif sur ton site.
Mercredi, le devis tombe : mille euros.
Vendredi... toujours rien.
```

## Generate (user)

1. ElevenLabs, Text to Speech, model **Eleven v4**.
2. Pick a voice from the library that fits the brand (the flagship film uses « Paul K, French Ad & Trailer Voice »).
3. Settings: Stability **40 to 50 %**, Similarity **80 to 90 %**, and the **language set explicitly** (for French: if it
   is left on automatic, the accent can drift, often to Canadian French).
4. Paste the whole text in one go (the intonation carries from one sentence to the next).
5. Generate **2 or 3 takes**, listen, keep the best one. Download it as MP3 (or WAV) and drop it as
   `<project>/assets/audio/voix.mp3`.

A paid plan is required for commercial use of the audio. Recording your own voice works the same way (quiet room,
phone close to the mouth, export MP3): the rest of the method does not change.

## After the voice

- **Montage, never regeneration, for the silences**: the silent gag (2 to 3 s), the pivot (about 1.5 s of silence),
  a breath before the end card and a tail of about 4 s. Cut only in the middle of a silence (`onsets.py --no-whisper`
  prints the cut points), 5 ms fades on every join (`build-audio.sh`, `CUTS`).
- **One wrong word in the best take** (v4 once read "l'IA" as "Lydia"): regenerate that sentence alone, splice it in
  the silences around it at the montage, then redo the timings (`method.md` § 4), since every cue after it moves.
