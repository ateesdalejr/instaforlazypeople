# Polisher Service - Instagram Caption Agent

A LangGraph-based AI agent that generates optimized Instagram captions from video scripts.

## Overview

The Caption Agent uses a **linear 4-node LangGraph workflow** to transform video scripts into engaging Instagram captions:

```
Script Analyzer → Caption Generator → Hook Creator → Caption Refiner
```

All inputs and outputs use **Pydantic models** for type safety and validation.

## Features

- **Script Analysis**: Extracts themes, tone, keywords, and emotional appeal
- **Caption Generation**: Creates engaging body text optimized for Instagram
- **Hook Creation**: Generates attention-grabbing opening lines
- **Caption Refinement**: Polishes with emojis, CTAs, hashtags, and formatting
- **Type-Safe**: All data validated with Pydantic models
- **Extensible**: Built on LangGraph for easy node additions

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY='your-openai-api-key'
```

## Quick Start

### Using the Python API

```python
from caption_agent import generate_instagram_caption
from caption_models import CaptionInput

# Create input with Pydantic model
caption_input = CaptionInput(
    script="""
    Hey everyone! Today I want to talk about consistency.
    You know, people always ask me what's the secret to getting fit.
    And I always tell them - it's not about being perfect, it's about showing up.
    """,
    video_url="https://storage.googleapis.com/bucket/video.mp4",
    tone="motivational"
)

# Generate caption
result = await generate_instagram_caption(
    script=caption_input.script,
    video_url=caption_input.video_url
)

if result.success:
    print(result.caption)
    print(f"Hashtags: {result.metadata['hashtags']}")
```

### Using the REST API

Start the server:
```bash
python main.py
```

Make a request:
```bash
curl -X POST http://localhost:8000/caption/generate \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Your video script here...",
    "video_url": "https://storage.googleapis.com/bucket/video.mp4",
    "tone": "engaging"
  }'
```

## Running Tests

The test suite includes 6 sample scenarios with pre-configured Pydantic models:

```bash
# Run all tests
python test_caption_agent.py

# Run a specific test
python test_caption_agent.py fitness
python test_caption_agent.py cooking
python test_caption_agent.py tech
python test_caption_agent.py travel
python test_caption_agent.py business
python test_caption_agent.py minimal
```

## LangGraph Workflow

### Node 1: Script Analyzer
**Input**: `CaptionInput`
**Output**: `ScriptAnalysis`
**Purpose**: Analyzes script to extract:
- Key themes (2-4 topics)
- Main message
- Detected tone
- Target keywords for hashtags
- Emotional appeal type

### Node 2: Caption Generator
**Input**: `ScriptAnalysis`
**Output**: `CaptionDraft`
**Purpose**: Creates initial caption body (100-150 chars) and suggests 8-12 hashtags

### Node 3: Hook Creator
**Input**: `ScriptAnalysis`, `CaptionDraft`
**Output**: `HookOutput`
**Purpose**: Generates attention-grabbing first line (30-50 chars)

### Node 4: Caption Refiner
**Input**: `HookOutput`, `CaptionDraft`, `ScriptAnalysis`
**Output**: `RefinedCaption`
**Purpose**: Assembles final caption with:
- Hook line
- Body with strategic line breaks
- 2-3 emojis
- Call-to-action
- 8-12 hashtags

## Pydantic Models

### Input Model
```python
class CaptionInput(BaseModel):
    script: str
    video_url: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = "engaging"
```

### Output Model
```python
class CaptionAgentOutput(BaseModel):
    caption: str
    metadata: dict
    script_analysis: Optional[ScriptAnalysis] = None
    success: bool = True
    error_message: Optional[str] = None
```

### State Model
```python
class CaptionAgentState(BaseModel):
    input_data: CaptionInput
    script_analysis: Optional[ScriptAnalysis] = None
    caption_draft: Optional[CaptionDraft] = None
    hook_output: Optional[HookOutput] = None
    refined_caption: Optional[RefinedCaption] = None
    created_at: datetime
    processing_errors: List[str]
```

## Architecture

```
polisher/
├── caption_agent.py         # LangGraph agent implementation
├── caption_models.py        # Pydantic models for type safety
├── test_caption_agent.py    # Test suite with sample data
├── main.py                  # FastAPI server with endpoints
├── models.py                # General service models
└── requirements.txt         # Dependencies
```

## Extension Ideas

The linear flow can be extended with:
- **Conditional routing**: Skip hook creation for certain tones
- **Iterative refinement**: Loop until quality threshold met
- **A/B testing node**: Generate multiple caption variants
- **Emoji optimization**: Analyze best emoji placement
- **Hashtag research**: Real-time hashtag performance lookup
- **Sentiment analysis**: Ensure tone matches brand voice

## API Endpoints

### `POST /caption/generate`
Generate Instagram caption from script

**Request Body**:
```json
{
  "script": "Your video script...",
  "video_url": "https://storage.googleapis.com/bucket/video.mp4",
  "target_audience": "fitness enthusiasts",
  "tone": "motivational"
}
```

**Response**:
```json
{
  "caption": "Your final Instagram caption...",
  "success": true,
  "metadata": {
    "hook": "Opening line",
    "body": "Main caption text",
    "cta": "Call to action",
    "hashtags": ["tag1", "tag2"],
    "total_length": 245,
    "line_count": 8
  },
  "script_analysis": {
    "key_themes": ["fitness", "motivation"],
    "main_message": "Consistency is key",
    "tone_detected": "inspirational"
  }
}
```

### `GET /health`
Health check endpoint

## Environment Variables

- `OPENAI_API_KEY`: Required for LLM caption generation
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)

## License

Part of the instaforlazypeople project.
