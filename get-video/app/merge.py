import logging
import os
import shutil
import subprocess
import uuid

import requests

log = logging.getLogger(__name__)


def merge_clips(video_urls: list[str], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    run_dir = os.path.join(output_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # --- Check ffmpeg availability ---
    ffmpeg_path = shutil.which("ffmpeg")
    log.info(f"[merge] ffmpeg binary: {ffmpeg_path}")
    if ffmpeg_path:
        version_result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True
        )
        log.info(f"[merge] ffmpeg version: {version_result.stdout.splitlines()[0] if version_result.stdout else 'unknown'}")
    else:
        log.error("[merge] ffmpeg NOT FOUND in PATH")
        log.error(f"[merge] PATH = {os.environ.get('PATH', 'unset')}")

    # --- Download clips ---
    clip_paths = []
    for i, url in enumerate(video_urls):
        clip_path = os.path.join(run_dir, f"clip_{i+1:02d}.mp4")
        log.info(f"[merge] Downloading clip {i+1}/{len(video_urls)}: {url[:80]}...")
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            with open(clip_path, "wb") as f:
                f.write(r.content)
            file_size = os.path.getsize(clip_path)
            log.info(f"[merge] Clip {i+1} saved: {clip_path} ({file_size} bytes)")
            clip_paths.append(clip_path)
        except Exception as e:
            log.error(f"[merge] Failed to download clip {i+1}: {e}")
            raise

    # --- Probe each clip ---
    for path in clip_paths:
        probe = subprocess.run(
            ["ffmpeg", "-i", path, "-f", "null", "-"],
            capture_output=True, text=True
        )
        # ffmpeg probe info goes to stderr
        probe_lines = [l for l in probe.stderr.splitlines() if "Duration" in l or "Stream" in l or "Error" in l]
        for line in probe_lines:
            log.info(f"[merge] Probe {os.path.basename(path)}: {line.strip()}")
        if probe.returncode != 0:
            log.warning(f"[merge] Probe {os.path.basename(path)} returned code {probe.returncode}")

    # --- Write ffmpeg concat file ---
    concat_file = os.path.join(run_dir, "filelist.txt")
    with open(concat_file, "w") as f:
        for path in clip_paths:
            f.write(f"file '{os.path.basename(path)}'\n")
    log.info(f"[merge] Concat file: {concat_file}")
    with open(concat_file) as f:
        log.info(f"[merge] Concat contents:\n{f.read()}")

    merged_path = os.path.join(output_dir, f"merged_{run_id}.mp4")

    # --- Try stream copy first (fast, no re-encode) ---
    copy_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", "-movflags", "+faststart", merged_path
    ]
    log.info(f"[merge] Running stream copy: {' '.join(copy_cmd)}")
    result = subprocess.run(copy_cmd, capture_output=True, text=True)
    log.info(f"[merge] Stream copy returncode: {result.returncode}")
    if result.stdout:
        log.info(f"[merge] Stream copy stdout: {result.stdout[-500:]}")
    if result.stderr:
        log.info(f"[merge] Stream copy stderr (last 1000 chars): {result.stderr[-1000:]}")

    if result.returncode != 0:
        log.warning("[merge] Stream copy failed, falling back to re-encode...")

        # --- Fallback: re-encode ---
        reencode_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", merged_path
        ]
        log.info(f"[merge] Running re-encode: {' '.join(reencode_cmd)}")
        result = subprocess.run(reencode_cmd, capture_output=True, text=True)
        log.info(f"[merge] Re-encode returncode: {result.returncode}")
        if result.stdout:
            log.info(f"[merge] Re-encode stdout: {result.stdout[-500:]}")
        if result.stderr:
            log.info(f"[merge] Re-encode stderr (last 1000 chars): {result.stderr[-1000:]}")

        if result.returncode != 0:
            log.error(f"[merge] Both ffmpeg attempts failed. Last exit code: {result.returncode}")
            log.error(f"[merge] Full stderr:\n{result.stderr}")
            raise RuntimeError(
                f"ffmpeg merge failed (exit {result.returncode}). "
                f"stderr: {result.stderr[-500:]}"
            )

    if os.path.exists(merged_path):
        log.info(f"[merge] Merged video: {merged_path} ({os.path.getsize(merged_path)} bytes)")
    else:
        log.error(f"[merge] Merged file not found at {merged_path}")

    return merged_path
