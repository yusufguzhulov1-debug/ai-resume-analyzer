# Scene routing and negative space

Choose visuals from what the sentence is doing, not from a fixed timer.

## Routing table

| Narration function | Primary visual | Supporting layer |
| --- | --- | --- |
| Hook or direct question | Presenter or content-matched hero character | One short subtitle phrase |
| Personal opinion or transition | Presenter full-screen | Optional paper label |
| Clicking a command/menu | Cropped screen | Command support card + circular PiP |
| Showing a folder/file/code | Cropped screen | Path card + circular PiP |
| Defining a concept | Paper hero acting out a concrete metaphor | Short term or definition |
| Explaining a process | Recurring character in sequential poses | Minimal nodes, arrows, or props |
| Comparing two ideas | Two poses or groups in one paper scene | One contrast label per side |
| Explaining risk or permission | Character, consequence, and gatekeeper | Warning or approval stamp |
| Summarizing a chapter | Character presenting the completed result | 2–4 concise items |
| Closing/CTA | Recurring character or presenter, then paper outro | Identity card + stamp |

## Character-first decision

For every non-screen sentence, first ask whether a person can demonstrate the idea through an action, pose, prop, or relationship. Use a pure diagram only when a character would reduce clarity, such as a precise hierarchy, numeric comparison, or software architecture.

Specify the character identity, facing direction, action, prop, shot size, and depth layer before image generation. A paper person standing beside an unrelated card does not count as character-led storytelling.

## Hybrid layout decision

Use the screen at the top and the presenter at lower right when the viewer needs both proof and human continuity. The remaining center-left area is reserved for a support card.

Select support-card content only after the character and screen composition works. Use this order:

1. Exact command being spoken.
2. Exact file or folder path being shown.
3. Current step in a short process.
4. One-sentence definition of the term on screen.
5. If none applies, leave some negative space instead of inventing decoration.

Do not repeat the subtitle word for word. The subtitle carries speech; the card carries structure.

## Timing

- Show the card 2–4 frames before the corresponding key phrase.
- Settle within 10–16 frames.
- Hold until the narration moves to the next concept.
- Replace the whole card between ideas; do not accumulate a dashboard.
- Avoid more than three readable layers at once: screen, card, presenter, subtitles already create four strong zones.

## Progressive disclosure diagrams

Build from top to bottom or left to right. Reveal only the currently discussed node. Previous nodes may remain at 60–85% opacity to preserve context. Use distinct accents for levels, but keep arrows and labels in the same ink color.

## Common failures

- Abstract concept shown only as stacked cards: design a character metaphor and action.
- Generic character reused without a relevant pose or prop: regenerate the pose from the narration beat.
- Character fused into the background: regenerate or extract it as a separate transparent asset.
- Empty center with no conceptual function: add a character action first, then a support card if information is still missing.
- Decorative scraps covering the ink landscape: remove them.
- Tiny screen recording plus large decorative title: enlarge the screen.
- Repeating the same sentence in title, card, and subtitle: keep it only in the subtitle.
- Presenter PiP hiding the final UI row: move the crop or card, not the PiP into the subtitle rail.
- Full desktop visible around the app window: crop before compositing.
