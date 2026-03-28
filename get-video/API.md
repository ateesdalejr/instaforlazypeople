# Gmail Video Service API

Reads a user's Gmail and Google Calendar, generates a storyboard via Claude, produces video clips via GMI Cloud (wan2.6-t2v), merges them with ffmpeg, and returns a single .mp4 file.

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

Run the full pipeline and download the merged video.

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

Same pipeline as `/data` but always returns JSON. Useful for debugging or when you want the storyboard and individual clip URLs.

**Query Parameters** — same as `/data`

**Response**
```json
{
  "storyboard": {
    "title": "A Busy Wednesday",
    "summary": "A day of meetings, code reviews, and a team lunch.",
    "scenes": [
      {
        "scene_number": 1,
        "description": "A person sits at a desk in a bright open office, typing quickly on a laptop...",
        "duration_seconds": 5.0
      }
    ]
  },
  "clips": [
    {
      "scene_number": 1,
      "request_id": "abc123",
      "status": "success",
      "video_url": "https://storage.googleapis.com/...",
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
```bash
python auth_google.py
```
This opens a browser window. After authorizing, tokens are saved to `google_tokens.json`.

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

### 5. Docker
```bash
docker-compose up --build
```

---

## Pipeline

```
GET /data?days=N&maxResults=N
  │
  ├─ 1. Fetch Gmail emails + Calendar events (parallel)
  ├─ 2. Claude API → generate 3-4 scene prompts (storyboard)
  ├─ 3. GMI Cloud wan2.6-t2v → generate video clips (parallel)
  ├─ 4. ffmpeg → merge clips into one .mp4
  └─ 5. Return merged video file
```

> Note: This endpoint takes 2-5 minutes to complete due to video generation time.
