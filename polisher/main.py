import os
import json
import redis
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from models import (
    PolishRequest,
    PolishResult,
    PolishConfig,
    ContentType,
    PolishStatus
)
from caption_agent import CaptionAgent
from caption_models import CaptionInput, CaptionAgentOutput

# Initialize FastAPI app
app = FastAPI(
    title="Polisher Service - Instagram Caption Generator",
    version="1.0.0",
    description="""
    🎨 **Polisher Service** - AI-powered Instagram caption generation using LangGraph

    ## Features
    - 🤖 Multi-node AI workflow for high-quality captions
    - 📝 Script analysis and theme extraction
    - 🎯 Attention-grabbing hooks
    - 💬 Strategic emojis and CTAs
    - #️⃣ Relevant hashtag generation

    ## Endpoints
    - `POST /captions` - Generate Instagram caption from video script
    - `GET /health` - Service health check

    ## Powered By
    - LangGraph for multi-agent workflows
    - OpenAI GPT-4 for content generation
    - Redis for caching
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Redis connection (optional — service works without it)
_redis_host = os.getenv("REDIS_HOST", "localhost")
_redis_port = int(os.getenv("REDIS_PORT", 6379))
try:
    redis_client = redis.Redis(host=_redis_host, port=_redis_port, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

# Initialize Caption Agent (lazy loaded)
_caption_agent = None


def get_caption_agent() -> CaptionAgent:
    """Get or create caption agent instance"""
    global _caption_agent
    if _caption_agent is None:
        _caption_agent = CaptionAgent()
    return _caption_agent


class PolishService:
    """Service to handle content polishing operations"""

    @staticmethod
    async def polish_content(request: PolishRequest, config: PolishConfig) -> PolishResult:
        """
        Polish content based on type and configuration
        """
        try:
            improvements = []

            # Simulate polishing process
            if config.enhance_quality:
                improvements.append("Enhanced quality")

            if config.apply_filters:
                improvements.append("Applied filters")

            if config.optimize_size:
                improvements.append("Optimized size")

            # Create result
            result = PolishResult(
                content_id=request.content_id,
                status=PolishStatus.COMPLETED,
                original_content=request.content_url or request.content_text,
                polished_content=f"polished_{request.content_url or request.content_text}",
                polished_url=f"https://polished.example.com/{request.content_id}",
                improvements=improvements,
                metadata={
                    "content_type": request.content_type.value,
                    "config": config.to_dict()
                }
            )

            # Store result in Redis (if available)
            if redis_client:
                redis_client.setex(
                    f"polish_result:{request.content_id}",
                    3600,  # 1 hour TTL
                    json.dumps(result.to_dict())
                )
                redis_client.publish("polished_content", json.dumps(result.to_dict()))

            return result

        except Exception as e:
            return PolishResult(
                content_id=request.content_id,
                status=PolishStatus.FAILED,
                error_message=str(e)
            )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    if redis_client:
        try:
            redis_client.ping()
            redis_ok = True
        except Exception:
            pass
    return {"status": "healthy", "service": "polisher", "redis": "connected" if redis_ok else "unavailable"}


@app.post("/polish")
async def polish_content(
    content_id: str,
    content_type: str,
    content_url: str = None,
    content_text: str = None,
    config: Dict[str, Any] = None
):
    """
    Polish content endpoint
    """
    try:
        # Create request
        request = PolishRequest(
            content_id=content_id,
            content_type=ContentType(content_type),
            content_url=content_url,
            content_text=content_text
        )

        # Create config
        polish_config = PolishConfig(**(config or {}))

        # Process
        result = await PolishService.polish_content(request, polish_config)

        return result.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{content_id}")
async def get_polish_result(content_id: str):
    """
    Get polishing result by content ID
    """
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis unavailable")
        result = redis_client.get(f"polish_result:{content_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        return json.loads(result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid result data")


@app.post("/caption/generate", response_model=CaptionAgentOutput)
async def generate_caption(caption_input: CaptionInput):
    """
    Generate Instagram caption from script using LangGraph agent

    Takes a video script and produces an optimized Instagram caption with:
    - Attention-grabbing hook
    - Engaging body text
    - Strategic emojis and line breaks
    - Call-to-action
    - Relevant hashtags
    """
    try:
        agent = get_caption_agent()
        result = await agent.generate_caption(caption_input)

        # Store in Redis for retrieval (if available)
        if result.success and redis_client:
            redis_client.setex(
                f"caption:{caption_input.script[:50]}",
                3600,  # 1 hour TTL
                json.dumps(result.model_dump())
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {str(e)}"
        )


@app.post("/captions")
async def create_caption(request: Request):
    """
    Generate Instagram caption from video script

    **Request Body:**
    - `script` (required): Video script text to generate caption from
    - `video_url` (required): URL of the video
    - `target_audience` (optional): Target audience description
    - `tone` (optional): Desired tone (default: "engaging")

    **Response:**
    - `caption`: Generated Instagram-ready caption with hook, body, emojis, CTA, and hashtags
    - `video`: Video URL from request
    - `metadata`: Additional generation details (hook, hashtags, character counts, etc.)

    **Example:**
    ```json
    {
        "script": "Today I'm sharing my top 3 productivity hacks...",
        "video_url": "https://example.com/video.mp4"
    }
    ```
    """
    try:
        # Manually parse request body
        body = await request.json()
        print(f"DEBUG: Raw request body: {body}")

        # Create CaptionInput from parsed JSON
        caption_input = CaptionInput(**body)
        print(f"DEBUG: Created CaptionInput: {caption_input}")

        agent = get_caption_agent()
        print(f"DEBUG: Agent created, generating caption...")

        result = await agent.generate_caption(caption_input)
        print(f"DEBUG: Caption generation result: success={result.success}")

        if not result.success:
            print(f"DEBUG: Generation failed: {result.error_message}")
            raise HTTPException(
                status_code=500,
                detail=f"Caption generation failed: {result.error_message}"
            )

        print(f"DEBUG: Returning response with caption length: {len(result.caption)}")
        return {
            "caption": result.caption,
            "video": caption_input.video_url,
            "metadata": result.metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception caught: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Run on service startup"""
    print("Polisher service starting up...")
    if redis_client:
        print("Connected to Redis")
    else:
        print("Redis unavailable — running without caching")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on service shutdown"""
    print("🛑 Polisher service shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
