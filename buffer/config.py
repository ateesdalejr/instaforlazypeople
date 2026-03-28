from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Buffer API (GraphQL)
    api_key: str = ""  # Buffer platform access token
    channel_id: str = ""
    graphql_url: str = "https://api.buffer.com"
    rate_limit_rpm: int = 60

    # Redis (matching monorepo convention)
    redis_host: str = "localhost"
    redis_port: int = 6379

    model_config = {"env_prefix": "BUFFER_", "env_file": ".env"}


settings = Settings()
