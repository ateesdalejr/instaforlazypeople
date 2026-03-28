import os
import json
import redis
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uvicorn
from models import (
    PolishRequest,
    PolishResult,
    PolishConfig,
    ContentType,
    PolishStatus
)
from caption_agent import CaptionAgent
from caption_models import CaptionInput, CaptionAgentOutput, CaptionResponse

# Initialize FastAPI app
app = FastAPI(title="Polisher Service", version="1.0.0")

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
async def create_caption(caption_input: CaptionInput):
    """
    POST /captions - Generate and store a caption

    Input:
    - script: Video script (required)
    - video_url: URL of the video (required)

    Output:
    - caption_id: ID for retrieving the caption
    - caption: Generated caption
    - video: Video URL
    """
    try:
        agent = get_caption_agent()
        result = await agent.generate_caption(caption_input)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Caption generation failed: {result.error_message}"
            )

        # Generate unique caption ID
        import hashlib
        caption_id = hashlib.md5(
            f"{caption_input.script}{caption_input.video_url}".encode()
        ).hexdigest()

        # Store caption data in Redis
        caption_data = {
            "caption": result.caption,
            "video": caption_input.video_url,
            "script": caption_input.script,
            "metadata": result.metadata
        }

        if redis_client:
            redis_client.setex(
                f"caption_data:{caption_id}",
                3600,  # 1 hour TTL
                json.dumps(caption_data)
            )

        return {
            "caption_id": caption_id,
            "caption": result.caption,
            "video": caption_input.video_url
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {str(e)}"
        )


@app.get("/captions/{caption_id}", response_model=CaptionResponse)
async def get_caption(caption_id: str):
    """
    GET /captions/{caption_id} - Retrieve a generated caption

    Output:
    - caption: Generated Instagram caption
    - video: Video URL
    """
    try:
        # Retrieve from Redis
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis unavailable")
        caption_data = redis_client.get(f"caption_data:{caption_id}")

        if not caption_data:
            raise HTTPException(
                status_code=404,
                detail="Caption not found or expired"
            )

        data = json.loads(caption_data)

        return CaptionResponse(
            caption=data["caption"],
            video=data["video"]
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Invalid caption data"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve caption: {str(e)}"
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
