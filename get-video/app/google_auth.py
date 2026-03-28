import json
import os
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from .config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_credentials() -> Credentials:
    settings = get_settings()
    tokens_path = settings.GOOGLE_TOKENS_PATH

    if not os.path.exists(tokens_path):
        raise FileNotFoundError(
            f"No Google tokens found at {tokens_path}. "
            "Run 'python auth_google.py' first to authenticate."
        )

    with open(tokens_path) as f:
        tokens = json.load(f)

    # Node.js googleapis stores expiry_date as epoch milliseconds
    expiry = None
    if "expiry_date" in tokens:
        expiry = datetime.fromtimestamp(tokens["expiry_date"] / 1000, tz=timezone.utc)
    elif "expiry" in tokens:
        # Python format: ISO string
        expiry = datetime.fromisoformat(tokens["expiry"])

    creds = Credentials(
        token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
        expiry=expiry,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_tokens(tokens_path, creds)

    return creds


def _save_tokens(tokens_path: str, creds: Credentials):
    with open(tokens_path) as f:
        existing = json.load(f)
    existing["access_token"] = creds.token
    if creds.expiry:
        existing["expiry_date"] = int(creds.expiry.timestamp() * 1000)
    with open(tokens_path, "w") as f:
        json.dump(existing, f, indent=2)
