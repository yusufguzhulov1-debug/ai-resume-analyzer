# Intake and Brand Spec

Use this schema to turn a conversational request into a production brief.

## Required

| Field | Type | Rule |
|---|---|---|
| `brand` | string | Exact public brand name |
| `creator` | string | Creator name, handle, or public role |
| `category` | string | Specific creator category |
| `services` | string[] | Two to four offers or content pillars |
| `tagline` | string | One clear point of view |
| `style` | string | Descriptive original visual thesis |
| `palette` | string[] | Three to six hex colors |
| `rhythm` | string | Semantic rhythm in four or more stages |
| `aspect` | string | `16:9`, `9:16`, or `1:1` |
| `duration` | number | Seconds; normally 5–12 |
| `engine` | string[] | One or both of `hyperframes`, `remotion` |
| `visualMode` | string | `text-illustration`, `image-assisted`, or `mixed` |
| `media` | object | Optional image assets; `images` may be empty |
| `music` | object | `uploaded` or `none` provenance |
| `timing` | object | `uploaded-music` or `designed-beat-grid` |

## Text-and-Illustration Example

```json
{
  "visualMode": "text-illustration",
  "media": {"images": []},
  "music": {
    "mode": "none",
    "source": null,
    "working": null,
    "userUploaded": false
  },
  "timing": {
    "mode": "designed-beat-grid",
    "bpm": 116,
    "beatsPerBar": 4,
    "offset": 0,
    "accentPattern": ["strong", "weak", "medium", "weak"],
    "map": "audiomap.json"
  }
}
```

## Image-and-Music Example

```json
{
  "visualMode": "image-assisted",
  "media": {
    "images": [
      {
        "role": "portrait",
        "source": "/absolute/path/to/user-portrait.png",
        "working": "assets/portrait.png",
        "origin": "user-provided"
      }
    ]
  },
  "music": {
    "mode": "uploaded",
    "source": "/absolute/path/to/user-upload.mp3",
    "working": "assets/bgm.mp3",
    "userUploaded": true,
    "segment": {"start": 0, "duration": 7}
  },
  "timing": {
    "mode": "uploaded-music",
    "map": "audiomap.json"
  }
}
```

## Missing Information

Ask for missing identity-critical copy. Images and music are optional. If images are absent, use `text-illustration`. If music is absent, use `designed-beat-grid`. Infer only reversible creative details and label them as creative choices.
