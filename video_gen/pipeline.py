"""Full pipeline: text → narrative → shots → video clips → merged .mp4.

Returns PipelineResult matching get-video's interface.
"""

import logging

from models import PipelineResult, Storyboard, Scene, VideoClip
import narrative_agent
import shot_planner
import video_generator
import editor
from mock_data import MOCK_EMAIL_TEXT

logger = logging.getLogger(__name__)


async def run_pipeline(days: int = 1, max_results: int = 20) -> PipelineResult:
    """Run the full video generation pipeline.

    For now uses mock email text. When gmail service is live,
    replace with: requests.get(f"http://gmail:3000/data?days={days}&maxResults={max_results}")
    """

    # TODO: fetch real emails from gmail service
    raw_text = MOCK_EMAIL_TEXT

    # Stage 1: Generate narrative from raw text
    logger.info("Stage 1: Generating narrative...")
    narrative = narrative_agent.generate_narrative(raw_text)
    logger.info("  Cold open: %s", narrative.cold_open[:80])

    # Stage 2: Plan shots from narrative
    logger.info("Stage 2: Planning shots...")
    shots = shot_planner.plan_shots(narrative)
    logger.info("  %d shots planned", len(shots))

    # Build Storyboard (matching get-video format)
    scenes = [
        Scene(
            scene_number=s.shot_id,
            description=s.visual_prompt,
            duration_seconds=s.duration_sec,
        )
        for s in shots
    ]
    storyboard = Storyboard(
        title=narrative.cold_open,
        summary=narrative.closing_hook,
        scenes=scenes,
    )

    # Stage 3: Generate video clips
    logger.info("Stage 3: Generating %d video clips...", len(shots))
    segments = await video_generator.generate_videos(shots)

    # Build VideoClip list (matching get-video format)
    clips = []
    segment_map = {seg.shot_id: seg for seg in segments}
    for s in shots:
        seg = segment_map.get(s.shot_id)
        if seg:
            clips.append(VideoClip(
                scene_number=s.shot_id,
                status="completed",
                video_url=seg.video_url,
            ))
        else:
            clips.append(VideoClip(
                scene_number=s.shot_id,
                status="failed",
                error="Video generation failed",
            ))

    # Stage 4: Assemble final video
    merged_path = None
    if segments:
        logger.info("Stage 4: Assembling final video...")
        final = await editor.assemble_video(segments, shots)
        merged_path = final.video_path
        logger.info("  Merged video: %s (%.1fs)", merged_path, final.duration_sec)
    else:
        logger.warning("Stage 4: No clips to merge")

    return PipelineResult(
        storyboard=storyboard,
        clips=clips,
        merged_video_path=merged_path,
    )
