from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_name: str = "Omni-Channel Task Manager"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tasks"
    redis_url: str = "redis://localhost:6379/0"
    events_channel: str = "tasks:events"
    cors_origins: list[str] = ["http://localhost:5173"]  

    telegram_bot_token: str = ""
    telegram_mode: Literal["polling", "webhook"] = "polling"
    telegram_webhook_url: str = "" 
    telegram_webhook_secret: str = ""
    telegram_api_base_url: str = "https://api.telegram.org"

    transcriber: Literal["gemini", "fake"] = "gemini"  
    gemini_api_key: str = ""
    whisper_model: str = "gemini-3.8-flash"
    voice_max_duration_sec: int = 120
    voice_max_file_mb: int = 20
    transcription_max_retries: int = 3
    transcription_timeout_sec: int = 60

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg2")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()