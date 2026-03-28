# InstaForLazyPeople

**Authenticity without the effort.**

Your emails. Your calendar. Your life — turned into a daily Instagram post while you do absolutely nothing.

InstaForLazyPeople reads your real day, writes a narrative, generates video clips, crafts a caption, and posts it. You get credit for being genuine without having to actually be genuine.

## How It Works

```
Your Gmail + Calendar
        |
   AI Storyboard -----> generates 3-4 scenes from your actual day
        |
   Video Generation ---> text-to-video clips, merged into one .mp4
        |
   Caption Polish -----> hook + body + hashtags, Instagram-ready
        |
   Auto-Post ----------> published to your socials via Buffer
```

One API call. ~5 minutes. A fully produced daily post that looks like you tried.

## The Pipeline

| Service | What it does |
|---|---|
| **get-video** | Pulls emails and calendar events, uses Claude to build a storyboard, generates video clips via GMI Cloud's text-to-video model, merges with ffmpeg |
| **polisher** | LangGraph agent chain — analyzes themes, writes captions, creates hooks, adds hashtags and CTAs |
| **buffer** | Posts the final video + caption to your configured social profiles |
| **orchestrator** | Coordinates everything, handles failures gracefully, serves the dashboard |

## Quick Start

```bash
# start everything
docker-compose up --build

# trigger the full pipeline
curl -X POST http://localhost:8000/run
```

That's it. Go be lazy.

## Configuration

Set these in your environment or `.env`:

- Google OAuth credentials (Gmail + Calendar access)
- `ANTHROPIC_API_KEY` — powers the storyboard and caption generation
- `GMI_API_KEY` — text-to-video generation
- `BUFFER_ACCESS_TOKEN` — social media posting
- `BUFFER_PROFILE_ID` — which social profile to post to

## Architecture

Five containerized services on a shared Docker network, communicating via Redis:

```
orchestrator :8000  -->  get-video :8002
                    -->  polisher  :8001
                    -->  buffer    :8003
                    -->  video_gen :8004 (alternative generator)
                    -->  redis     :6379
```

Interactive API docs available at each service's `/docs` endpoint when running.

## Why

Creating content is work. Curating an online presence is work. But your life is already interesting enough — you just don't have time to package it. This does the packaging for you.

The irony is the point: AI-generated "authenticity" that's based on your actual life. It's more real than most content out there anyway.

## License

MIT
