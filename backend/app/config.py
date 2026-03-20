import logging
import os

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    STOCKFISH_PATH: str = "/usr/games/stockfish"
    ANALYSIS_DEPTH: int = 12
    DATABASE_PATH: str = "/app/data/app.db"
    DEFAULT_GAME_COUNT: int = 50
    OPENAI_MODEL: str = "gpt-4o-mini"
    CHAT_HISTORY_LIMIT: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


try:
    settings = Settings()
    if not settings.OPENAI_API_KEY:
        logger.warning(
            "OPENAI_API_KEY is not set. OpenAI features will fail when used."
        )
except Exception as e:
    logger.warning("Failed to load settings: %s. Using defaults.", e)
    settings = Settings(OPENAI_API_KEY="")


def require_openai_key() -> str:
    """Return the OpenAI API key or raise a clear error."""
    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is required for this feature. "
            "Set it in your .env file or environment."
        )
    return settings.OPENAI_API_KEY
