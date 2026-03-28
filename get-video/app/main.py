import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .pipeline import run_pipeline

app = FastAPI(title="Gmail Video Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data")
def data(days: int = 1, maxResults: int = 20):
    """
    Run the full pipeline and return the merged video as an .mp4 download.
    Falls back to JSON if video generation fails.
    """
    try:
        result = run_pipeline(days, maxResults)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if result.merged_video_path:
        return FileResponse(
            result.merged_video_path,
            media_type="video/mp4",
            filename="daily_video.mp4",
        )

    # Fallback if all clips failed
    return result.model_dump()


@app.get("/data/json")
def data_json(days: int = 1, maxResults: int = 20):
    """
    Same pipeline but always returns JSON — useful for debugging.
    Returns storyboard, individual clip URLs, and merged video path.
    """
    try:
        result = run_pipeline(days, maxResults)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result.model_dump()
