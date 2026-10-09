# HeyGen API Reference

Base URL: `https://api.heygen.com`
Auth Header: `X-Api-Key: <your-key>`
Get key: https://app.heygen.com/settings/api

---

## Video Agent API (v3) — AI-Driven Generation

### POST /v3/video-agents

AI handles scriptwriting, avatar selection, and visual assembly.

**Request:**
```json
{
  "prompt": "A professional woman explaining quarterly results",
  "avatar_id": "optional_avatar_id",
  "voice_id": "optional_voice_id",
  "aspect_ratio": "16:9"
}
```

**Response:**
```json
{
  "data": {
    "video_id": "abc123def456"
  }
}
```

**Cost:** $0.0333/sec (~$2/min)

---

## Studio Video API (v2) — Multi-Scene Control

### POST /v2/video/generate

Up to 50 scenes per request with per-scene avatar, voice, and background.

**Request:**
```json
{
  "video_inputs": [
    {
      "character": {
        "type": "avatar",
        "avatar_id": "Kristin_public_3_20240108",
        "avatar_style": "normal"
      },
      "voice": {
        "type": "text",
        "input_text": "Hello, welcome to our presentation.",
        "voice_id": "en-US-JennyNeural"
      },
      "background": {
        "type": "color",
        "value": "#ffffff"
      }
    }
  ],
  "dimension": {"width": 1920, "height": 1080},
  "aspect_ratio": "16:9",
  "test": false
}
```

Set `"use_avatar_iv_model": true` for Photo Avatar (Avatar IV).

**Response:**
```json
{
  "data": {
    "video_id": "abc123def456"
  }
}
```

**Cost:** $0.0167/sec for Avatar III (~$1/min)

---

## Video Status API

### GET /v2/videos/{video_id}

**Response:**
```json
{
  "data": {
    "status": "completed",
    "video_url": "https://files.heygen.ai/video/abc123.mp4",
    "duration": 30.5,
    "thumbnail_url": "https://files.heygen.ai/thumb/abc123.jpg"
  }
}
```

**Status values:** `pending` → `processing` → `completed` | `failed`

**Important:** Download URLs expire after **7 days**.

---

## Template API

### GET /v3/template/{template_id}

Retrieve template with scene-level variable placeholders.

**Response:**
```json
{
  "data": {
    "name": "Sales Outreach",
    "scenes": [
      {
        "variables": [
          {"name": "prospect_name", "type": "text", "properties": {"content": ""}},
          {"name": "company", "type": "text", "properties": {"content": ""}}
        ]
      }
    ]
  }
}
```

### POST /v2/template/generate

Generate video from template with injected variables.

**Request:**
```json
{
  "template_id": "tmpl_abc123",
  "variables": [
    {"name": "prospect_name", "type": "text", "properties": {"content": "John Smith"}},
    {"name": "company", "type": "text", "properties": {"content": "Acme Corp"}}
  ]
}
```

**Response:**
```json
{
  "data": {
    "video_id": "vid_xyz789"
  }
}
```

### GET /v2/templates

List all available templates.

---

## Translation API

### POST /v3/video-translations (preferred)

175+ languages. Explicit mode selection for speed vs precision.

**Request:**
```json
{
  "video_url": "https://files.heygen.ai/video/abc123.mp4",
  "output_language": "es",
  "mode": "speed"
}
```

**Mode values:** `"speed"` ($0.0333/sec) or `"precision"` ($0.0667/sec)

**Response:**
```json
{
  "data": {
    "video_id": "translated_vid_001"
  }
}
```

### POST /v2/video_translate (legacy, no mode parameter)

Still works but does not support speed/precision selection.

**Request:**
```json
{
  "video_url": "...",
  "output_language": "es",
  "translate_audio_only": false
}
```

---

## TTS API (Starfish)

### POST /v1/audio/text_to_speech

**Request:**
```json
{
  "text": "Hello, this is a test.",
  "voice_id": "en-US-JennyNeural",
  "speed": 1.0,
  "pitch": 0
}
```

**Response:**
```json
{
  "data": {
    "url": "https://files.heygen.ai/audio/tts_001.mp3",
    "duration": 3.2
  }
}
```

**Cost:** $0.000667/sec (~$0.04/min)

---

## Asset API

### POST /v1/asset

Upload file via multipart/form-data. Fields: `file` (required), `type` (optional: image, video, audio).

**Response:**
```json
{
  "data": {
    "asset_id": "asset_abc123",
    "url": "https://files.heygen.ai/asset/abc123.png"
  }
}
```

### GET /v1/asset/list

Query params: `?type=image&limit=50&offset=0`

**Response:**
```json
{
  "data": {
    "assets": [
      {"asset_id": "asset_001", "url": "...", "type": "image", "created_at": "..."}
    ],
    "total": 25
  }
}
```

---

## Avatar API

### GET /v2/avatars

List all available avatars.

**Response:**
```json
{
  "data": {
    "avatars": [
      {
        "avatar_id": "Kristin_public_3_20240108",
        "avatar_name": "Kristin",
        "gender": "female",
        "preview_image_url": "https://...",
        "preview_video_url": "https://..."
      }
    ]
  }
}
```

### POST /v2/photo_avatar/group

Create avatar group from uploaded photo.

**Request:**
```json
{
  "name": "My Avatar",
  "image_key": "asset_abc123"
}
```

**Response:**
```json
{
  "data": {
    "group_id": "grp_xyz789"
  }
}
```

### GET /v2/photo_avatar/group/{group_id}

Check training status.

**Response:**
```json
{
  "data": {
    "status": "completed",
    "avatars": [
      {"avatar_id": "photo_avatar_001", "avatar_name": "My Avatar"}
    ]
  }
}
```

**Training status:** `pending` → `training` → `completed` | `failed`

---

## Voice API

### GET /v2/voices

**Response:**
```json
{
  "data": {
    "voices": [
      {
        "voice_id": "en-US-JennyNeural",
        "name": "Jenny",
        "language": "English",
        "gender": "female",
        "preview_audio": "https://..."
      }
    ]
  }
}
```

---

## Webhook API

### POST /v1/webhook/endpoint.add

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["avatar_video.success", "avatar_video.fail"]
}
```

**Response:**
```json
{
  "data": {
    "webhook_id": "wh_abc123"
  }
}
```

### GET /v1/webhook/endpoint.list

### POST /v1/webhook/endpoint.delete

**Request:** `{"webhook_id": "wh_abc123"}`

**Note:** Webhook endpoints must respond to OPTIONS preflight within 1 second.

---

## User / Credits API

### GET /v2/user/remaining_quota

**Response:**
```json
{
  "error": null,
  "data": {
    "remaining_quota": 45.50,
    "details": {
      "avatar_iv_free_credit": 0,
      "b_roll_free_credit": 0,
      "generative_element_free_concept_engine_credit": 3,
      "generative_element_free_design_element_credit": 3
    }
  }
}
```

Returns remaining paid API balance in USD plus a `details` object with per-feature free-tier credits. The legacy `/v1/user/remaining_quota` returns 404 -- use v2.

---

## Constraints

| Constraint | Limit |
|-----------|-------|
| Concurrent videos | 3 (standard API plan) |
| Max video length | 30 minutes (Enterprise for longer) |
| Default resolution | 1080p (4K Enterprise only) |
| Photo Avatar max | 3 minutes |
| URL expiry | 7 days |
| Scenes per request | 50 (Studio API) |
| Min API balance | $5 pay-as-you-go |
