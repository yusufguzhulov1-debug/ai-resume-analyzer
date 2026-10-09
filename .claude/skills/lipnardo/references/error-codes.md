# HeyGen API Error Codes and Recovery Strategies

## Error Taxonomy

| Category | HTTP Codes | Retry? | Max Retries | Strategy |
|----------|-----------|--------|-------------|----------|
| Authentication | 401, 403 | No | — | Verify API key is valid and has sufficient balance |
| Validation | 400 | No | — | Fix request body — check required fields, valid IDs |
| Rate Limiting | 429 | Yes | 3 | Exponential backoff: 2s, 4s, 8s |
| Server Error | 500, 502, 503 | Yes | 2 | Fixed 5-second delay between retries |
| Concurrent Limit | 429 (specific) | Yes | — | Wait for active video to complete, then retry |
| Generation Failed | 200 + status=failed | Maybe | 1 | Retry once with same parameters; if fails again, try different avatar |
| URL Expired | 410 or download 404 | No | — | Re-fetch video URL via GET /v2/videos/{id} |
| Polling Timeout | — | No | — | Video exceeded 30-minute max; check video length |

## Common Error Messages and Solutions

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Invalid API key" | Wrong or expired key | Regenerate at app.heygen.com/settings/api |
| "Insufficient credits" | API balance depleted | Top up at app.heygen.com |
| "Avatar not found" | Invalid avatar_id | List avatars with GET /v2/avatars |
| "Voice not found" | Invalid voice_id | List voices with GET /v2/voices |
| "Max concurrent limit reached" | 3 videos already processing | Wait for completion or upgrade plan |
| "Video generation failed" | Content policy or rendering error | Try different script/avatar combination |
| "Photo does not meet requirements" | Bad photo for avatar training | Use front-facing, well-lit, min 512x512 photo |
| "Template not found" | Invalid template_id | List templates with GET /v2/templates |
| "Invalid language code" | Unsupported translation language | Check supported languages list |

## Retry Implementation Pattern

```python
attempt = 0
while attempt < max_retries:
    try:
        result = api_call()
        break
    except RateLimitError:
        delay = (2 ** attempt) * 2  # 2s, 4s, 8s
        sleep(delay)
        attempt += 1
    except ServerError:
        sleep(5)
        attempt += 1
    except ClientError:
        raise  # Don't retry 4xx
```

## Error Handling Best Practices

- Always check HTTP status code before parsing the response body
- Log the full response body on errors for debugging
- For 429 errors, check the Retry-After header if present
- For generation failures, check the error field in the video status response
- For concurrent limit errors, poll active videos and wait for one to finish
- Never retry 401/403 errors — they indicate a configuration problem
- On repeated 500 errors, check HeyGen status page before further retries
- Store video_id immediately after creation so you can query status later even if polling fails

## Status Polling Errors

- Poll interval: 5 seconds minimum to avoid rate limiting
- Max poll duration: 30 minutes (videos rarely take longer)
- If status is "failed", the error field contains the failure reason
- If status is "processing" after 30 minutes, the video likely failed silently
- Always implement a timeout on the polling loop to avoid infinite waits
