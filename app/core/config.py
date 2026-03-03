from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, Field


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    MIN_BOOKING_MINUTES: int = 15
    MAX_BOOKING_DAYS: int = 7
    PENDING_EXPIRY_MINUTES: int = 15
    REMINDER_MINUTES_BEFORE: int = 30

    FIRST_SUPERUSER_EMAIL: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()