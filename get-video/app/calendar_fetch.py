from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from .google_auth import get_credentials
from .models import CalendarEvent


def get_events(days_back: int, max_results: int = 50) -> list[CalendarEvent]:
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(tz=timezone.utc)

    time_min = (now - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_max = now.replace(hour=23, minute=59, second=59, microsecond=0)

    result = service.events().list(
        calendarId="primary",
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results,
    ).execute()

    events = []
    for e in result.get("items", []):
        events.append(CalendarEvent(
            id=e.get("id", ""),
            title=e.get("summary", "(No title)"),
            start=e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", ""),
            end=e.get("end", {}).get("dateTime") or e.get("end", {}).get("date", ""),
            location=e.get("location"),
            description=e.get("description"),
            attendees=[a["email"] for a in e.get("attendees", []) if "email" in a] or None,
        ))

    return events
