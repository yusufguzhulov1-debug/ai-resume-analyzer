---
format: 1920x1080
duration: "{{TOTAL}}s"
message: "{{ONE_LINE_THESIS}}"
arc: Hook → Problem → Pivot → Turn → Demo → Payoff → Reassurance → CTA
audience: "{{AUDIENCE}}"
mode: autonomous
captions: disabled
music: "pre-mixed with voice and SFX in assets/audio/mix.wav (mounted at root by the orchestrator)"
direction: "{{LETTER_AND_NAME_OF_THE_CHOSEN_DIRECTION_IN_DIRECTIONS_MD}}"
styleframes: "{{styleframes/A1.png (t s), styleframes/A2.png (t s), styleframes/A3.png (t s)}}"
patterns: ../patterns/STORYBOARD-CRAFT.md, ../patterns/PATTERNS.md
---

<!--
Skeleton of the motion-design skill. Replace every {{...}} (grep -n "{{" STORYBOARD.md must print nothing), delete
this comment, and keep the exact field names: HeyGen's packet builder, assembler and transition injector parse them,
line by line (every "- key: value" field and the "Word cues:" line stay on ONE line, however long).
What each line must contain, with a filled example: templates/STORYBOARD-TEMPLATE.md (repository root). Complete film
written this way: examples/ligne-du-temps-v8/STORYBOARD.md (the flagship film) and examples/C-le-devis-v7a/STORYBOARD.md.
Grammar and 15-point grid: patterns/STORYBOARD-CRAFT.md. House rules: .claude/skills/motion-design/SKILL.md.

Timing rules (all times come from onsets.json, built on the FINAL voice montage by mots.py then onsets.py, never from
Whisper alone):
- A frame = one idea of the script, 3 to 6 s, built by one worker. Frame boundaries sit in the silences.
- Sum of all frame durations = duration above = TOTAL in assemble.sh and build-audio.sh (check it with the script of
  method.md § 6, do not trust mental math).
- Word cues and Scene times are FRAME-LOCAL: cue = global onset - frame start (onsets.py --window START END).
- A Scene is a shot: a framing between two camera moves that change subject. Steps about every 0.5 s inside it (never
  more than 1 s without an event), a camera track in every shot, no frozen hold, never the same layout for more than 3 s.
- One blueprint per frame, 1 to 3 rules (each rule id cited anywhere in the block also lands in the packet; limit 48 KB).
- transition_in: cut for every frame. The continuity is written in the image: handoff_out of frame N is copied word for
  word into handoff_in of frame N+1 (camera state, blur, world state, objects, light, text). Hard cuts (narrative voice:
  0 to 4, at act changes) write "aucun raccord de caméra (coupe franche voulue)" plus a position match on both sides.
  The light flash (dark to light) and the iris (to the end card), when used, are added by assemble.sh.
- world: dark | light. Each frame paints its own full-bleed ground as a class="clip" layer.
- Visible copy: exactly the quoted copy of the Scene lines, in the language of the voice (French: typographic ’, « »,
  non-breaking spaces before : ? !), nothing else.
-->

## Video direction

