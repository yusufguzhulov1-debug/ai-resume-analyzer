# Copy rules

The short hard rules are in SKILL.md ("CRITICAL — truthfulness"). This file has the detail.

## Sources, in order of trust
1. The app's own strings in the target language (from the app repo, read-only). Use them for
   every word shown inside a rebuilt screen.
2. The store listing in the target storefront and language (store_assets.py).
3. The app's website in the target language.
4. The user's own notes about the app (brand rules, forbidden words, spelling).

Store screenshots can be in another language than the listing text. Rebuild the screen, but
take the words from the app's strings in the target language.

## Never
- Ratings, stars, review counts, download counts, "#1", "best", rankings.
- Percentages or money figures ("save 40 %", "save €300") unless the website states that exact
  figure — and even then prefer not to.
- People: invented names, faces, quotes, testimonials, "users say".
- "No ads" / "ad-free" / "free forever" unless the listing says exactly that. Check the Play
  labels (store_assets.py writes `contains_ads` / `in_app_purchases` only on an exact match).
- Claims that the app knows something for sure when it only suggests or asks (AI detection,
  reminders, predictions). Say "helps you …".
- Features from a roadmap, a beta, or another platform only, unless the video says so.

## Always
- The app name spelled exactly as in the store listing.
- The AI-generated label in the video's language, visible for the whole video.
- Only the store badges the app is really on (project.json `stores`).
- Per-app rules (examples of the kind: "never mention prizes", "the name is always lowercase",
  "never say ad-free") go in the project's DESIGN.md, not in this repo.
