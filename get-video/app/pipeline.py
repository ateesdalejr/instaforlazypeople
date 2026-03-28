from concurrent.futures import ThreadPoolExecutor
import logging

from .calendar_fetch import get_events
from .gmail import get_emails
from .merge import merge_clips
from .models import PipelineResult
from .storyboard import generate_storyboard
from .video import generate_scene_video
from .config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


def run_pipeline(days: int, max_results: int) -> PipelineResult:
    settings = get_settings()

    # Step 1: Fetch Gmail + Calendar in parallel
    log.info("Step 1: Fetching emails and calendar events...")
    with ThreadPoolExecutor(max_workers=2) as pool:
        email_future = pool.submit(get_emails, days, max_results)
        event_future = pool.submit(get_events, days)
        try:
            emails = email_future.result()
            log.info(f"  Emails fetched: {len(emails)}")
        except Exception:
            log.exception("  Failed to fetch emails")
            raise
        try:
            events = event_future.result()
            log.info(f"  Events fetched: {len(events)}")
        except Exception:
            log.exception("  Failed to fetch calendar events")
            raise
    log.info(f"  Got {len(emails)} emails, {len(events)} calendar events")

    # Step 2: Generate storyboard via Claude
    log.info("Step 2: Generating storyboard with Claude...")
    storyboard = generate_storyboard(emails, events)
    log.info(f"  Storyboard: '{storyboard.title}' with {len(storyboard.scenes)} scenes")
    for s in storyboard.scenes:
        log.info(f"  Scene {s.scene_number}: {s.description[:80]}...")

    # Step 3: Generate video clips in parallel (one per scene)
    log.info("Step 3: Generating video clips via GMI Cloud...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        clips = list(pool.map(generate_scene_video, storyboard.scenes))
    for c in clips:
        if c.video_url:
            log.info(f"  Scene {c.scene_number}: done -> {c.video_url}")
        else:
            log.info(f"  Scene {c.scene_number}: FAILED -> {c.error}")

    # Step 4: Merge successful clips with ffmpeg
    successful_urls = [c.video_url for c in clips if c.video_url]
    merged_path = None
    if successful_urls:
        log.info(f"Step 4: Merging {len(successful_urls)} clips with ffmpeg...")
        merged_path = merge_clips(successful_urls, settings.OUTPUT_DIR)
        log.info(f"  Merged video: {merged_path}")
    else:
        log.info("Step 4: No successful clips to merge")

    return PipelineResult(
        storyboard=storyboard,
        clips=clips,
        merged_video_path=merged_path,
    )
