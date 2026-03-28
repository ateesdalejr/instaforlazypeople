import json
import re

import anthropic

from .config import get_settings
from .models import Email, CalendarEvent, Storyboard


SYSTEM_PROMPT = """You are a creative director turning someone's daily email and calendar data into a short visual storyboard for a 15-20 second video. The Gmail account owner is the main character.

Rules:
- Generate exactly 3-4 scenes, each approximately 5 seconds long.
- Each scene description must be a vivid, concrete text-to-video prompt — describe exactly what the camera sees (people, setting, action, mood, lighting). No abstract concepts.
- Infer what the person actually did that day based on their emails and events. If there is a hackathon event, show them at a hackathon. If there are work emails, show them at a desk, etc.
- Do NOT include any private information (no names, email addresses, phone numbers, or company names).
- Focus on visual storytelling: capture the energy, mood, and arc of the day.
- Output ONLY valid JSON — no markdown, no explanation, just the JSON object.

Output this exact JSON schema:
{
  "title": "short title for the day's video",
  "summary": "one-sentence summary of the day",
  "scenes": [
    {
      "scene_number": 1,
      "description": "vivid text-to-video prompt",
      "duration_seconds": 5.0
    }
  ]
}"""


def _condense(emails: list[Email], events: list[CalendarEvent]) -> str:
    lines = ["=== CALENDAR EVENTS ==="]
    if events:
        for e in events:
            lines.append(f"- {e.title} at {e.start}")
    else:
        lines.append("(no events)")

    lines.append("\n=== EMAILS (subject + snippet) ===")
    if emails:
        for em in emails[:20]:  # cap at 20 to avoid token bloat
            lines.append(f"- [{em.date}] {em.subject}: {em.snippet[:150]}")
    else:
        lines.append("(no emails)")

    return "\n".join(lines)


def generate_storyboard(emails: list[Email], events: list[CalendarEvent]) -> Storyboard:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    user_message = (
        "Here is the person's Gmail and calendar data for the day. "
        "Generate a storyboard for a 15-20 second video of their day:\n\n"
        + _condense(emails, events)
    )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    return Storyboard.model_validate(data)
