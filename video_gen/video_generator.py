"""
Stage 3: ShotCard[] -> VideoSegment[]

Calls the Kling v3 API via GMI Cloud to generate video clips in parallel.
"""

import os
import asyncio
import logging

from dotenv import load_dotenv
import aiohttp

load_dotenv()

from models import ShotCard, VideoSegment

logger = logging.getLogger(__name__)

BASE_URL = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"


def _get_headers() -> dict:
    api_key = os.getenv("GMI_API_KEY")
    if not api_key:
        raise RuntimeError("GMI_API_KEY environment variable is not set")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


async def _submit_shot(session: aiohttp.ClientSession, shot: ShotCard) -> str:
    """Submit a single shot to the Kling v3 API. Returns request_id."""
    payload = {
        "model": "kling-v3-text-to-video",
        "payload": {
            "prompt": shot.visual_prompt,
            "duration": "3",
            "aspect_ratio": "9:16",
            "sound": "off",
        },
    }

    async with session.post(f"{BASE_URL}/requests", json=payload) as resp:
        resp.raise_for_status()
        data = await resp.json()
        request_id = data["request_id"]
        logger.info("Shot %d submitted -> request_id=%s", shot.shot_id, request_id)
        return request_id


async def _poll_until_done(
    session: aiohttp.ClientSession,
    request_id: str,
    timeout: int = 600,
) -> dict:
    """Poll a request until status is 'success' or 'failed'. Returns full response dict."""
    url = f"{BASE_URL}/requests/{request_id}"
    elapsed = 0
    interval = 5

    while elapsed < timeout:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

        status = data.get("status")
        if status == "success":
            logger.info("Request %s succeeded", request_id)
            return data
        if status in ("failed", "cancelled"):
            logger.error("Request %s ended with status: %s", request_id, status)
            return data

        logger.debug("Request %s status=%s, waiting %ds...", request_id, status, interval)
        await asyncio.sleep(interval)
        elapsed += interval

    logger.error("Request %s timed out after %ds", request_id, timeout)
    return {"status": "failed", "error": "timeout"}


async def _process_shot(
    session: aiohttp.ClientSession,
    shot: ShotCard,
) -> VideoSegment | None:
    """Submit one shot, poll until done, and return a VideoSegment or None on failure."""
    try:
        request_id = await _submit_shot(session, shot)
        result = await _poll_until_done(session, request_id)

        if result.get("status") != "success":
            logger.error("Shot %d failed: %s", shot.shot_id, result)
            return None

        outcome = result.get("outcome", {})
        logger.info("Shot %d outcome keys: %s", shot.shot_id, list(outcome.keys()))
        logger.info("Shot %d full outcome: %s", shot.shot_id, outcome)
        # Try common keys: video_url, url, video, output_url
        video_url = outcome.get("video_url") or outcome.get("url")
        if not video_url:
            # Kling v3 returns media_urls: [{"id": "0", "url": "..."}]
            media_urls = outcome.get("media_urls", [])
            if media_urls and isinstance(media_urls, list):
                first = media_urls[0]
                video_url = first.get("url") if isinstance(first, dict) else first
        if not video_url:
            logger.error("Shot %d: could not find video URL in outcome: %s", shot.shot_id, outcome)
            return None
        return VideoSegment(
            shot_id=shot.shot_id,
            video_url=video_url,
            duration_sec=shot.duration_sec,
        )

    except Exception:
        logger.exception("Shot %d raised an exception", shot.shot_id)
        return None


async def generate_videos(shots: list[ShotCard]) -> list[VideoSegment]:
    """Generate video segments for all shots in parallel via the Seedance API."""
    async with aiohttp.ClientSession(headers=_get_headers()) as session:
        tasks = [_process_shot(session, shot) for shot in shots]
        results = await asyncio.gather(*tasks)

    segments = [seg for seg in results if seg is not None]
    logger.info("Generated %d/%d video segments", len(segments), len(shots))
    return segments


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_shot = ShotCard(
        shot_id=1,
        visual_prompt="A cinematic close-up of a person opening a laptop in a dimly lit room, soft morning light streaming through blinds, dramatic slow motion",
        voiceover_text="It was 9 AM. Against all odds, he opened his inbox.",
        subtitle_text="9:03 AM — The Inbox",
        duration_sec=5.0,
    )

    segments = asyncio.run(generate_videos([test_shot]))
    for seg in segments:
        print(seg.model_dump_json(indent=2))
