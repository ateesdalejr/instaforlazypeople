import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.environ["GMI_API_KEY"]
BASE_URL = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"

REQUEST_IDS = [
    ("Scene 1", "d82b104b-0912-4370-bbd5-3785b5b3fb1a"),
    ("Scene 2", "9192f53d-8d58-4c16-b61e-886eca7b9a44"),
    ("Scene 3", "e8799e26-1ee9-4bcc-a20c-850895d02364"),
    ("Scene 4", "3296e2df-5bf6-4fc8-99e9-9363481ba1a4"),
]

headers = {"Authorization": f"Bearer {API_KEY}"}

for name, rid in REQUEST_IDS:
    r = requests.get(f"{BASE_URL}/requests/{rid}", headers=headers)
    data = r.json()
    status = data.get("status")
    outcome = data.get("outcome", {})
    if isinstance(outcome, list):
        url = outcome[0].get("url") if outcome else None
    else:
        url = outcome.get("video_url") or outcome.get("url")
    print(f"{name} [{status}]: {url or 'not ready'}")
