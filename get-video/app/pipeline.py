from concurrent.futures import ThreadPoolExecutor

from .calendar_fetch import get_events
from .gmail import get_emails
from .merge import merge_clips
from .models import PipelineResult
from .storyboard import generate_storyboard
from .video import generate_scene_video
from .config import get_settings


def run_pipeline(days: int, max_results: int) -> PipelineResult:
    settings = get_settings()

    # Step 1: Fetch Gmail + Calendar in parallel
    with ThreadPoolExecutor(max_workers=2) as pool:
        email_future = pool.submit(get_emails, days, max_results)
        event_future = pool.submit(get_events, days)
        emails = email_future.result()
        events = event_future.result()

    # Step 2: Generate storyboard via Claude
    storyboard = generate_storyboard(emails, events)

    # Step 3: Generate video clips in parallel (one per scene)
    with ThreadPoolExecutor(max_workers=4) as pool:
        clips = list(pool.map(generate_scene_video, storyboard.scenes))

    # Step 4: Merge successful clips with ffmpeg
    successful_urls = [c.video_url for c in clips if c.video_url]
    merged_path = None
    if successful_urls:
        merged_path = merge_clips(successful_urls, settings.OUTPUT_DIR)

    return PipelineResult(
        storyboard=storyboard,
        clips=clips,
        merged_video_path=merged_path,
    )
