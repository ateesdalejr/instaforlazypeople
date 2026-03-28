from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google OAuth2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/oauth/callback"
    GOOGLE_TOKENS_PATH: str = "google_tokens.json"

    # GMI Cloud
    GMI_API_KEY: str
    GMI_BASE_URL: str = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"
    GMI_MODEL: str = "wan2.6-t2v"
    GMI_POLL_INTERVAL: int = 5
    GMI_POLL_TIMEOUT: int = 300

    # Anthropic
    ANTHROPIC_API_KEY: str

    # Output
    OUTPUT_DIR: str = "./output"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
