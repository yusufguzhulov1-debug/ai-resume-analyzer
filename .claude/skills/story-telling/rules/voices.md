---
name: voices
description: Complete Sarvam bulbul voice and language catalog, with picking guidance and per-language font pairing
---

# Voices and languages

Model `bulbul:v3` unless `SARVAM_MODEL` says otherwise. Speaker names are
lowercase and case sensitive: `Shubh` fails, `shubh` works.

## bulbul:v3 speakers

37 voices. All work with every supported language.

| Male | Female |
|---|---|
| shubh (default) | ritu |
| aditya | priya |
| rahul | neha |
| rohan | pooja |
| amit | simran |
| dev | kavya |
| ratan | ishita |
| varun | shreya |
| manan | roopa |
| sumit | tanya |
| kabir | shruti |
| aayan | suhani |
| ashutosh | kavitha |
| advait | rupali |
| anand | |
| tarun | |
| sunny | |
| mani | |
| gokul | |
| vijay | |
| mohit | |
| rehan | |
| soham | |

Picking a voice:

- `shubh` is the safe default: neutral Indian English, works for finance,
  technology and news explainers.
- Use a female voice when the source or the brand voice is female, or simply to
  differentiate a series. `ritu` and `priya` are the closest female equivalents
  to `shubh` in tone.
- Keep one voice per series. Switching voices between parts of the same series
  reads as a production error.
- Test before committing to a long story: generate scene 0 only, listen, then
  generate the rest. Deleting one wav and rerunning costs one call.

## bulbul:v2 speakers

Only relevant if `SARVAM_MODEL=bulbul:v2`. v2 rejects v3 speaker names.

- Female: anushka, manisha, vidya, arya
- Male: abhilash, karun, hitesh

## Languages

`languageCode` is BCP-47 and must be one of:

| Code | Language | Font to pair |
|---|---|---|
| `en-IN` | Indian English | any Latin family |
| `hi-IN` | Hindi | `AnekDevanagari` |
| `mr-IN` | Marathi | `AnekDevanagari` |
| `bn-IN` | Bengali | add a Bengali family to `fonts.ts` |
| `gu-IN` | Gujarati | add a Gujarati family |
| `kn-IN` | Kannada | add a Kannada family |
| `ml-IN` | Malayalam | add a Malayalam family |
| `od-IN` | Odia | add an Odia family |
| `pa-IN` | Punjabi | add a Gurmukhi family |
| `ta-IN` | Tamil | add a Tamil family |
| `te-IN` | Telugu | add a Telugu family |

The subtitles render the `narration` string exactly as written, so a non-Latin
script needs a font that covers it. `src/lib/fonts.ts` currently ships Latin
families plus `AnekDevanagari` (Devanagari and Latin). For any other script,
add the family there with the right `subsets` before generating, otherwise the
subtitles render as boxes while the audio is perfectly fine.

Code mixing works: Hindi narration with English product names in Latin script
is read correctly by `hi-IN`, and `AnekDevanagari` covers both scripts.

## Tuning

| Field | Range | Effect |
|---|---|---|
| `pace` | 0.5 to 2.0 | 1.05 is natural narration. Above 1.2 sounds rushed. Below 0.9 drags. |
| `temperature` | 0.01 to 2.0 | v3 only. 0.6 stable, 1.0+ more expressive but more artefacts. |
| `speech_sample_rate` | 8000 to 48000 | 24000 default. Higher only helps if the final mix is high quality. |

Not available on v3: `pitch`, `loudness`, `enable_preprocessing`. Those are v2
only and are silently ignored, which is why `cli/service.ts` branches on the
model rather than always sending them.

## Limits

- 2500 characters per request on v3, 1500 on v2. One scene is 150 to 220
  characters, so a scene never hits the limit. The generator throws before
  calling the API if a narration is too long.
- There is no word timestamp output, which is why subtitles are spread evenly
  across the scene rather than word aligned. Keep scenes inside the word budget
  in `narration.md` and this stays imperceptible.

## Fixing a voice that reads something wrong

1. Rewrite the text, do not fight the model. "CA" becomes "chartered
   accountant", "6.5%" becomes "six point five percent", "RARE" becomes "Rare".
2. Delete just that file: `public/<slug>/voice-3.wav`.
3. Rerun `npm run generate -- --slug <slug> --only voice`. Everything else is
   skipped, and the new duration is measured and written back automatically.
