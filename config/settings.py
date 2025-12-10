# Configuration of secrets / database

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Central configuration object for the project.
    The idea is simple: instead of hardcoding parameters (DB credentials, API keys...),
    we load everything from environment variables. This makes the project easy to move
    across development, Docker, or cloud environments without changing the code.
    """

    # General project information
    PROJECT_NAME: str = "LLM-4-ESG-in-AM"
    ENV: str = "development"  # Can be switched to 'production' later

    # --- Database configuration ---
    # These defaults match the values inside docker-compose.yml.
    # When running locally without Docker, DB_HOST should be "localhost".
    DB_USER: str = "esg_user"
    DB_PASSWORD: str = "esg_password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "esg_db"

    # --- API Keys for LLM services ---
    # Optional during development; if not provided, the pipeline falls back to mock mode.
    OPENAI_API_KEY: Optional[str] = None

    # --- Scraper parameters ---
    # These help control network load and avoid accidental rate limits.
    SCRAPING_RATE_LIMIT_SECONDS: int = 5
    SCRAPING_TIMEOUT_SECONDS: int = 30

    class Config:
        """
        Pydantic-specific configuration:
        - Reads from .env automatically
        - Forces case sensitivity for environment variables
        - Ignores unknown fields instead of throwing errors
        """
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache
def get_settings():
    """
    Returns a cached instance of Settings.
    We only want to read the .env file once — after that, the same object is reused
    across the whole application. This improves performance and keeps configuration
    consistent everywhere.
    """
    return Settings()
