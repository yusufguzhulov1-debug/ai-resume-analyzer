---
name: demo-video-creation-skill
description: Creates high-quality SaaS and product demo videos from a company website, screenshots, app flow, or launch brief. Use whenever the user asks for product demo videos, SaaS promo videos, app walkthroughs, website-to-video conversion, launch videos, Remotion or FFmpeg video production, browser screenshots for video, or 1080p/4K demo videos, even if the only input is a URL.
---

# Demo Video Creation Skill

Create a polished product demo video from a company URL or product assets. The default output is a 60-90 second 1080p+ video; render 4K when the machine, assets, and delivery target support it.

## Operating Standard

- Base the video on the real product surface: website pages, app screens, logged-in workflows, screenshots, user-provided assets, or verified public demos.
- Treat URL-only input as enough to start. Infer the product, audience, core workflow, and brand system from the site, then ask only for missing access or high-impact preferences.
- Prefer product-manager storytelling over generic marketing. Show what problem the user has, what they do inside the product, what changes on screen, and why the outcome matters.
- Use Remotion for motion composition when practical and FFmpeg for inspection, encoding, contact sheets, audio handling, and delivery conversion.
- Keep claims defensible. Do not invent metrics, customer logos, detector results, integrations, compliance status, or pricing unless verified from source material.
- Avoid overfitting to a prior client. Reuse the workflow, quality gates, and motion patterns; do not reuse client-specific screenshots, copy, colors, pricing, personas, or version-by-version fixes.

## Inputs

If the user provides only a website URL:

1. Open the site in a browser, map the nav, value proposition, product pages, pricing, help docs, and visible interactive states.
2. Capture high-resolution screenshots of the pages and UI surfaces that best explain the product.
3. Build a narrative around the strongest product loop discovered from the site.
4. State any access boundary if a logged-in product area is required.

If the user provides more context, use it to raise quality:

- Target audience, campaign platform, aspect ratio, preferred duration, CTA, launch goal.
- Product workflow steps, demo account access, sample inputs, or expected before/after output.
- Brand assets, screenshots, video references, fonts, music direction, prohibited claims, and legal notes.

## Reference Routing

- Read `references/capture-workflow.md` before browser research, logged-in capture, or screenshot work.
- Read `references/storytelling.md` before writing the script, storyboard, shot list, or product narrative.
- Read `references/visual-system.md` before choosing motion language, typography, transitions, layout, or music.
- Read `references/remotion-ffmpeg.md` before implementing the video project or rendering files.
- Read `references/qc-checklist.md` before calling the video complete.

## Production Workflow

1. **Scope the deliverable**
   - Confirm target duration, aspect ratio, resolution, language, and delivery platform when available.
   - Default to 16:9, 60-90 seconds, 30fps, H.264 MP4, 1080p minimum.
   - Use 4K when requested or when the video will be used for launch, investor, conference, or paid ad distribution.

2. **Research the product**
   - Browse the website and product pages deeply enough to identify the core loop, not only the homepage promise.
   - Build a quick feature map: main user, pain point, primary action, visible product output, proof, CTA.
   - If the product is behind login, use the user's active browser session or ask them to log in, then continue from the authenticated UI.

3. **Capture product evidence**
   - Capture desktop screenshots at 2x or higher device scale when possible.
   - Capture filled and empty states if they explain the transformation.
   - Name assets by scene and state, such as `dashboard-empty.png`, `workflow-result.png`, `pricing.png`.
   - Keep a manifest with URL, page title, capture time, viewport, file name, and notes.

4. **Write the product story**
   - Open with the user's problem or desired outcome in plain language.
   - Move through the product loop in this order: setup, action, transformation, review/proof, broader workflow, CTA.
   - Keep text short enough for a moving video. Use captions as anchors, not paragraphs.
   - Use native-sounding copy for the audience; avoid generic AI phrases such as "unlock productivity" unless the product genuinely says that.

5. **Design the motion system**
   - Use the brand's real colors and typography as the base, then add one restrained display font or accent face if it improves hierarchy.
   - Use product screenshots as the hero assets. Add browser frames, cursor paths, zooms, masks, scan lines, comparison panels, or kinetic typography only when they clarify the workflow.
   - Choose transitions that match the product: liquid/ripple for fluid transformation, scan wipe for analysis, spotlight reveal for proof, spatial push for navigation, split comparison for before/after.
   - Keep motion continuous. Scene changes should feel like the camera or interface is moving through one product story, not separate slides.

6. **Build and render**
   - Use the starter template in `assets/remotion-starter/` when a project scaffold is useful.
   - Render review stills or a contact sheet before rendering the final video.
   - Render 1080p first for QA, then 4K final if requested.
   - Use FFmpeg or ffprobe to verify duration, resolution, codec, frame rate, and audio stream.

7. **QA before delivery**
   - Check that no text overlaps, crops awkwardly, or becomes unreadable on fast cuts.
   - Check that buttons, cursors, callouts, and masks align with the underlying UI.
   - Check that all screenshots are crisp enough at final scale.
   - Check that music is instrumental, rights-safe, and balanced under any voiceover or SFX.
   - Provide the final MP4 plus useful production artifacts: storyboard, asset manifest, contact sheet, and source project when relevant.

## Reusable Scripts

- `scripts/create_demo_brief.py` creates a structured brief from a URL and optional product context.
- `scripts/qc_video.py` inspects final video metadata with ffprobe and flags resolution, duration, codec, and audio issues.
- `scripts/make_contact_sheet.py` creates a visual contact sheet with FFmpeg for quick review.

Run scripts from a project folder or with absolute paths. They are helpers, not a replacement for visual judgment.

## Starter Template

Copy `assets/remotion-starter/` into the working project when starting a new video. Replace the placeholder config in `src/demoConfig.ts`, add screenshots to `public/` or Remotion static assets, and adapt scenes to the product narrative.

The starter is intentionally generic:

- It includes a product-story composition with opening, workflow, proof, and CTA scenes.
- It uses real screenshot slots but falls back to clean UI placeholders.
- It includes motion primitives for fades, zooms, rail movement, cursor emphasis, and comparison panels.
- It avoids client-specific copy, colors, or assets.

## Completion Bar

Do not call the video finished until these are true:

- The product story is derived from real product evidence.
- Final render is at least 1080p, or the user explicitly accepted a lower target.
- The video has been inspected visually through stills, preview render, or contact sheet.
- FFmpeg/ffprobe metadata confirms resolution, duration, video codec, and audio state.
- Any licensing or source boundary for music, fonts, stock footage, or third-party pages is documented.
- The user receives a concrete video file, not only a plan or script.
