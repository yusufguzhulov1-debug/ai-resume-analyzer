# Capture Workflow

Use this guide when researching a product website, logged-in app, or live workflow for a demo video.

## Research Pass

Start broad, then narrow:

1. Homepage: identify category, audience, promise, CTA, and visual language.
2. Product pages: identify the real workflow, not just benefits.
3. Pricing or plans: understand buyer segment and feature emphasis.
4. Docs, changelog, blog, or templates: find concrete use cases and language the company already uses.
5. Logged-in product, if available: capture the actual surface users will trust most.

Create a short product map:

- Product name
- Primary user
- Main job-to-be-done
- Core loop
- 3-5 features worth showing
- Proof source, if any
- CTA
- Claims that must not be made without verification

## Browser Capture Standards

Prefer crisp source assets over fixing blur later.

- Use desktop screenshots at 1920x1080 minimum; 2560x1440 or higher is better.
- Use device scale factor 2 when browser tooling supports it.
- Capture mobile separately for vertical/social variants; do not crop desktop into mobile unless the product is desktop-only and the user accepts it.
- Capture full-page screenshots for research, but use viewport screenshots for video composition.
- Capture interaction states: empty state, filled input, processing, output, result, settings, and CTA.
- Keep scrollbars and browser chrome only if they help orient the viewer; otherwise crop or frame the UI cleanly in composition.

## Logged-In Products

If the product requires login:

- Ask the user to log in through the available browser surface.
- Do not store credentials in files, manifests, or comments.
- If access fails, make a video from public evidence and clearly mark the access boundary.
- Avoid changing production data unless the user explicitly authorizes it.
- Use demo data or reversible test inputs whenever possible.

## Screenshot Manifest

Track every important screenshot:

```json
{
  "captured_at": "2026-07-01T12:00:00Z",
  "viewport": "2560x1440",
  "device_scale_factor": 2,
  "pages": [
    {
      "name": "dashboard-filled",
      "url": "https://example.com/app",
      "title": "Dashboard",
      "file": "dashboard-filled.png",
      "notes": "Primary workflow result state"
    }
  ]
}
```

## Capture Quality Checks

- Text must remain legible after the planned zoom/crop.
- Repeated feature screenshots should share the same aspect ratio and visual scale.
- Before/after screenshots should have matching width, height, zoom, and alignment.
- Cursor paths and button highlights must be based on actual UI coordinates.
- Remove accidental overlays, OS notifications, browser download bars, or capture tool UI.
