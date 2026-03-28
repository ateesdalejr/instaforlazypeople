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

# Initialize FastAPI app
app = FastAPI(title="Polisher Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)


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

            # Store result in Redis
            redis_client.setex(
                f"polish_result:{request.content_id}",
                3600,  # 1 hour TTL
                json.dumps(result.to_dict())
            )

            # Publish to processor service
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
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "polisher", "redis": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


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
        result = redis_client.get(f"polish_result:{content_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        return json.loads(result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid result data")


@app.on_event("startup")
async def startup_event():
    """Run on service startup"""
    print("🎨 Polisher service starting up...")
    try:
        redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")


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
