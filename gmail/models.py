"""
Pydantic models matching the GET /data response from the Gmail service.

Usage:
    import requests
    from models import DataResponse

    response = requests.get("http://localhost:3000/data", params={"days": 7, "maxResults": 20})
    data = DataResponse.model_validate(response.json())

    for email in data.emails:
        print(email.subject, email.body)

    for event in data.events:
        print(event.title, event.start)
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Email(BaseModel):
    id: str
    date: str
    from_: str = None  # alias because 'from' is a Python keyword
    subject: str
    snippet: str
    body: str

    model_config = {"populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        # Map 'from' key from JSON to 'from_'
        if isinstance(obj, dict) and "from" in obj:
            obj = {**obj, "from_": obj.pop("from")}
        return super().model_validate(obj, *args, **kwargs)


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None


class DataResponse(BaseModel):
    emails: List[Email]
    events: List[CalendarEvent]
