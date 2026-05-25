"""
Application settings loaded from environment variables via pydantic-settings.

Create a `.env` file (see .env.example) — never commit real secrets.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------
    # Async PostgreSQL URL for SQLAlchemy + asyncpg
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@db:5432/classpulse

    # -----------------------------------------------------------------------
    # Redis / Message Broker
    # -----------------------------------------------------------------------
    REDIS_URL: str  # e.g. redis://redis:6379/0

    # -----------------------------------------------------------------------
    # JWT Authentication
    # -----------------------------------------------------------------------
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15    # Short-lived — rotate via refresh
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7       # Stored in Redis for revocation

    # -----------------------------------------------------------------------
    # LLM (Google Gemini)
    # -----------------------------------------------------------------------
    LLM_API_KEY: str
    LLM_MODEL: str = "gemini-2.5-flash"     # Override in .env for other models

    # -----------------------------------------------------------------------
    # Feature Flags
    # -----------------------------------------------------------------------
    # Max AI feedback calls a student can trigger per hour per assignment.
    # Enforced via Redis sliding-window rate limiting in the Celery worker.
    LLM_RATE_LIMIT_PER_HOUR: int = 5

    # -----------------------------------------------------------------------
    # SMTP / Email (optional — leave empty to disable)
    # -----------------------------------------------------------------------
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@classpulse.app"
    EMAIL_ENABLED: bool = False

    # -----------------------------------------------------------------------
    # MinIO (Object Storage)
    # -----------------------------------------------------------------------
    MINIO_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "classpulse"

    # -----------------------------------------------------------------------
    # File uploads
    # -----------------------------------------------------------------------
    UPLOAD_DIR: str = "/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000"  # Comma-separated list

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
