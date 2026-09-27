from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


REPOSITORY_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    AVERAGE_PROCESSING_TIME_MINUTES: int = 6
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        # Resolve consistently regardless of whether commands run from the
        # repository root or backend/. Real process variables still win.
        env_file = REPOSITORY_ENV_FILE


@lru_cache()
def get_settings() -> Settings:
    return Settings()
