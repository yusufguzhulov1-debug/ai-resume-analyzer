# One sub-agent per frame

The orchestrator (you) never writes the frames of a film itself: each frame is built by its own sub-agent, in
parallel, from a bounded packet. It keeps your context clean and every frame gets a full, focused worker.

## Before dispatch

1. `STORYBOARD.md` approved, `frame.md` without placeholders, fonts and icons in `<project>/assets/`.
2. Packets built and under 48 KB each:
   `node .claude/skills/product-launch-video/scripts/frame-packets.mjs --project <project> --storyboard <project>/STORYBOARD.md`
3. Read `.claude/skills/hyperframes/references/subagent-dispatch.md` once (harness mapping, waves, waiting rule).

## The prompt

Use the template of SKILL.md (step 8) word for word, with absolute paths. It hands the worker exactly three documents:
`_role.md` (HeyGen's shared worker contract + the product-launch delta), its own packet (storyboard block, blueprint,
motion rules inlined) and `frame.md`, plus the dispatch context and the house rules of this repository. The worker never
sees the conversation, `STORYBOARD.md` or the skills: if something matters, it is in the packet or in the prompt.

Frame-specific lines to add to the dispatch context when they apply:

- **Last dark frame (before the flash)**: "End on a bright point at (LEAK_X, LEAK_Y) from <time>; the orchestrator
  floods the light from that exact point at <LEAK_AT + 0.03 - frame start> s."
- **Frame under the iris**: "The orchestrator keeps this frame mounted until <IRIS_AT + 0.80 - frame start> s: every
  internal clip and the ground must last until then. End on <object> at (IRIS_X, IRIS_Y)."
- **Handoffs**: every frame of the storyboard carries `handoff_in` / `handoff_out` (camera state, blur, world state,
  objects, light, text at the seam); they are binding for both workers: the first image of the frame is exactly its
  `handoff_in`, the last one exactly its `handoff_out`.
- **Shared world**: when `frame.md` points to an executable reference (`reference/<world>.html`), add "Copy the CSS,
  the template, the camera kit and the decor build function of reference/<world>.html verbatim (only `../assets/`
  becomes `assets/`, and the template ids take the prefix of this frame)". Frames that share a decor share the SAME
  function: check it with the diff of `method.md` § 8 once the files exist.
- **Retry**: resume the worker that built the frame (SendMessage) with the lint or check findings that name it,
  verbatim, rather than dispatching a new one; it keeps its context and costs less. A new worker only if the first one
  is gone.

## Pilot, then parallel

1. **Pilot**: dispatch frame 1 alone, in the background. When its file exists, run `bash <project>/assemble.sh` (frames not built yet are
   skipped automatically, the orchestrator layer waits for the end card), then
   `cd <project> && npx hyperframes snapshot --at <3 or 4 moments of frame 1>` and show the contact sheet to the user.
   Fix the look now (in `frame.md` if it is a style issue, then re-dispatch the pilot) before building the rest.
2. **Parallel**: dispatch every remaining frame at once, one worker each, in the background (in waves if the harness caps concurrency:
   never merge two frames into one worker). A worker takes 8 to 30 minutes.
3. **Wait on the files**: a frame is done when `<project>/compositions/frames/<frame_id>.html` exists and is a single
   `<template>...</template>`. A missing file after the worker returned: re-dispatch once with the same prompt.
4. Assemble (`bash <project>/assemble.sh`): it marks the built frames `animated`, rebuilds the index and lints.
   For every lint or check error, re-dispatch the frame concerned with the finding (or make the smallest fix yourself
   when it is one line).

## What workers must never do

Run `npx hyperframes` (any command), edit `STORYBOARD.md`, `frame.md`, `index.html` or another frame, add `<audio>`,
load a font or a script from the network, invent visible copy that the Scene lines do not quote, put an inner
`<template id>` outside the root element of the frame, or set `style.visibility = "visible"` (always `"inherit"`).
Every worker writes a complete first version of its file early, then refines it: a session cut must leave a usable
file, not half of one.
