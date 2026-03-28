"""
End-to-end test: queues a real Instagram post to Buffer.

Usage:
    uv run python test_e2e.py

Requires BUFFER_API_KEY and BUFFER_CHANNEL_ID in .env
"""

import asyncio

from config import settings
from clients.graphql_client import GraphQLClient
from models import CreateUpdate, Media


async def main():
    assert settings.api_key, "BUFFER_API_KEY not set in .env"
    assert settings.channel_id, "BUFFER_CHANNEL_ID not set in .env"

    print(f"Channel ID: {settings.channel_id}")
    print(f"GraphQL URL: {settings.graphql_url}")
    print()

    client = GraphQLClient()

    # Use a public domain test image
    request = CreateUpdate(
        profile_ids=[settings.channel_id],
        text="Automated e2e test from the buffer microservice",
        media=Media(photo="https://picsum.photos/1080/1080"),
        now=False,  # Queue it, don't publish immediately
    )

    print("Sending post to Buffer queue...")
    result = await client.create_post(request, settings.channel_id)

    print(f"Success: {result.success}")
    print(f"Post ID: {result.post_id}")
    print(f"Status:  {result.status}")
    if result.error:
        print(f"Error:   {result.error}")

    assert result.success, f"Post failed: {result.error}"
    assert result.post_id, "No post ID returned"
    print("\nE2E test passed! Post queued in Buffer.")


if __name__ == "__main__":
    asyncio.run(main())
