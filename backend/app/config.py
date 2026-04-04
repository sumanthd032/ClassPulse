from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import list


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # LLM
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_max_calls_per_student_per_hour: int = 5

    # File storage
    upload_dir: str = "/app/uploads"
    aws_s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"

    # App
    cors_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False
    environment: str = "development"


settings = Settings()
