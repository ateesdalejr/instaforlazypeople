import logging

from clients.graphql_client import GraphQLClient
from clients.rate_limiter import PerUserRateLimiter
from config import settings
from domain import PostResult
from exceptions import MissingConfigError
from models import CreateUpdate

logger = logging.getLogger(__name__)


class PostService:
    def __init__(
        self,
        graphql_client: GraphQLClient,
        rate_limiter: PerUserRateLimiter,
    ):
        self._graphql = graphql_client
        self._rate_limiter = rate_limiter

    async def create_post(self, request: CreateUpdate) -> PostResult:
        if not settings.api_key or not settings.channel_id:
            raise MissingConfigError()

        await self._rate_limiter.acquire("global")

        # Use default channel; profile_ids from the request are accepted
        # for forward compatibility but the channel_id config takes precedence for now
        channel_id = settings.channel_id

        return await self._graphql.create_post(request, channel_id)
