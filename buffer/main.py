import asyncio
import json
import logging
from contextlib import asynccontextmanager

import redis
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from clients.graphql_client import GraphQLClient
from clients.rate_limiter import PerUserRateLimiter
from config import settings
from exceptions import BufferServiceError
from models import CreateUpdate
from post_service import PostService

logger = logging.getLogger(__name__)

# --- Service instances ---
graphql_client = GraphQLClient()
rate_limiter = PerUserRateLimiter(rpm=settings.rate_limit_rpm)
post_service = PostService(graphql_client, rate_limiter)

# Redis connection
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


async def _redis_subscriber():
    """Listen on polished_content channel and post to Buffer."""
    pubsub = redis_client.pubsub()
    pubsub.subscribe("polished_content")
    logger.info("Subscribed to polished_content channel")

    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if message and message["type"] == "message":
            try:
                data = json.loads(message["data"])
                request = CreateUpdate(**data)
                result = await post_service.create_post(request)
                redis_client.publish("buffered_content", result.model_dump_json())
                logger.info("Posted to Buffer: success=%s", result.success)
            except Exception:
                logger.exception("Error processing Redis message")
        else:
            await asyncio.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_client.ping()
        logger.info("Connected to Redis at %s:%s", settings.redis_host, settings.redis_port)
        subscriber_task = asyncio.create_task(_redis_subscriber())
    except Exception as exc:
        logger.warning("Redis not available, pub/sub disabled: %s", exc)
        subscriber_task = None

    yield

    if subscriber_task:
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Buffer Service", version="1.0.0", lifespan=lifespan)


# --- Exception handler ---
@app.exception_handler(BufferServiceError)
async def buffer_error_handler(request, exc: BufferServiceError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": exc.detail,
        },
    )


# --- Health ---
@app.get("/health")
async def health():
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        pass
    return {
        "status": "healthy",
        "service": "buffer",
        "redis": "connected" if redis_ok else "disconnected",
    }


# --- Posts ---
@app.post("/v1/posts")
async def create_post(request: CreateUpdate):
    result = await post_service.create_post(request)
    return result


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
