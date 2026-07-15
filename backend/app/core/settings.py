"""
Application Settings.

Central configuration for Athena AI Terminal.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = "Athena AI Terminal"

    APP_VERSION: str = "1.0.0"

    APP_ENV: str = "development"

    DEBUG: bool = True

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/athena"
    )

    DB_ECHO: bool = False

    DB_POOL_SIZE: int = 10

    DB_MAX_OVERFLOW: int = 20

    DB_POOL_RECYCLE: int = 1800

    # ==========================================================
    # MT5
    # ==========================================================

    MT5_LOGIN: int = 0

    MT5_PASSWORD: str = ""

    MT5_SERVER: str = ""

    MT5_PATH: str = ""

    DEFAULT_SYMBOL: str = "XAUUSD"

    DEFAULT_TIMEFRAME: str = "M1"

    MARKET_SYMBOLS: list[str] = [
        "XAUUSD",
    ]

    MARKET_TIMEFRAMES: list[str] = [
        "M1",
    ]

    # ==========================================================
    # Ollama
    # ==========================================================

    OLLAMA_HOST: str = "http://127.0.0.1:11434"

    OLLAMA_MODEL: str = "qwen3:8b"

    OLLAMA_TIMEOUT: int = 300

    # ==========================================================
    # Scheduler
    # ==========================================================

    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"

    COLLECTOR_INTERVAL_SECONDS: int = 60

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE: str = "logs/athena.log"

    # ==========================================================
    # API
    # ==========================================================

    API_PREFIX: str = "/api"

    API_V1_STR: str = "/api/v1"

    # ==========================================================
    # Trading
    # ==========================================================

    EXECUTION_PROVIDER: str = "paper"

    DEFAULT_VOLUME: float = 0.01

    MAX_OPEN_TRADES: int = 5

    MAX_RISK_PERCENT: float = 2.0

    RISK_REWARD_RATIO: float = 2.0

    ATR_MULTIPLIER: float = 1.5

    MAGIC_NUMBER: int = 20260712

    SLIPPAGE: int = 20

    # ==========================================================
    # AI
    # ==========================================================

    MIN_AI_CONFIDENCE: float = 70

    MIN_CONFLUENCE_SCORE: float = 60

    # ==========================================================
    # CORS
    # ==========================================================

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    """
    return Settings()


settings = get_settings()
