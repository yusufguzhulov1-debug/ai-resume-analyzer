# HeyGen Avatar Types and Photo Requirements

## Avatar Types Comparison

| Type | How Created | Cost/Sec | Max Duration | Training | Best For |
|------|-----------|----------|-------------|----------|---------|
| Avatar III | Pre-built by HeyGen | $0.0167 | 30 min | None | Quick videos, standard presenters |
| Photo Avatar (IV) | User uploads photo | $0.0500 | 3 min | Minutes-hours | Custom face, personal branding |
| Digital Twin (IV) | Studio recording + consent | $0.0667 | 30 min | Hours-days | Professional, high-fidelity |

## Photo Avatar Requirements

- **Resolution**: Minimum 512x512px, recommended 1024x1024+
- **Face**: Front-facing, centered, full face visible
- **Lighting**: Even, natural lighting, no harsh shadows
- **Background**: Clean, uncluttered preferred
- **Expression**: Neutral or slight smile, mouth closed
- **Accessories**: No sunglasses, large hats, or face coverings
- **Format**: JPEG or PNG
- **File size**: Under 10MB

## Photo-to-Avatar Pipeline

1. Upload photo: `POST /v1/asset` (returns `asset_id`)
2. Create group: `POST /v2/photo_avatar/group` (returns `group_id`)
3. Poll training: `GET /v2/photo_avatar/group/{group_id}`
4. Status: `pending` → `training` → `completed`
5. Get `avatar_id` from completed response
6. Use in video generation with `use_avatar_iv_model: true`

## Voice Selection

- 100+ pre-built voices across 40+ languages
- List: `GET /v2/voices`
- Filter by language, gender
- Each has `preview_audio` URL for sampling

## Listing Avatars

- `GET /v2/avatars` returns all accessible avatars
- Fields: `avatar_id`, `avatar_name`, `gender`, `preview_image_url`
- Photo avatars appear after training completes
