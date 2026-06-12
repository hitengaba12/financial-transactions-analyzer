from typing import Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: AnyUrl = Field(..., env="DATABASE_URL")
    redis_url: AnyUrl = Field(..., env="REDIS_URL")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-1.5", env="GEMINI_MODEL")
    service_name: str = Field("financial-transactions-analyzer", env="SERVICE_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    celery_task_always_eager: bool = Field(False, env="CELERY_TASK_ALWAYS_EAGER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
