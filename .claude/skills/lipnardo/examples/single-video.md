# Single Video Generation Example

## User Request
> "Create a talking head video of a professional woman explaining our Q3 results"

## Claude (using Lipnardo)

### 1. Read references
Reads `references/credit-costs.md` and `references/heygen-api-reference.md`.

### 2. Estimate cost
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py estimate --feature video_agent --duration 60
# Output: {"estimated_cost": 2.00, "feature": "video_agent", "duration": 60}
```

> "This will cost approximately **$2.00** for a ~60 second video. Shall I proceed?"

### 3. Generate
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py --mode agent \
  --prompt "A professional woman in business attire explaining quarterly financial results. She stands in front of a modern office background, speaking clearly and confidently about revenue growth and strategic initiatives." \
  --aspect-ratio 16:9
```

### 4. Poll (automatic)
Script polls with exponential backoff: 10s, 20s, 40s, 60s...
Typical generation time: 2-5 minutes.

### 5. Download (automatic)
Video downloads to `~/Documents/lipnardo_videos/abc123.mp4`.

### 6. Log cost
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py log \
  --feature video_agent --duration 62 --video-id abc123 --prompt "Q3 results"
```

### 7. Report
> "Video saved to `~/Documents/lipnardo_videos/abc123.mp4`
> - Duration: 62 seconds
> - Size: 12.4 MB
> - Cost: ~$2.07
> - Video ID: abc123 (use for translation or re-download)"
