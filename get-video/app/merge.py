import os
import subprocess
import uuid

import requests


def merge_clips(video_urls: list[str], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    run_dir = os.path.join(output_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Download clips
    clip_paths = []
    for i, url in enumerate(video_urls):
        clip_path = os.path.join(run_dir, f"clip_{i+1:02d}.mp4")
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(clip_path, "wb") as f:
            f.write(r.content)
        clip_paths.append(clip_path)

    # Write ffmpeg concat file
    concat_file = os.path.join(run_dir, "filelist.txt")
    with open(concat_file, "w") as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")

    merged_path = os.path.join(output_dir, f"merged_{run_id}.mp4")

    # Try stream copy first (fast, no re-encode)
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c", "copy", "-movflags", "+faststart", merged_path],
        capture_output=True,
    )

    if result.returncode != 0:
        # Fallback: re-encode
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
             "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", merged_path],
            capture_output=True,
            check=True,
        )

    return merged_path
