# Batch Personalized Video Example

## User Request
> "Generate personalized outreach videos for each prospect in my CSV"

## Input: prospects.csv
```csv
prompt,avatar_id,name
"Hello John, I wanted to share how our platform can help Acme Corp scale faster.",Kristin_public_3_20240108,john_acme
"Hi Sarah, TechCo's engineering team would love our developer tools.",Kristin_public_3_20240108,sarah_techco
"Welcome Marcus, let me show you what we built for companies like DataFlow.",Kristin_public_3_20240108,marcus_dataflow
```

## Claude (using Lipnardo)

### 1. Estimate batch cost
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/credit_check.py estimate-batch \
  --input prospects.csv --feature avatar3 --avg-duration 45
# Output: {"estimated_total": 2.25, "video_count": 3, "avg_duration": 45}
```

> "Estimated total: **$2.25** for 3 videos (avg 45s at $0.0167/sec). Proceed?"

### 2. Run batch
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/batch_generate.py \
  --input prospects.csv --mode agent --max-concurrent 3
```

### 3. Progress
```
{"action":"submitted","index":0,"video_id":"vid_001"}
{"action":"submitted","index":1,"video_id":"vid_002"}
{"action":"submitted","index":2,"video_id":"vid_003"}
{"polling":true,"video_id":"vid_001","video_status":"processing"}
{"action":"completed","index":0,"path":"~/Documents/lipnardo_videos/batch_.../vid_001.mp4"}
...
```

### 4. Result
All videos saved to `~/Documents/lipnardo_videos/batch_20260415_103022/`.

Manifest at `batch_manifest_20260415_103022.json` tracks every job's status for crash recovery.
