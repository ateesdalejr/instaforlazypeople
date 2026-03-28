# get-video Service API

Reads a user's Gmail and Google Calendar, generates a storyboard via Claude, produces video clips via GMI Cloud (wan2.1-t2v), merges them with ffmpeg, and returns a single .mp4 file.

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### `GET /health`

Check if the service is running.

**Response**
```json
{ "status": "ok" }
```

---

### `GET /data`

Run the full pipeline and download the merged video as an .mp4 file.

**Query Parameters**

| Parameter    | Type | Default | Description                          |
|-------------|------|---------|--------------------------------------|
| `days`       | int  | `1`     | How many days back to read emails    |
| `maxResults` | int  | `20`    | Max number of emails to fetch        |

**Response**

- `200 OK` — `video/mp4` file download (`daily_video.mp4`)
- `500` — JSON error if pipeline fails

**Example**
```bash
curl "http://localhost:8000/data?days=3&maxResults=10" -o daily_video.mp4
```

---

### `GET /data/json`

Same pipeline as `/data` but always returns JSON. Use this for debugging or when you want the storyboard and individual clip URLs without downloading the video.

**Query Parameters** — same as `/data`

**Response**
```json
{
  "storyboard": {
    "title": "Hackathon Hustle in the City",
    "summary": "A day of morning calls, an Uber ride, and an all-day AI hackathon.",
    "scenes": [
      {
        "scene_number": 1,
        "description": "Early morning, soft golden light filtering through apartment blinds...",
        "duration_seconds": 5.0
      }
    ]
  },
  "clips": [
    {
      "scene_number": 1,
      "request_id": "d82b104b-0912-4370-bbd5-3785b5b3fb1a",
      "status": "success",
      "video_url": "https://storage.gmicloud.ai/....mp4",
      "error": null
    }
  ],
  "merged_video_path": "./output/merged_a1b2c3d4.mp4"
}
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GMI_API_KEY, ANTHROPIC_API_KEY
```

### 3. Authenticate with Google

In [Google Cloud Console](https://console.cloud.google.com):
- Go to APIs & Services → Credentials → your OAuth 2.0 Client
- Add `http://localhost:8080/` to Authorized redirect URIs and save

Then run:
```bash
python auth_google.py
```
A browser window will open. After authorizing, tokens are saved to `google_tokens.json`.

### 4. Run the server
```bash
uvicorn app.main:app
```
> Do not use `--reload` — it causes the server to restart mid-request when token files are written.

### 5. Docker
```bash
docker-compose up --build
```

---

## Debugging

### Check individual clip URLs by request ID
```bash
python check_urls.py
```
Edit `check_urls.py` to add your request IDs. Useful if the server crashes mid-pipeline after clips are already generated.

---

## Pipeline

```
GET /data?days=N&maxResults=N
  │
  ├─ 1. Fetch Gmail emails (sequential) + Calendar events — ~3s
  ├─ 2. Claude API → generate 3-4 scene prompts (storyboard) — ~18s
  ├─ 3. GMI Cloud wan2.1-t2v → generate video clips (parallel) — ~2-5min
  ├─ 4. ffmpeg → merge clips into one .mp4 — ~30s
  └─ 5. Return merged video file
```

> Total time: ~3-6 minutes end to end.
