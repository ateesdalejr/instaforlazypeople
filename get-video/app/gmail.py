import base64
import logging
import re
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from .google_auth import get_credentials
from .models import Email

log = logging.getLogger(__name__)


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _find_part(payload: dict, mime_type: str) -> str | None:
    if not payload:
        return None
    if payload.get("mimeType") == mime_type:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        found = _find_part(part, mime_type)
        if found:
            return found
    return None


def _extract_body(payload: dict) -> str:
    body = _find_part(payload, "text/plain")
    if not body:
        html = _find_part(payload, "text/html")
        if html:
            body = re.sub(r"<[^>]+>", " ", html)
            body = re.sub(r"\s+", " ", body).strip()
    return body or "(no body)"


def _fetch_message(msg_id: str) -> dict:
    creds = get_credentials()
    svc = build("gmail", "v1", credentials=creds)
    return svc.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()


def get_emails(days_back: int, max_results: int) -> list[Email]:
    log.info("  gmail: getting credentials...")
    creds = get_credentials()
    log.info("  gmail: building service...")
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    log.info("  gmail: service ready, fetching messages...")

    q = ""
    if days_back:
        since = (datetime.now(tz=timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
        q = f"after:{since}"

    list_res = service.users().messages().list(
        userId="me",
        q=q or None,
        maxResults=max_results,
    ).execute()

    messages = list_res.get("messages", [])
    if not messages:
        return []

    full_messages = [_fetch_message(m["id"]) for m in messages]
    log.info(f"  gmail: fetched {len(full_messages)} full messages")

    emails = []
    for data in full_messages:
        headers = data.get("payload", {}).get("headers", [])
        emails.append(Email(
            id=data["id"],
            date=_get_header(headers, "Date"),
            **{"from": _get_header(headers, "From")},
            subject=_get_header(headers, "Subject"),
            snippet=data.get("snippet", ""),
            body=_extract_body(data.get("payload", {})),
        ))

    return emails
