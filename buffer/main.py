import logging

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

app = FastAPI(title="Buffer Service", version="1.0.0")


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
    return {"status": "healthy", "service": "buffer"}


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
