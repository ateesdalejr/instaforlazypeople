import logging

import httpx

from config import settings
from domain import PostResult
from exceptions import BufferAPIError
from models import CreateUpdate

logger = logging.getLogger(__name__)

CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
    createPost(input: $input) {
        ... on PostActionSuccess {
            post {
                id
                status
                text
                createdAt
            }
        }
        ... on NotFoundError { message }
        ... on UnauthorizedError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message code }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
    }
}
"""


class GraphQLClient:
    """Buffer GraphQL API client."""

    def __init__(self):
        self._url = settings.graphql_url
        self._token = settings.api_key

    async def create_post(self, request: CreateUpdate, channel_id: str) -> PostResult:
        mode = "addToQueue"
        if request.now:
            mode = "shareNow"
        elif request.top:
            mode = "shareNext"

        input_vars: dict = {
            "channelId": channel_id,
            "text": request.text or "",
            "schedulingType": "notification",
            "mode": mode,
            "metadata": {
                "instagram": {
                    "type": "post",
                    "shouldShareToFeed": True,
                },
            },
        }

        if request.scheduled_at:
            input_vars["dueAt"] = request.scheduled_at.isoformat()
            input_vars["mode"] = "customScheduled"

        # Attach media if provided
        if request.media and request.media.video:
            input_vars["assets"] = {
                "videos": [{"url": request.media.video}],
            }
            input_vars["metadata"]["instagram"]["type"] = "reel"
        elif request.media and request.media.photo:
            input_vars["assets"] = {
                "images": [{"url": request.media.photo}],
            }

        result = await self._execute(CREATE_POST_MUTATION, {"input": input_vars})

        create_post_result = result.get("createPost", {})

        # Check if it's an error type (has "message" field but no "post")
        if "message" in create_post_result:
            return PostResult(
                success=False,
                error=create_post_result["message"],
            )

        post = create_post_result.get("post", {})
        return PostResult(
            success=True,
            post_id=post.get("id"),
            status=post.get("status"),
        )

    async def _execute(self, query: str, variables: dict | None = None) -> dict:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise BufferAPIError(502, f"Buffer API unreachable: {exc}")

        if resp.status_code >= 500:
            raise BufferAPIError(resp.status_code, f"Buffer API server error: {resp.status_code}")

        if resp.status_code >= 400:
            raise BufferAPIError(resp.status_code, resp.text[:200])

        body = resp.json()
        if "errors" in body and not body.get("data"):
            msg = body["errors"][0].get("message", "Unknown GraphQL error")
            raise BufferAPIError(400, msg)

        return body.get("data", {})
