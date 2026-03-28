# Gmail & Calendar Data Service

A TypeScript/Express service that exposes Gmail and Google Calendar data over HTTP.

## Base URL
```
http://localhost:3000
```

---

## Endpoints

### GET /health
Returns service status.

**Response:**
```json
{ "status": "ok" }
```

---

### GET /data
Returns emails and calendar events for a given time window.

**Query Parameters:**

| Parameter    | Type   | Default | Description                          |
|-------------|--------|---------|--------------------------------------|
| `days`       | number | `1`     | How many days back to fetch data for |
| `maxResults` | number | `20`    | Max number of emails to return       |

**Example Request:**
```
GET /data?days=7&maxResults=10
```

**Example Response:**
```json
{
  "emails": [
    {
      "id": "18e1a2b3c4d5e6f7",
      "date": "Sat, 28 Mar 2026 12:38:05 -0700",
      "from": "Sunny Cui <sunny.work.2002@gmail.com>",
      "subject": "Hackathon github",
      "snippet": "Here is the link to the repo...",
      "body": "Full plain-text body of the email..."
    }
  ],
  "events": [
    {
      "id": "abc123xyz",
      "title": "Sunny <> Natan",
      "start": "2026-03-28T09:00:00-07:00",
      "end": "2026-03-28T09:30:00-07:00",
      "location": null,
      "description": null,
      "attendees": ["sunny@gmail.com", "natan@gmail.com"]
    }
  ]
}
```

---

## Data Models

### Email
| Field     | Type   | Description                                      |
|-----------|--------|--------------------------------------------------|
| `id`      | string | Gmail message ID                                 |
| `date`    | string | Raw date string from email header                |
| `from`    | string | Sender name and email address                    |
| `subject` | string | Email subject line                               |
| `snippet` | string | Short preview of the email body                  |
| `body`    | string | Full plain-text body (HTML tags stripped)        |

### CalendarEvent
| Field         | Type            | Description                          |
|---------------|-----------------|--------------------------------------|
| `id`          | string          | Google Calendar event ID             |
| `title`       | string          | Event title/summary                  |
| `start`       | string          | ISO 8601 start datetime              |
| `end`         | string          | ISO 8601 end datetime                |
| `location`    | string or null  | Event location if set                |
| `description` | string or null  | Event description if set             |
| `attendees`   | string[] or null| List of attendee email addresses     |

---

## Running Locally

### Prerequisites
- Node.js 20+
- `google_tokens.json` in project root (run `npm run auth:google` to generate)
- `.env` file with Google OAuth credentials

### Start the server
```bash
npm run serve
```

### Run with Docker
```bash
docker-compose up
```
The `google_tokens.json` file is mounted as a read-only volume — no credentials are baked into the image.

---

## Python Usage

Models are provided in `models.py` (requires `pydantic`):

```python
import requests
from models import DataResponse

response = requests.get("http://localhost:3000/data", params={"days": 7, "maxResults": 20})
data = DataResponse.model_validate(response.json())

for email in data.emails:
    print(f"{email.subject}: {email.body[:100]}")

for event in data.events:
    print(f"{event.title} at {event.start}")
```
