"""Stage 1: Raw email text → Narrative structure via GMI Cloud LLM."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from models import Beat, Narrative
from prompts import NARRATIVE_PROMPT


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.gmi-serving.com/v1/",
        api_key=os.getenv("GMI_API_KEY"),
    )


def generate_narrative(text: str) -> Narrative:
    """Take raw email text and return a structured Narrative."""
    client = _get_client()

    completion = client.chat.completions.create(
        model="openai/gpt-5.4",
        messages=[
            {"role": "system", "content": NARRATIVE_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )

    raw = json.loads(completion.choices[0].message.content)

    # The LLM may wrap the object under a "narrative" key or return it directly
    data = raw.get("narrative", raw)

    return Narrative(**data)


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from mock_data import MOCK_EMAIL_TEXT

    narrative = generate_narrative(MOCK_EMAIL_TEXT)
    print("=== Cold Open ===")
    print(narrative.cold_open)
    print(f"\n=== Acts ({len(narrative.acts)}) ===")
    for i, act in enumerate(narrative.acts, 1):
        print(f"  Act {i}: {len(act)} beats")
        for b in act:
            print(f"    [{b.beat_type}] {b.summary}  (drama {b.drama_score})")
    print(f"\n=== Closing Hook ===\n{narrative.closing_hook}")
    print(f"\n=== Persona Quirks ===\n{narrative.persona_quirks}")
