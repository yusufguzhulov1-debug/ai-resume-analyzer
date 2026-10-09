# HeyGen Credit Costs and Estimation

## Pricing Table

| Feature | Cost/Second | Cost/Minute | Notes |
|---------|------------|------------|-------|
| Avatar III Video | $0.0167 | ~$1.00 | Standard pre-built avatars |
| Video Agent | $0.0333 | ~$2.00 | AI-driven prompt-to-video |
| Photo Avatar (IV) | $0.0500 | ~$3.00 | Custom from user photo, 3-min max |
| Digital Twin (IV) | $0.0667 | ~$4.00 | Studio-recorded avatar |
| Translation — Fast | $0.0333 | ~$2.00 | Speed-optimized |
| Translation — Quality | $0.0667 | ~$4.00 | Precision lip-sync |
| Starfish TTS | $0.000667 | ~$0.04 | Text-to-speech audio only |

## Cost Estimation Formulas

- **Single video**: cost = duration_seconds × rate_per_second
- **Batch estimation**: total_cost = num_videos × avg_duration_seconds × rate
- **Balance check**: GET /v2/user/remaining_quota returns remaining API balance in USD (legacy /v1/ path returns 404)
- **Minimum API balance**: $5 pay-as-you-go (no monthly commitment)
- **MCP credits are separate from API credits** — don't mix them

## Cost Optimization Tips

- Use Avatar III ($1/min) over Photo Avatar ($3/min) when custom face isn't needed
- Use Translation Fast ($2/min) for drafts, Quality ($4/min) for finals
- Test with --test true flag to generate watermarked videos for free
- Monitor balance with `python3 credit_check.py balance` before large batches
- Use TTS ($0.04/min) to preview audio before committing to full video generation

## Examples

| Scenario | Duration | Rate | Cost |
|----------|----------|------|------|
| 1-min Avatar III video | 60s | $0.0167/s | ~$1.00 |
| 5-min Photo Avatar video | 300s | $0.0500/s | ~$15.00 |
| 10× 2-min Avatar III batch | 1200s total | $0.0167/s | ~$20.00 |
| 3-min Quality Translation | 180s | $0.0667/s | ~$12.00 |
| 10-min TTS audio | 600s | $0.000667/s | ~$0.40 |
