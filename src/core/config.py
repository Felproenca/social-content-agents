from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"

    # Storage
    database_url: str = "sqlite+aiosqlite:///./data/agents.db"

    # Platforms
    linkedin_access_token: str = ""
    meta_access_token: str = ""
    tiktok_access_token: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