- **One world** (frame.md): {{THE_PLACE_THE_CAMERA_TRAVELS_THROUGH}}. Frames 1-{{LAST_DARK}} = PROBLEM in the dark world; frames {{FIRST_LIGHT}}-{{LAST_LIGHT}} = SOLUTION in the light world; frame {{END}} = END CARD back on the dark stage. Each frame paints its own full-bleed ground as a `class="clip"` layer.
- **Invisible seams**: every frame enters with `cut`; each seam falls at the top of the blur of a camera move and the `handoff_out` of frame N is copied word for word into the `handoff_in` of frame N+1. Wanted exceptions: {{TIME_AND_REASON_OF_EACH_HARD_CUT}}.
- **Text** (readable without sound): every sentence of the voice is a `subtitle` at the bottom center (band y 890 to 980, nothing else in it) that arrives WORD BY WORD on the timestamps given in each frame (`word@seconds`, frame-local). Exactly ONE word or group per sentence sits in the `key-word-box` (named in the Scene lines as [boîte : …]). No other colored or glowing text. Typographic moments (the sentence IS the image, centered, 84 px at most): {{2_OR_3_MOMENTS}}.
- **Peaks**: only the 3 or 4 peaks named as [trait : …] ({{PEAK_WORDS}}): a thin accent stroke or a tapered brush stroke under THE key word. No giant word, no big box.
- **One thing to look at**: in every shot the camera isolates the subject of the sentence and shows the whole only when it makes sense; a clear zoom in one direction, never a back-and-forth; side-by-side layouts with equal margins; no decor without meaning, no line crossing a sentence.
- **Real interfaces** (frame.md, from recent screenshots): {{REAL_INTERFACES}}. Uncluttered, the same device in the whole film.
- **Motion grammar**: two speeds, gestures of 1 to 6 images (expo.out) and linear drifts that never stop; the 0.3 to 0.9 s range is kept for the camera and the cursor (expo, power3 or power4); elements arrive too big and blurred then settle, never faded in at their final size; no frozen hold (every hold names its living layer); no "effect" transition.
- **Visible copy**: exactly the quoted copy of the Scene lines, nothing else.
- **Negative list**: slideshow (everything at t=0), screensaver (many things floating), doubled object, colored text instead of the box, big sentence, giant word, abstract symbol, hesitating cursor, several objects moving during a seam, any hue other than the accent except real interfaces and tool-tile brand colors.

**MONDE**
- Acte {{n}} ({{t}} à {{t}}) : {{place}} ; stations {{name (x, y)}} ; fond {{color + texture that makes the drift visible}}
- Couleurs de rôle : accent = {{what matters}} ; négatif = {{…}}

**SIGNATURES**
- Mécanisme 1 « {{name}} » : {{t1, t2, t3, t4}} (4 to 8 times)
- Mécanisme 2 « {{name}} » : {{…}}
- Registres de texte : {{subtitle word by word: one motion ; key-word box: one motion ; peak stroke: one motion ; typographic moment: one motion}}
- Rimes : {{the gesture of the end (t) replays the gesture of the start (t)}}

**PARTITION CAMÉRA** (global times) : {{t type target · t type target · …}}

**VOIX** : timings in onsets.json ; silences over 0.4 s, each written as a shot with its silent action : {{t à t (action) · …}}

**COUPES** (quota of the voice) : {{t · first word · reason}}

**RYTHME** : {{pain: shots / 10 s ; solution: shots / 10 s}}

**SON** (global times, on the gestures) : {{effect t · effect t · …}}

## Frame 1: {{TITLE_1}} · 0.00 → {{OUT_1}}

- scene: {{ONE_LINE_CAPTION_1}}
- duration: {{D1}}s
- transition_in: cut
- status: outline
- src: compositions/frames/01-{{SLUG_1}}.html
- voiceover: "{{EXACT_SENTENCES_OF_THIS_FRAME}}"
- type: hook
- blueprint: {{BLUEPRINT_ID}} (Adapt)
- focal: {{HERO_ELEMENT}}
- rules: {{RULE_1}}, {{RULE_2}}
- world: dark
- handoff_in: aucun (ouverture du film) ; première image = {{WHAT_IS_ON_SCREEN_AT_0.00: the first word or what it names, never the logo}}
- handoff_out: à {{D1}} : {{cam(x, y, scale, rx, rz) blur px ; camera move in progress and its speed ; world state ; objects on screen with position and size ; light ; text ; grain}}

Word cues: {{Word@0.00 word@0.24 word@0.78 ...}}

