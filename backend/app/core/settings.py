"""
Application Settings.

Central configuration for Athena AI Terminal.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated
from typing import Any

from pydantic import BeforeValidator
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import NoDecode
from pydantic_settings import SettingsConfigDict



def _parse_comma_separated_str_list(value: Any) -> list[str]:
    """Parse env values that are comma-separated or JSON list strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = json.loads(text)
            if not isinstance(parsed, list):
                raise TypeError("expected a JSON list")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in text.split(",") if item.strip()]
    raise TypeError(f"expected str or list, got {type(value).__name__}")


CommaSeparatedStrList = Annotated[
    list[str],
    NoDecode,
    BeforeValidator(_parse_comma_separated_str_list),
]


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

    # Hard cap (seconds) on mt5.initialize() during app startup so a missing
    # or unreachable MT5 terminal never blocks the API from coming up.
    MT5_INIT_TIMEOUT: int = 15

    # High-frequency MT5 tick → WebSocket stream (forming candle / last price).
    TICK_STREAM_ENABLED: bool = True
    TICK_POLL_MS: int = 200

    DEFAULT_SYMBOL: str = "XAUUSD"

    DEFAULT_TIMEFRAME: str = "M5"

    MARKET_SYMBOLS: CommaSeparatedStrList = Field(
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
        ],
    )

    MARKET_TIMEFRAMES: CommaSeparatedStrList = Field(
        default_factory=lambda: [
            "M1",
            "M5",
            "M15",
            "M30",
            "H1",
            "H4",
            "D1",
        ],
    )

    # Bars pulled per single MT5 call during deep/backfill pulls (clamped by
    # broker maxbars). NOT used for routine polling — see
    # MARKET_COLLECTOR_POLL_BARS for that.
    MARKET_COLLECTOR_BARS: int = 50000

    # Bars requested on each routine scheduled collect (every symbol x
    # timeframe, as often as every 60s). Keep this small — it only needs to
    # cover the newest bar(s) since the last poll; requesting tens of
    # thousands of bars here overloads MT5/DB and starves the scheduler.
    MARKET_COLLECTOR_POLL_BARS: int = 10

    # Max bars for explicit POST /market/backfill requests.
    MARKET_BACKFILL_BARS: int = 100000

    # One-shot startup backfill when DB depth is below this threshold.
    MARKET_STARTUP_BACKFILL_ENABLED: bool = True
    MARKET_STARTUP_BACKFILL_THRESHOLD: int = 5000

    # ==========================================================
    # Market Data Engine (tick -> candle pipeline)
    # ==========================================================

    # Master switch for the tick-based candle engine. When enabled, the
    # legacy interval candle collectors and tick streamer are replaced.
    MARKET_ENGINE_ENABLED: bool = True

    # Target depth of the one-time initial history download (years of
    # M1 data; higher timeframes scale accordingly). Actual depth is
    # limited by what the broker provides.
    MARKET_INITIAL_SYNC_YEARS: int = 5

    # Persist raw ticks to market_ticks (for backtesting / future ML).
    MARKET_STORE_TICKS: bool = False

    # Seconds between batched database flushes of completed candles.
    MARKET_WRITE_FLUSH_SECONDS: float = 1.0

    # Run local analysis (recommendation engine) after each candle close.
    MARKET_ANALYZE_ON_CLOSE: bool = True

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
    # Multi-layer Market Cache (RAM → DB → MT5)
    # ==========================================================

    # Master switch for CacheManager (chart history / indicators / AI ctx).
    # Live account state is never cached regardless of this flag.
    CACHE_ENABLED: bool = True

    # Layer 1: max completed candles retained per symbol/timeframe in RAM.
    CACHE_MAX_RAM_CANDLES: int = 5000

    # Soft RAM budget (MB) across all series; LRU eviction when exceeded.
    CACHE_MAX_RAM_MB: float = 256.0

    # Max distinct symbol/timeframe series kept in RAM.
    CACHE_MAX_SERIES: int = 128

    # Drop inactive series after this many seconds without access.
    CACHE_INACTIVE_TTL_SECONDS: float = 900.0

    # Background preload of related timeframes / watchlist / recent.
    CACHE_PRELOAD_ENABLED: bool = True

    CACHE_PRELOAD_WORKERS: int = 2

    CACHE_PRELOAD_LIMIT: int = 500

    # Related timeframes warmed when a chart opens (e.g. M5 → these).
    CACHE_PRELOAD_TIMEFRAMES: CommaSeparatedStrList = Field(
        default_factory=lambda: ["M1", "M15", "H1", "H4"],
    )

    # Indicator result cache (skip full recompute when series unchanged).
    CACHE_INDICATOR_ENABLED: bool = True

    # Short-lived AI market context TTL (seconds). Keep 30–60s.
    CACHE_AI_TTL_SECONDS: float = 45.0

    # ==========================================================
    # AI Provider (provider-agnostic)
    # ==========================================================

    AI_PROVIDER: str = "local"

    AI_FALLBACK_PROVIDER: str = "local"

    AI_TIMEOUT: int = 60

    AI_MAX_RETRIES: int = 3

    AI_CACHE_TTL_SECONDS: int = 3600

    REDIS_URL: str = "redis://localhost:6379/0"

    GEMINI_API_KEY: str = ""

    GEMINI_MODEL: str = "gemini-2.5-flash"

    GEMINI_EMBED_MODEL: str = "text-embedding-004"

    OPENAI_API_KEY: str = ""

    OPENAI_MODEL: str = "gpt-4o-mini"

    AI_BASE_URL: str = ""

    AZURE_OPENAI_ENDPOINT: str = ""

    AZURE_OPENAI_API_KEY: str = ""

    AZURE_OPENAI_DEPLOYMENT: str = "gpt-5-mini"

    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    AZURE_OPENAI_EMBED_DEPLOYMENT: str = ""

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

    OLLAMA_TEMPERATURE: float = 0.3

    OLLAMA_TOP_P: float = 0.9

    OLLAMA_MAX_TOKENS: int = 1024

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

    NEWS_RSS_FEEDS: CommaSeparatedStrList = Field(
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

    LEARNING_LABEL_INTERVAL_SECONDS: int = 900

    LEARNING_ANALYTICS_INTERVAL_SECONDS: int = 3600

    LEARNING_ANALYTICS_MIN_SAMPLES: int = 10

    LEARNING_WEIGHT_UPDATE_INTERVAL_HOURS: int = 24

    LEARNING_WEIGHT_MIN_SAMPLES: int = 50

    LEARNING_WEIGHT_STEP: float = 2.0

    LEARNING_WEIGHT_MAX_STEP: float = 1.5

    LEARNING_WEIGHT_MIN: float = 5.0

    LEARNING_WEIGHT_MAX: float = 35.0

    ENGINE_VERSION: str = "1.0.0"

    INDICATOR_VERSION: str = "1.0.0"

    STRATEGY_VERSION: str = "1.0.0"

    LEARNING_SYSTEM_VERSION: str = "1.0.0"

    # ==========================================================
    # Trade Probability (deterministic)
    # ==========================================================

    PROBABILITY_LOW_SAMPLE: int = 20

    PROBABILITY_BLEND_MIN: int = 30

    PROBABILITY_CANDIDATE_LIMIT: int = 500

    PROBABILITY_SIMILAR_TOP_N: int = 20

    SIMILARITY_WEIGHT_TREND: float = 0.25

    SIMILARITY_WEIGHT_STRUCTURE: float = 0.20

    SIMILARITY_WEIGHT_LIQUIDITY: float = 0.15

    SIMILARITY_WEIGHT_MOMENTUM: float = 0.15

    SIMILARITY_WEIGHT_NEWS: float = 0.10

    SIMILARITY_WEIGHT_ATR: float = 0.10

    SIMILARITY_WEIGHT_RISK: float = 0.05

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

    EXECUTION_PROVIDER: str = "mt5"

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

    # ==========================================================
    # Institutional Qualification Desk (quality over quantity)
    # ==========================================================

    QUALIFICATION_ENABLED: bool = True

    MIN_SETUP_QUALITY: int = 75
    MIN_CONFIDENCE: int = 70
    MAX_ACTIONABLE_TRADES: int = 3
    MAX_WATCHLIST: int = 8

    QUAL_MIN_ADX: float = 22.0
    QUAL_MIN_STRUCTURE_SCORE: float = 40.0
    QUAL_MAX_SPREAD_FRACTION: float = 0.00035
    QUAL_ENFORCE_SESSION: bool = False
    QUAL_ALLOWED_SESSIONS: CommaSeparatedStrList = Field(
        default_factory=lambda: [
            "London",
            "New York",
            "Overlap",
            "Asian",
            "Sydney",
        ],
    )

    QUAL_MTF_REQUIRE_STRICT: bool = True
    QUAL_MTF_REQUIRED_ALIGNMENT: CommaSeparatedStrList = Field(
        default_factory=lambda: ["H4", "H1"],
    )

    QUAL_COMPRESSION_ATR_RATIO: float = 0.65
    QUAL_EXPANSION_ATR_RATIO: float = 1.35
    QUAL_HIGH_VOL_ATR_RATIO: float = 1.6
    QUAL_COMPRESSION_RANGE_FRACTION: float = 0.004
    QUAL_RANGING_MIN_ADX: float = 25.0
    QUAL_LOW_VOL_MIN_QUALITY: float = 85.0
    QUAL_HIGH_VOL_MIN_QUALITY: float = 70.0
    QUAL_FLOOR_MIN_QUALITY: float = 65.0

    QUAL_SESSION_THRESHOLDS: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "Asian": {"min_quality": 85.0, "min_adx": 25.0},
            "Sydney": {"min_quality": 85.0, "min_adx": 25.0},
            "London": {"min_quality": 75.0, "min_adx": 22.0},
            "New York": {"min_quality": 75.0, "min_adx": 22.0},
            "Overlap": {"min_quality": 70.0, "min_adx": 20.0},
        },
    )

    QUAL_REGIME_THRESHOLDS: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "LOW_VOLATILITY": {"min_quality": 85.0},
            "HIGH_VOLATILITY": {"min_quality": 70.0, "min_adx": 18.0},
            "RANGING": {"min_adx": 28.0},
            "COMPRESSION": {"min_quality": 95.0},
            "TRENDING": {"min_quality": 75.0},
            "BREAKOUT": {"min_quality": 72.0, "min_adx": 20.0},
            "EXPANSION": {"min_quality": 70.0},
        },
    )

    ALLOW_CORRELATED_TRADES: bool = False
    MAX_CORRELATED_EXPOSURE: int = 1
    MAX_SIMULTANEOUS_BUYS: int = 3
    MAX_SIMULTANEOUS_SELLS: int = 3
    MAX_PORTFOLIO_RISK_PERCENT: float = 6.0

    CORRELATION_GROUPS: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "USD_LONG": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],
            "USD_SHORT": ["USDJPY", "USDCHF", "USDCAD"],
            "JPY_CROSSES": ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "NZDJPY"],
            "EUR_CROSSES": ["EURGBP", "EURJPY", "EURCHF", "EURAUD"],
            "GOLD": ["XAUUSD", "XAGUSD"],
        },
    )

    SETUP_LIFECYCLE_ENABLED: bool = True
    SETUP_MAX_AGE_MINUTES: int = 240
    SETUP_LEVEL_CHANGE_ATR_FRACTION: float = 0.35

    PORTFOLIO_AWARENESS_ENABLED: bool = True

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
    # Agents (orchestrator)
    # ==========================================================

    AGENTS_ENABLED: bool = False

    AGENTS_EVENT_HISTORY_SIZE: int = 500

    AGENTS_DISABLED: CommaSeparatedStrList = Field(
        default_factory=list,
    )

    # Market Watch Agent (timeframes: M1/M5/M15/H1/H4/D1)
    MARKET_WATCH_SYMBOLS: CommaSeparatedStrList = Field(
        default_factory=lambda: [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "XAUUSD",
        ],
    )

    MARKET_WATCH_TIMEFRAMES: CommaSeparatedStrList = Field(
        default_factory=lambda: [
            "M1",
            "M5",
            "M15",
            "H1",
            "H4",
            "D1",
        ],
    )

    MARKET_WATCH_SCAN_INTERVAL_SECONDS: int = 60

    MARKET_WATCH_CANDLE_LIMIT: int = 200

    MARKET_WATCH_VOLUME_SPIKE_RATIO: float = 2.0

    MARKET_WATCH_ATR_EXPANSION_RATIO: float = 1.5

    MARKET_WATCH_GAP_ATR_FRACTION: float = 0.5

    # Scanner (ranked opportunity board)
    SCANNER_SYMBOLS: CommaSeparatedStrList = Field(
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
        ],
    )

    SCANNER_SECONDARY_TIMEFRAMES: CommaSeparatedStrList = Field(
        default_factory=lambda: ["M15", "H1", "H4"],
    )

    SCANNER_STALE_MINUTES: int = 45

    SCANNER_STRONG_SIGNAL_CONFIDENCE: int = 75

    SCANNER_MARKET_WATCH_MAX_AGE_SECONDS: int = 300

    SCANNER_MIN_SCORE_DEFAULT: int = 0

    # Technical Agent scoring (weights normalized at runtime)
    TECHNICAL_SCORE_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: {
            "trend": 30.0,
            "momentum": 25.0,
            "volatility": 15.0,
            "volume": 15.0,
            "structure": 15.0,
        },
    )

    TECHNICAL_INDICATOR_CACHE_SIZE: int = 256

    # SMC Agent
    SMC_SCORE_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: {
            "structure": 30.0,
            "liquidity": 20.0,
            "order_blocks": 20.0,
            "fvg": 15.0,
            "premium_discount": 15.0,
        },
    )

    SMC_INDICATOR_CACHE_SIZE: int = 256

    # Risk Agent (evidence only)
    RISK_SCORE_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: {
            "geometry": 30.0,
            "volatility": 20.0,
            "session": 15.0,
            "news": 20.0,
            "liquidity": 15.0,
        },
    )

    RISK_ACCOUNT_BALANCE: float = 10000.0

    RISK_MAX_SPREAD_POINTS: float = 30.0

    RISK_EXTREME_ATR_RATIO: float = 2.0

    RISK_CACHE_SIZE: int = 256

    # Validation Agent thresholds
    VALIDATION_MIN_TECHNICAL_SCORE: float = 60.0

    VALIDATION_MIN_SMC_SCORE: float = 60.0

    VALIDATION_MIN_RISK_SCORE: float = 60.0

    VALIDATION_MIN_RR: float = 1.8

    VALIDATION_MIN_CONFLUENCE: float = 70.0

    VALIDATION_CONFLUENCE_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: {
            "technical": 34.0,
            "smc": 33.0,
            "risk": 33.0,
        },
    )

    VALIDATION_CACHE_SIZE: int = 256

    # Phase 4 agents
    MEMORY_AGENT_ENABLED: bool = True

    LEARNING_AGENT_ENABLED: bool = True

    NEWS_AGENT_ENABLED: bool = True

    REASONING_ENABLED: bool = True

    REASONING_MIN_CONFLUENCE: float = 70.0

    REASONING_MIN_STATUS: str = "APPROVED"

    REASONING_CACHE_TTL_SECONDS: int = 3600

    REASONING_MAX_RETRIES: int = 2

    REASONING_SIMILAR_TRADES_TOP_K: int = 20

    MEMORY_SIMILARITY_TOP_K: int = 20

    MEMORY_EMBEDDINGS_ENABLED: bool = False

    LEARNING_SCAN_INTERVAL_SECONDS: int = 300

    NEWS_AGENT_SCAN_INTERVAL_SECONDS: int = 900

    # Phase 5 — Portfolio / Watchlist / Communication / Notifications
    PORTFOLIO_AGENT_ENABLED: bool = True

    WATCHLIST_AGENT_ENABLED: bool = True

    COMMUNICATION_AGENT_ENABLED: bool = True

    PERSONALIZATION_ENABLED: bool = True

    PORTFOLIO_SCAN_INTERVAL_SECONDS: int = 60

    PORTFOLIO_ACCOUNT_BALANCE: float = 10000.0

    WATCHLIST_MIN_CONFLUENCE: float = 75.0

    WATCHLIST_DEDUP_TTL_SECONDS: int = 300

    COMM_DEDUP_TTL_SECONDS: int = 300

    COMM_GROUP_WINDOW_SECONDS: int = 60

    COMM_DEFAULT_QUIET_START: str = "22:00"

    COMM_DEFAULT_QUIET_END: str = "07:00"

    NOTIFY_TELEGRAM_ENABLED: bool = False

    NOTIFY_TELEGRAM_BOT_TOKEN: str = ""

    NOTIFY_DISCORD_ENABLED: bool = False

    NOTIFY_DISCORD_WEBHOOK_URL: str = ""

    NOTIFY_EMAIL_ENABLED: bool = False

    NOTIFY_SMTP_HOST: str = ""

    NOTIFY_SMTP_PORT: int = 587

    NOTIFY_SMTP_USER: str = ""

    NOTIFY_SMTP_PASSWORD: str = ""

    NOTIFY_SMTP_FROM: str = ""

    NOTIFY_PUSH_ENABLED: bool = False

    NOTIFY_WEBSOCKET_ENABLED: bool = True

    # ==========================================================
    # CORS
    # ==========================================================

    BACKEND_CORS_ORIGINS: CommaSeparatedStrList = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    """

    try:
        loaded = Settings()
    except Exception as exc:  # noqa: BLE001
        raise

    return loaded


settings = get_settings()
