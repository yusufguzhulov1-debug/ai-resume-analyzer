---
name: lipnardo
description: >
  Generate AI avatar talking-head videos using HeyGen API. Single videos,
  multi-scene studio compositions, batch personalization from CSV/JSON,
  template variable injection, photo-to-avatar pipeline, video translation
  with lip-sync, Starfish TTS, credit estimation, and asset management.
  Use when user says "avatar video", "talking head", "HeyGen", "lip sync",
  "video translate", "batch video", "photo avatar", "TTS", "text to speech",
  "personalized video", "video agent", or "lipnardo".
argument-hint: "[generate|batch|template|translate|tts|avatar|assets|credits|download] [prompt or options]"
metadata:
  version: "1.0.0"
  author: AgriciDaniel
---

# Lipnardo -- HeyGen Avatar Video Production Director

## Core Principle

Act as a **Video Production Director** that orchestrates HeyGen's avatar video API.
Analyze the user's intent, select the right generation mode, estimate costs before
generating, and manage the full video lifecycle from creation through download.

## Mandatory Pre-reads

Before ANY video generation, you MUST read these references:
1. `references/heygen-api-reference.md` -- endpoint details and request/response schemas
2. `references/credit-costs.md` -- pricing table and cost estimation formulas

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/lipnardo` | Interactive -- detect intent, select mode, generate |
| `/lipnardo generate <prompt>` | Generate video with AI Video Agent (v3) |
| `/lipnardo studio <config.json>` | Multi-scene video with Studio API (v2) |
| `/lipnardo batch <file.csv>` | Batch generate from CSV/JSON data |
| `/lipnardo template list` | List available HeyGen templates |
| `/lipnardo template inspect <id>` | Show template scenes and variables |
| `/lipnardo template generate <id>` | Generate from template with variable injection |
| `/lipnardo translate <video_id> <lang>` | Translate video with lip-sync |
| `/lipnardo tts <text>` | Generate TTS audio via Starfish engine |
| `/lipnardo avatar create <photo>` | Create avatar from photo (full pipeline) |
| `/lipnardo avatar list` | List available avatars |
| `/lipnardo avatar voices` | List available voices |
| `/lipnardo assets upload <file>` | Upload asset to HeyGen |
| `/lipnardo assets list` | List uploaded assets |
| `/lipnardo credits` | Check API balance |
| `/lipnardo credits estimate` | Estimate cost before generation |
| `/lipnardo download <video_id>` | Download video before URL expires |
| `/lipnardo setup` | Validate API key and configuration |
| `/lipnardo webhook register <url>` | Register webhook endpoint |

## Setup and Authentication

First-time users must validate their setup:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_setup.py
```

API key resolution order (highest priority first):
1. `--api-key` flag on any script (explicit override)
2. `HEYGEN_API_KEY` environment variable (recommended)
3. `~/.heygen/config.json` file with `{"api_key": "your-key"}`

Get your key from: https://app.heygen.com/settings/api

## Generation Pipeline

Follow this pipeline for every video generation:

### Step 1: Analyze Intent

Determine what the user needs:
- **Simple prompt** → Video Agent mode (AI selects avatar, writes script)
- **Specific avatar/scenes** → Studio mode (precise multi-scene control)
- **Mass personalization** → Template or Batch mode
- **Existing video** → Translation or download

If the request is vague, ask about: use case, avatar preference, duration, aspect ratio.

### Step 2: Estimate Cost

ALWAYS estimate before generating:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py estimate --feature video_agent --duration 60
```

Show the user the estimated cost and confirm before proceeding.

### Step 3: Generate

**Video Agent mode** (AI-driven, simple prompt):
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py --mode agent \
  --prompt "A professional woman explaining quarterly results" \
  --aspect-ratio 16:9
```

**Studio mode** (multi-scene, precise control):
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py --mode studio \
  --config /path/to/scenes.json
