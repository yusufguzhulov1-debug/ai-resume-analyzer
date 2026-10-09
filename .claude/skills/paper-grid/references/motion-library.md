# Paper-grid motion library

All components are `Reel` methods in [paper_grid.py](../scripts/paper_grid.py). Frames are reel frames. Call a component inside `with reel.scene(id, start, end):`; the scene toggles visibility, and the component owns its own entrance and action. The spoken-beat column is one example of where each fits; these are proven pieces to reach for, not a required set. Invent new artifacts when the story calls for them.

| Component | Spoken beat it serves | What moves |
|---|---|---|
| `live_chip(id, text, until)` | "Someone just dropped…" (frame 1) | Visible from the first frame; red dot pulses; leaves at `until` |
| `chip(id, text, ic, at, out, logo=, glow_at=)` | Naming a thing ("Claude skill pack", a skill name) | Slides in from the right, optional glow, slides out left |
| `post_card(id, at, drop, stack_at, autopilot_at, counts, bubbles)` | A post / "runs your LinkedIn" | Card drops or rises, lines draw, back cards fan into a pack, Autopilot toggles green, counters climb, comment bubbles pop |
| `big_number(id, text, at, chips)` | "It's free", a price, a multiplier | Hero figure springs in, chips rise, dot burst |
| `proof_list(id, img, img_w, n_rows, row_px, first_row_center, at, expand_at, focus_row)` | "Not one, it's 12" over a real list screenshot | One focused row, then the full list opens while a counter runs 1→n and a highlight sweeps the rows |
| `image_card(id, img, at, kenburns=, highlights=[(x,y,w,h,f)])` | "It's on GitHub", real artwork or page | Card rises, slow push, highlight boxes pop on their words |
| `skill_beat(id, name, ic, at, out, kind, ...)` | "One writes… one comments… one plans…" | Header chip + one card per item. `kind`: `typed` (post types, tag), `comment` (someone's post + typed draft), `reply` (question + typed reply), `profile` (old headline struck, new one rises), `week` (7 days fill with post chips) |
| `hero_chip(id, name, ic, at)` | Re-hook payoff ("the best part is the humanizer") | Large chip springs in with a ring pulse and glow |
| `flag_draft(id, at, parts, flag_frames, scan, dash_fix, shrink_at)` | "Scores the words that scream AI, caps the em dashes" | Scan line passes; flagged phrases turn red and a counter ticks; dashes flare amber and become commas; card shrinks to make room |
| `meter_rows(id, rows, at, fill_at, focus_at, note)` | "Runs it through five detectors" | Named rows fan in from alternating sides, bars fill with no numbers, rims light on "score", note chip ("Only you see this") |
| `approval(id, at, click_at)` | "Nothing goes out until you say yes" | Cursor travels to the primary button, press, button turns green, state reads approved |
| `composer(id, at, end, placeholder)` | "It can't… have something to say" | Empty composer with a blinking caret |
| `note_to_post(id, at, fields, fly_at, post_html, post_at)` | "Feed it a real note… now it's worth posting" | Note fields type, note flies into a skill chip, finished post rises with counters and a "ready" tag |
| `cta(id, keyword, at, type_span, pill_at, chips)` | "Comment KEYWORD and I'll send you…" | Comment bar types the keyword, keyword pill lands, resource chips drop in, pill floats |
| `camera_moves(face_pushes, split_settles, split_push)` | Layout changes | Face pushes for re-hooks, split pane settles on re-entry, opening push on the split, slow drift |

Low-level helpers for new components: `s` (set), `ft` (fromTo), `to`, `pop`, `rise`, `leave`, `typed`, `count`, `blink`, `add`, `css`, `image`. Keep new pieces in the same vocabulary (white card, one rim, chip with icon tile, tag, skeleton bars) and add them to the library when they prove reusable.

## Timing starting points (30 fps)

- Card or chip lands on the noun; the action lands on the verb 4–15 frames later.
- Typing: about 1–1.5 characters per frame, finishing just before the phrase ends.
- Counters: 20–50 frames with `power2.out`, starting a few frames after the card lands.
- Leave 6 frames before the next item; the next item arrives on its word.
