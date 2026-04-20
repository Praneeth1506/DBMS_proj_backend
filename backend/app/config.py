"""
config.py — All env-var configuration lives here.
Never access os.getenv() directly in service code; import from here.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # ── Google OAuth / Calendar / Tasks ───────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/oauth2callback"
    CALENDAR_ID: str = "primary"
    GOOGLE_TOKEN_FILE: str = "token.json"
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    # Session window — person must have left for this many seconds before a
    # new interaction is created on re-detection (grace period).
    PERSON_GRACE_PERIOD_SECONDS: int = 600          # 10 minutes
    SESSION_DURATION_MINUTES: int = 30
    FACE_SIMILARITY_THRESHOLD: float = 0.60
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 3
    MEMORY_CONTEXT_LIMIT: int = 3                   # last N interactions returned
    MAX_TRANSCRIPT_CHUNK_SIZE: int = 10000
    
    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"  # comma-separated list or "*"

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """Async database URL for async SQLAlchemy operations"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
