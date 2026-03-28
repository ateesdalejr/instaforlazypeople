"""
Run this script once to authenticate with Google and save tokens.

    python auth_google.py

It will print a URL — open it in your browser, authorize, then paste
the code back into the terminal. Tokens are saved to google_tokens.json.
"""

import json
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

TOKENS_PATH = "google_tokens.json"

client_config = {
    "installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback")],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

tokens = {
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    "expiry": creds.expiry.isoformat() if creds.expiry else None,
}

with open(TOKENS_PATH, "w") as f:
    json.dump(tokens, f, indent=2)

print(f"Tokens saved to {TOKENS_PATH}")
