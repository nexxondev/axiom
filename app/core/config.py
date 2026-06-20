"""
AXIOM Configuration
Nexxon National | Unclassified

Single source of truth for all environment config.
Pydantic-settings validates on startup — if it's
wrong, the server won't start. No silent failures.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AXIOM"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-change-in-production-minimum-64-chars-required",
        min_length=32
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
