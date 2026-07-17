"""
Application Settings.

Central configuration for Athena AI Terminal.
"""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# #region agent log
_DEBUG_LOG_PATH = Path(__file__).resolve().parents[3] / "debug-0dd6e1.log"


def _agent_debug_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict,
    run_id: str = "pre-fix",
) -> None:
    payload = {
        "sessionId": "0dd6e1",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with _DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass


# #endregion


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

    DEFAULT_TIMEFRAME: str = "M5"

    MARKET_SYMBOLS: list[str] = Field(
        default_factory=lambda: [
            "XAUUSD",
            "XAGUSD",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "NZDUSD",
            "USDCHF",
            "EURJPY",
            "GBPJPY",
            "EURGBP",
            "BTCUSD",
            "ETHUSD",
            "SOLUSD",
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
    # AI Provider (provider-agnostic)
    # ==========================================================

    AI_PROVIDER: str = "gemini"

    AI_FALLBACK_PROVIDER: str = "local"

    AI_TIMEOUT: int = 60

    AI_MAX_RETRIES: int = 3

    AI_CACHE_TTL_SECONDS: int = 3600

    REDIS_URL: str = "redis://localhost:6379/0"

    GEMINI_API_KEY: str = ""

    GEMINI_MODEL: str = "gemini-2.0-flash"

    GEMINI_EMBED_MODEL: str = "text-embedding-004"

    OPENAI_API_KEY: str = ""

    OPENAI_MODEL: str = "gpt-4o-mini"

    AI_BASE_URL: str = ""

    ANTHROPIC_API_KEY: str = ""

    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # ==========================================================
    # Ollama (local provider)
    # ==========================================================

    OLLAMA_HOST: str = "http://127.0.0.1:11434"

    OLLAMA_MODEL: str = "llama3.2"

    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

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

    # Legacy ATR multiplier (kept for backward-compatible wrappers).
    ATR_MULTIPLIER: float = 2.0

    # Legacy global pip floor (unused by institutional risk engine).
    MIN_STOP_PIPS: float = 15.0

    # Institutional risk engine thresholds
    MIN_RR: float = 1.8
    PREFERRED_RR: float = 2.5
    MAX_RR: float = 4.0
    SL_BUFFER_ATR_FRACTION: float = 0.15
    MIN_SL_ATR_FRACTION: float = 0.75
    ATR_MIN_FRACTION_OF_PRICE: float = 0.00015
    REQUIRE_BOS: bool = True
    REQUIRE_CHOCH: bool = False
    VOLUME_AVG_LOOKBACK: int = 20
    VOLUME_MIN_RATIO: float = 0.8
    STRUCTURE_LOOKBACK_BARS: int = 80

    ATR_MULTIPLIERS_BY_STYLE: dict[str, float] = Field(
        default_factory=lambda: {
            "scalp": 1.2,
            "intraday": 1.5,
            "swing": 2.0,
        },
    )

    INSTRUMENT_RISK_PROFILES: dict[str, dict] = Field(
        default_factory=lambda: {
            "EURUSD": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "GBPUSD": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "AUDUSD": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "NZDUSD": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "USDCAD": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "USDCHF": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "EURGBP": {
                "digits": 5,
                "pip_size": 0.0001,
                "min_sl_pips": 8,
                "tick_size": 0.00001,
            },
            "USDJPY": {
                "digits": 3,
                "pip_size": 0.01,
                "min_sl_pips": 10,
                "tick_size": 0.001,
            },
            "EURJPY": {
                "digits": 3,
                "pip_size": 0.01,
                "min_sl_pips": 10,
                "tick_size": 0.001,
            },
            "GBPJPY": {
                "digits": 3,
                "pip_size": 0.01,
                "min_sl_pips": 12,
                "tick_size": 0.001,
            },
            "XAUUSD": {
                "digits": 2,
                "pip_size": 0.1,
                "point_size": 0.01,
                "min_sl_points": 150,
                "tick_size": 0.01,
            },
            "XAGUSD": {
                "digits": 3,
                "pip_size": 0.01,
                "min_sl_pips": 20,
                "tick_size": 0.001,
            },
            "BTCUSD": {
                "digits": 2,
                "pip_size": 1.0,
                "min_sl_atr_mult": 0.75,
                "tick_size": 0.01,
            },
            "ETHUSD": {
                "digits": 2,
                "pip_size": 0.1,
                "min_sl_atr_mult": 0.75,
                "tick_size": 0.01,
            },
            "SOLUSD": {
                "digits": 3,
                "pip_size": 0.01,
                "min_sl_atr_mult": 0.75,
                "tick_size": 0.001,
            },
        },
    )

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
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    """
    # #region agent log
    list_fields = (
        "MARKET_SYMBOLS",
        "MARKET_TIMEFRAMES",
        "NEWS_RSS_FEEDS",
        "BACKEND_CORS_ORIGINS",
    )
    env_file_path = Path.cwd() / ".env"
    dotenv_values: dict[str, str] = {}
    dotenv_read_error = None
    try:
        if env_file_path.is_file():
            for raw_line in env_file_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                dotenv_values[key.strip()] = value
    except Exception as exc:  # noqa: BLE001
        dotenv_read_error = repr(exc)

    for field_name in list_fields:
        os_val = os.environ.get(field_name)
        file_val = dotenv_values.get(field_name)
        effective = os_val if os_val is not None else file_val
        json_ok = None
        json_err = None
        if effective is not None:
            try:
                json.loads(effective)
                json_ok = True
            except Exception as exc:  # noqa: BLE001
                json_ok = False
                json_err = repr(exc)
        _agent_debug_log(
            "A" if field_name == "MARKET_SYMBOLS" else "E",
            "settings.py:get_settings",
            "list field raw env probe",
            {
                "field": field_name,
                "cwd": str(Path.cwd()),
                "env_file_exists": env_file_path.is_file(),
                "env_file_path": str(env_file_path.resolve()),
                "dotenv_read_error": dotenv_read_error,
                "in_os_environ": field_name in os.environ,
                "os_environ_repr": repr(os_val) if os_val is not None else None,
                "dotenv_repr": repr(file_val) if file_val is not None else None,
                "effective_repr": repr(effective) if effective is not None else None,
                "effective_len": len(effective) if effective is not None else None,
                "effective_is_empty": effective == "" if effective is not None else None,
                "looks_comma_separated": (
                    effective is not None
                    and "," in effective
                    and not effective.strip().startswith("[")
                ),
                "json_loads_ok": json_ok,
                "json_loads_error": json_err,
            },
        )
    # #endregion

    try:
        return Settings()
    except Exception as exc:  # noqa: BLE001
        # #region agent log
        _agent_debug_log(
            "A",
            "settings.py:get_settings:exception",
            "Settings() construction failed",
            {
                "exc_type": type(exc).__name__,
                "exc_repr": repr(exc),
                "exc_str": str(exc),
            },
        )
        # #endregion
        raise


settings = get_settings()
