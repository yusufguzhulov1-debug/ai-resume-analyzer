# Photo-to-Avatar Pipeline Example

## User Request
> "Create a talking head video using my headshot photo"

## Claude (using Lipnardo)

### 1. Read references
Reads `references/avatar-types.md` for photo requirements and pricing.

> "Photo Avatar IV costs **$0.05/sec** (~$3/min) with a 3-minute max.
> Your photo should be: front-facing, 512x512 min, even lighting, mouth closed."

### 2. Create avatar from photo
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/photo_avatar.py create \
  --photo ~/headshot.jpg --name "Daniel"
```

### 3. Training (automatic polling)
```
{"action":"uploading_photo","file":"~/headshot.jpg"}
{"action":"photo_uploaded","asset_id":"asset_abc123"}
{"action":"creating_avatar_group","name":"Daniel"}
{"action":"group_created","group_id":"grp_xyz789"}
{"polling_training":true,"group_id":"grp_xyz789","training_status":"training"}
...
{"polling_training":true,"group_id":"grp_xyz789","training_status":"completed"}
```

Training typically takes 5-30 minutes.

### 4. Avatar ready
```json
{
  "success": true,
  "group_id": "grp_xyz789",
  "avatar_id": "photo_avatar_daniel_001",
  "name": "Daniel"
}
```

### 5. Generate video with new avatar
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/photo_avatar.py generate \
  --avatar-id photo_avatar_daniel_001 \
  --script "Welcome to our company! I'm excited to show you what we've been working on." \
  --voice-id en-US-GuyNeural
```

### 6. Result
> "Your personalized avatar video is ready!
> - Path: `~/Documents/lipnardo_videos/def456.mp4`
> - Duration: 15 seconds
> - Cost: ~$0.75 (Photo Avatar IV at $0.05/sec)
> - Avatar ID: photo_avatar_daniel_001 (reusable for future videos)"
