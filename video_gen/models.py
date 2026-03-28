from pydantic import BaseModel


# Input — just a raw string of text from the email person
class VideoGenRequest(BaseModel):
    text: str


# Stage 1: narrative_agent output
class Beat(BaseModel):
    timestamp: str         # e.g. "9:03 AM"
    summary: str           # dramatic one-liner
    raw_quote: str         # funniest line from email
    beat_type: str         # mundane | conflict | triumph | social | existential
    drama_score: int       # 1-10


class Narrative(BaseModel):
    cold_open: str         # "March 28. Against impossible odds, he opened Gmail."
    acts: list[list[Beat]] # [[act1 beats], [act2 beats], [act3 beats]]
    closing_hook: str      # "Tomorrow, he returns to the inbox."
    persona_quirks: list[str]


# Stage 2: shot_planner output
class ShotCard(BaseModel):
    shot_id: int
    visual_prompt: str     # Seedance prompt
    voiceover_text: str    # narration
    subtitle_text: str     # on-screen text
    duration_sec: float    # 3-12s (Seedance limit)


# Stage 3: video_generator output
class VideoSegment(BaseModel):
    shot_id: int
    video_url: str         # URL from Seedance
    duration_sec: float


# Stage 4: editor output
class FinalVideo(BaseModel):
    video_path: str
    duration_sec: float


# Full API response — includes video + script for downstream services
class VideoGenResponse(BaseModel):
    video_path: str
    duration_sec: float
    narrative: Narrative
    shot_cards: list[ShotCard]