```

Studio scene config format:
```json
{
  "video_inputs": [
    {
      "character": {"type": "avatar", "avatar_id": "...", "avatar_style": "normal"},
      "voice": {"type": "text", "input_text": "Script here", "voice_id": "..."},
      "background": {"type": "color", "value": "#ffffff"}
    }
  ]
}
```

### Step 4: Poll and Download

Scripts handle polling automatically with exponential backoff (10s → 60s, 30-minute ceiling).
Videos download to `~/Documents/lipnardo_videos/` by default.

### Step 5: Log Cost

After successful generation, log the cost:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py log \
  --feature video_agent --duration DURATION --video-id VIDEO_ID --prompt "summary"
```

### Step 6: Report to User

Show: file path, duration, file size, estimated cost, and video_id (for later translation/download).

## Batch Pipeline

For generating multiple personalized videos from CSV or JSON:

1. **Estimate total cost first:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py estimate-batch \
  --input data.csv --feature avatar3 --avg-duration 60
```

2. **Confirm with user** before proceeding.

3. **Run batch:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/batch_generate.py --input data.csv --mode agent
```

4. **Monitor progress** -- the script outputs JSON progress to stderr.

5. **Resume interrupted batches:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/batch_generate.py --resume manifest.json
```

CSV format for agent mode: columns `prompt` (required), `avatar_id`, `voice_id`, `name` (optional).
CSV format for template mode: columns match template variable names.

## Template Pipeline

For template-based mass personalization:

1. **List templates:** `template_video.py list`
2. **Inspect variables:** `template_video.py inspect --template-id ID`
3. **Generate with variables:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/template_video.py generate \
  --template-id ID --variables '{"name":"John","company":"Acme"}'
```
4. **Batch from CSV:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/template_video.py generate \
  --template-id ID --input prospects.csv
```

## Photo Avatar Pipeline

Full pipeline from photo to talking-head video:

1. **Create avatar from photo:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/photo_avatar.py create \
  --photo /path/to/headshot.jpg --name "My Avatar"
```
2. Training takes minutes to hours -- script waits automatically.
3. **Generate video with trained avatar:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/photo_avatar.py generate \
  --avatar-id AVATAR_ID --script "Hello, welcome to our company!"
```

Photo requirements: front-facing, 512x512 min, even lighting, mouth closed.
Photo Avatar IV costs $0.05/sec with a 3-minute max. Read `references/avatar-types.md`.

## Translation Pipeline

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/translate_video.py \
  --video-id VIDEO_ID --target-lang es --mode fast
```

- **Fast/speed mode**: speed-optimized via v3 API, $0.0333/sec
- **Quality/precision mode**: precision lip-sync via v3 API, $0.0667/sec
- 175+ languages supported

## TTS Pipeline

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/tts.py synthesize \
  --text "Hello world" --voice-id en-US-JennyNeural
python3 ${CLAUDE_SKILL_DIR}/scripts/tts.py list-voices --language en
```

## Asset Management

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/asset_manager.py upload --file image.png
python3 ${CLAUDE_SKILL_DIR}/scripts/asset_manager.py list --type image
```

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| 401 Unauthorized | Invalid API key | Run `/lipnardo setup`, re-check key |
| 429 Rate Limited | Too many requests | Script auto-retries with backoff |
| Concurrent limit | 3 videos already processing | Wait for completion |
| Generation failed | Content policy or avatar issue | Try different avatar/script |
| URL expired | Download URL > 7 days old | Re-download via `/lipnardo download` |
| Insufficient credits | API balance depleted | Top up at app.heygen.com |

Read `references/error-codes.md` for full error taxonomy and retry strategies.

## Cost Tracking

ALWAYS estimate cost before generating. ALWAYS log cost after successful generation.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py balance
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py estimate --feature avatar3 --duration 60
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py summary
```

Read `references/credit-costs.md` for full pricing table.

## Response Format

After every successful generation, report to the user:
- **Path**: where the video file was saved
- **Duration**: video length in seconds
- **Size**: file size
- **Cost**: estimated cost based on feature type and duration
- **Video ID**: for later translation, download, or reference

## API Constraints

- **3 concurrent videos** max (batch script respects this automatically)
- **30 minutes** max per video (Enterprise for longer)
- **1080p** default resolution (4K Enterprise only)
- **Photo Avatar IV**: 3 minutes max duration
- **Download URLs**: expire after 7 days -- download promptly
- **50 scenes** max per Studio API request
