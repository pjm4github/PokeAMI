"""Application configuration via pydantic-settings.

References:
    - pydantic-settings documentation for BaseSettings pattern
    - Environment variable configuration for simulated AMI parameters
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    api_key: str = "dev-api-key-change-me"
    meter_count: int = 50
    data_days: int = 30
    interval_minutes: int = 15
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
