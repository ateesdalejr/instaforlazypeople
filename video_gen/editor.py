"""Stage 4: Stitch video clips + TTS voiceover + subtitles into a final video."""

import asyncio
import hashlib
import logging
import os
import tempfile
import uuid

import aiohttp
import edge_tts
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ColorClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)

from models import FinalVideo, ShotCard, VideoSegment

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def generate_tts(text: str, output_path: str, voice: str = "en-US-GuyNeural"):
    """Generate a TTS audio file using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def _download_video(session: aiohttp.ClientSession, url: str, dest: str):
    """Download a video URL to a local file (with caching)."""
    # Cache by URL hash so we never re-download
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cached = os.path.join(CACHE_DIR, f"{url_hash}.mp4")
    if os.path.isfile(cached):
        logger.info("Cache hit: %s", cached)
        # Copy to dest
        import shutil
        shutil.copy2(cached, dest)
        return

    async with session.get(url) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            async for chunk in resp.content.iter_chunked(1024 * 64):
                f.write(chunk)
    # Save to cache
    import shutil
    shutil.copy2(dest, cached)
    logger.info("Downloaded and cached: %s", cached)


def _make_subtitle_overlay(text: str, video_size: tuple, duration: float):
    """Create a subtitle overlay: small white text at bottom of frame."""
    w, h = video_size

    # Semi-transparent black strip at bottom 12%
    strip_h = int(h * 0.12)
    strip = (
        ColorClip(size=(w, strip_h), color=(0, 0, 0))
        .with_opacity(0.5)
        .with_duration(duration)
        .with_position(("center", h - strip_h))
    )

    # Smaller white text
    txt = TextClip(
        text=text,
        font_size=24,
        color="white",
        font="Arial",
        size=(w - 60, None),
        method="caption",
    )
    txt_h = txt.size[1]
    txt = (
        txt
        .with_duration(duration)
        .with_position(("center", h - strip_h + (strip_h - txt_h) // 2))
    )

    return [strip, txt]


# ---------------------------------------------------------------------------
# Main assembly
# ---------------------------------------------------------------------------

async def assemble_video(segments: list[VideoSegment], shots: list[ShotCard]) -> FinalVideo:
    """Download clips, generate TTS, overlay subtitles, and stitch into one .mp4."""

    shot_map = {sc.shot_id: sc for sc in shots}

    tmpdir = tempfile.mkdtemp(prefix="videogen_")
    video_paths: list[str] = []
    tts_paths: list[str] = []

    # --- Download videos and generate TTS in parallel ---
    async with aiohttp.ClientSession() as session:
        download_tasks = []
        tts_tasks = []

        for seg in segments:
            vpath = os.path.join(tmpdir, f"clip_{seg.shot_id}.mp4")
            video_paths.append(vpath)
            download_tasks.append(_download_video(session, seg.video_url, vpath))

            shot = shot_map[seg.shot_id]
            tpath = os.path.join(tmpdir, f"tts_{seg.shot_id}.mp3")
            tts_paths.append(tpath)
            tts_tasks.append(generate_tts(shot.voiceover_text, tpath))

        await asyncio.gather(*download_tasks, *tts_tasks)

    # --- Compose each clip: VIDEO duration is the boss ---
    composed_clips = []

    for seg, vpath, tpath in zip(segments, video_paths, tts_paths):
        shot = shot_map[seg.shot_id]

        clip = VideoFileClip(vpath)
        audio = AudioFileClip(tpath)
        vid_dur = clip.duration

        # Trim audio to video length — video is the boss
        if audio.duration > vid_dur:
            audio = audio.subclipped(0, vid_dur)

        # Subtitle = voiceover text (keep them in sync)
        subtitle_layers = _make_subtitle_overlay(shot.voiceover_text, clip.size, vid_dur)
        clip = CompositeVideoClip([clip] + subtitle_layers).with_duration(vid_dur)

        # Set voiceover audio
        clip = clip.with_audio(audio)

        composed_clips.append(clip)

    if not composed_clips:
        raise RuntimeError("No clips to assemble")

    # --- Concatenate clips (simple, no crossfade to avoid black frames) ---
    if len(composed_clips) > 1:
        final = concatenate_videoclips(composed_clips, method="chain")
    else:
        final = composed_clips[0]

    # --- Write output ---
    output_filename = f"final_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=24,
        logger=None,
    )

    total_duration = final.duration

    final.close()
    for c in composed_clips:
        c.close()

    logger.info("Final video written to %s (%.1fs)", output_path, total_duration)
    return FinalVideo(video_path=output_path, duration_sec=total_duration)
