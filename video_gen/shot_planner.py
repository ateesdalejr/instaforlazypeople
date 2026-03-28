"""Stage 2: Narrative → list[ShotCard] via GMI Cloud LLM."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from models import Narrative, ShotCard
from prompts import SHOT_PROMPT

DEFAULT_DURATION_SEC = 3.0


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.gmi-serving.com/v1/",
        api_key=os.getenv("GMI_API_KEY"),
    )


def plan_shots(narrative: Narrative) -> list[ShotCard]:
    """Convert a Narrative into 4-5 ShotCards ready for video generation."""
    client = _get_client()

    narrative_json = narrative.model_dump_json()

    completion = client.chat.completions.create(
        model="openai/gpt-5.4",
        messages=[
            {"role": "system", "content": SHOT_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Here is the narrative:\n\n{narrative_json}\n\n"
                    "Return a JSON object with a single key \"shots\" containing an array of exactly 5 ShotCard objects. Each shot is 3 seconds. Shots 1+2 are a contrast pair, shots 3+4 are a contrast pair, shot 5 is the solo closer."
                ),
            },
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )

    raw = json.loads(completion.choices[0].message.content)

    # The LLM may return {"shots": [...]}, {"shot_cards": [...]}, or a bare list
    if isinstance(raw, list):
        shots_data = raw
    elif isinstance(raw, dict):
        # Find the first list value in the dict
        shots_data = None
        for key in ("shots", "shot_cards"):
            if key in raw and isinstance(raw[key], list):
                shots_data = raw[key]
                break
        if shots_data is None:
            # Fallback: grab the first list value
            for v in raw.values():
                if isinstance(v, list):
                    shots_data = v
                    break
        if shots_data is None:
            # Maybe the LLM returned a single shot card as a dict
            if "shot_id" in raw:
                shots_data = [raw]
            else:
                raise ValueError(f"Could not find shot list in LLM response: {list(raw.keys())}")
    else:
        raise ValueError(f"Unexpected LLM response type: {type(raw)}")

    shots: list[ShotCard] = []
    for item in shots_data:
        if isinstance(item, dict):
            item.setdefault("duration_sec", DEFAULT_DURATION_SEC)
            shots.append(ShotCard(**item))

    return shots


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from mock_data import MOCK_EMAIL_TEXT
    from narrative_agent import generate_narrative

    print("Stage 1: generating narrative...")
    narrative = generate_narrative(MOCK_EMAIL_TEXT)
    print(f"  -> {len(narrative.acts)} acts, cold open: {narrative.cold_open[:60]}...")

    print("\nStage 2: planning shots...")
    shots = plan_shots(narrative)
    print(f"  -> {len(shots)} shots\n")

    for sc in shots:
        print(f"Shot {sc.shot_id} ({sc.duration_sec}s)")
        print(f"  Visual : {sc.visual_prompt[:80]}...")
        print(f"  VO     : {sc.voiceover_text[:80]}...")
        print(f"  Sub    : {sc.subtitle_text[:80]}...")
        print()
