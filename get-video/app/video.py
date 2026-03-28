import time
import logging

import requests

from .config import get_settings
from .models import Scene, VideoClip

log = logging.getLogger(__name__)


def submit_video(prompt: str) -> str:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.GMI_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{settings.GMI_BASE_URL}/requests",
        headers=headers,
        json={"model": settings.GMI_MODEL, "payload": {"prompt": prompt}},
    )
    response.raise_for_status()
    return response.json()["request_id"]


def poll_video(request_id: str) -> str:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.GMI_API_KEY}"}
    deadline = time.time() + settings.GMI_POLL_TIMEOUT

    while time.time() < deadline:
        r = requests.get(
            f"{settings.GMI_BASE_URL}/requests/{request_id}",
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()
        status = data["status"]

        if status == "success":
            outcome = data.get("outcome", {})
            # GMI returns outcome as either a list [{'url': '...'}] or a dict
            if isinstance(outcome, list):
                url = outcome[0].get("url") if outcome else None
            else:
                url = outcome.get("video_url") or outcome.get("url") or next(iter(outcome.values()), None)
            if not url:
                raise RuntimeError(f"No video URL in outcome: {outcome}")
            log.info(f"  Video URL: {url}")
            return url
        elif status in ("failed", "cancelled"):
            raise RuntimeError(f"Video generation {status} for request {request_id}")

        time.sleep(settings.GMI_POLL_INTERVAL)

    raise TimeoutError(f"Video generation timed out after {settings.GMI_POLL_TIMEOUT}s")


def generate_scene_video(scene: Scene) -> VideoClip:
    try:
        log.info(f"  Scene {scene.scene_number}: submitting to GMI Cloud...")
        request_id = submit_video(scene.description)
        log.info(f"  Scene {scene.scene_number}: request_id={request_id}, polling...")
        video_url = poll_video(request_id)
        return VideoClip(
            scene_number=scene.scene_number,
            request_id=request_id,
            status="success",
            video_url=video_url,
        )
    except Exception as e:
        return VideoClip(
            scene_number=scene.scene_number,
            status="failed",
            error=str(e),
        )
