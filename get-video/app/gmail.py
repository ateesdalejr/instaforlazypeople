import base64
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from googleapiclient.discovery import build

from .google_auth import get_credentials
from .models import Email


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


def _fetch_message(service, msg_id: str) -> dict:
    return service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()


def get_emails(days_back: int, max_results: int) -> list[Email]:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    q = ""
    if days_back:
        since = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        q = f"after:{since}"

    list_res = service.users().messages().list(
        userId="me",
        q=q or None,
        maxResults=max_results,
    ).execute()

    messages = list_res.get("messages", [])
    if not messages:
        return []

    # Fetch all full messages in parallel
    with ThreadPoolExecutor(max_workers=10) as pool:
        full_messages = list(pool.map(
            lambda m: _fetch_message(service, m["id"]),
            messages
        ))

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
