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
    # Authentication
    # ==========================================================

    SECRET_KEY: str = Field(
        default="dev-secret-change-in-production",
    )

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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

    MARKET_SYMBOLS: list[str] = Field(
        default_factory=lambda: [
            "XAUUSD",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "NZDUSD",
            "USDCHF",
        ],
    )

    MARKET_TIMEFRAMES: list[str] = Field(
        default_factory=lambda: [
            "M1",
            "M5",
            "M15",
        ],
    )

    COLLECTOR_INTERVALS: dict[str, int] = Field(
        default_factory=lambda: {
            "M1": 60,
            "M5": 300,
            "M15": 900,
            "M30": 1800,
            "H1": 3600,
            "H4": 14400,
            "D1": 86400,
        },
    )

    MULTI_TF_CONTEXT: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "M1": ["M5", "M15"],
            "M5": ["M15", "H1"],
            "M15": ["H1", "H4"],
            "M30": ["H1", "H4"],
            "H1": ["H4", "D1"],
            "H4": ["D1"],
            "D1": [],
        },
    )

    # ==========================================================
    # Ollama
    # ==========================================================

    OLLAMA_HOST: str = "http://127.0.0.1:11434"

    OLLAMA_MODEL: str = "qwen3:8b"

    OLLAMA_TIMEOUT: int = 300

    OLLAMA_MAX_RETRIES: int = 3

    # ==========================================================
    # Scheduler
    # ==========================================================

    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"

    COLLECTOR_INTERVAL_SECONDS: int = 60

    # ==========================================================
    # News
    # ==========================================================

    NEWS_API_KEY: str = ""

    NEWS_SYNC_INTERVAL: int = 900

    NEWS_BLOCK_MINUTES: int = 30

    NEWS_SENTIMENT_WEIGHT: int = 15

    NEWS_RSS_FEEDS: list[str] = Field(
        default_factory=lambda: [
            "https://www.forexfactory.com/ffcal_week_this.xml",
        ],
    )

    # ==========================================================
    # Learning
    # ==========================================================

    LEARNING_ENABLED: bool = True

    LEARNING_MIN_SAMPLES: int = 50

    LEARNING_RETRAIN_INTERVAL_HOURS: int = 168

    LEARNING_MODEL_PATH: str = "storage/learning"

    LEARNING_OUTCOME_HORIZON_CANDLES: int = 10

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

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ],
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    """
    return Settings()


settings = get_settings()