Scene 1 (0.00 à {{t}} s) : P1, {{this shot in a few words}}
  TEXTE ÉCRAN : subtitle « {{FIRST_WORDS}} » word by word from 0.00, [boîte : {{KEY_WORD}}] at {{t}} ; écart {{avance | synchro | aucun texte}}
  IMAGE DE DÉPART : handoff_in.
  ÉTAPES : {{t element property from → to, duration, curve ; t + 0.5 … (0.1 to 0.3 s apart in the hook)}}
  PISTE CAMÉRA : {{drift vector, %/s or u/s ; t à t move toward cam(…) curve, blur}}
  COUCHES ET PROFONDEUR : {{blurred foreground cut by the edge ; sharp subject ; background ; animated layers}}
  OBJET-PONT ET VECTEUR : {{object → new role in the next shot | vector: exit direction, duration, curve}}
  SON : {{effect at t, on the gesture}}
  IMAGE CLÉ : {{t : the thumbnail to draw, in one sentence}}

Scene 2 ({{t}} à {{D1}} s) : P2, {{…}}
  {{same eight lines}}

## Frame 2: {{TITLE_2}} · {{IN_2}} → {{OUT_2}}

- scene: {{ONE_LINE_CAPTION_2}}
- duration: {{D2}}s
- transition_in: cut
- status: outline
- src: compositions/frames/02-{{SLUG_2}}.html
- voiceover: "{{EXACT_SENTENCES_OF_THIS_FRAME}}"
- type: pain_point
- blueprint: {{BLUEPRINT_ID}} (Adapt)
- focal: {{HERO_ELEMENT}}
- rules: {{RULE_1}}, {{RULE_2}}
- world: dark
- handoff_in: à 0.00 : {{WORD_FOR_WORD_COPY_OF_THE_HANDOFF_OUT_OF_FRAME_1}}
- handoff_out: à {{D2}} : {{…}}

Word cues: {{...}}

Scene 1 (0.00 à {{t}} s) : P{{n}}, {{…}}
  {{same eight lines}}

<!-- Repeat one block per frame, then delete this comment. The pivot (a word alone, a silence, a question) ends the dark
world: a wanted hard cut, or the light flash of assemble.sh from (LEAK_X, LEAK_Y). The end of the film replays a gesture
of the start (the rhyme). -->

## Frame {{END}}: {{END_CARD_TITLE}} · {{IN_END}} → {{TOTAL}}

- scene: Back on the dark stage: the wordmark assembles, « {{PROMISE}} » lands, a cursor arrives and clicks « {{CTA_LABEL}} » directly
- duration: {{D_END}}s
- transition_in: cut
- status: outline
- src: compositions/frames/{{END}}-fin.html
- voiceover: "{{BRAND_SPOKEN_IN_LETTERS}}. {{PROMISE}}."
- type: cta
- blueprint: logo-assemble-lockup (Adapt)
- focal: the wordmark, then the CTA button
- rules: cursor-click-ripple, press-release-spring
- world: dark
- handoff_in: à 0.00 : {{WORD_FOR_WORD_COPY_OF_THE_PREVIOUS_HANDOFF_OUT}}
- handoff_out: aucun (fin du film, {{noir | iris}} à {{D_END}})

Word cues: {{...}} (hold to {{D_END}})

Scene 1 (0.00 à {{t}} s) : P{{n}}, the wordmark
  ÉTAPES : dark stage with a soft accent texture across the top third and a warm halo; the wordmark « {{WORDMARK}} » falls in letter by letter on its cue (each letter ×1.4 and blurred, sharp in 0.12 s); {{an event every 0.5 s}}.
Scene 2 ({{t}} à {{t}} s) : P{{n}}, the promise and the button
  ÉTAPES : « {{PROMISE_START}} » + [trait : {{PROMISE_END}}] on their cues; the sub-line « {{SUB_LINE}} » word by word; the CTA button « {{CTA_LABEL}} » arrives ×1.1 and blurred then settles, with the same ring as {{THE_BUTTON_EARLIER_IN_THE_FILM}} (the rhyme); mono URL « {{URL}} ».
Scene 3 ({{t}} à {{D_END}} s) : P{{n}}, the click and the living hold
  ÉTAPES : a cursor arrives in ONE curved move (0.4 to 0.5 s power3.out) and clicks directly, no hesitation; pressed state in 3 colors and a ripple, the button fills with the accent; then 2 to 3 s of living hold (drift, texture that moves), then {{black | iris}}. No frozen image.
