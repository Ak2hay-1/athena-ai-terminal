# Athena AI Terminal — Features

AI-powered trading intelligence for MetaTrader 5 and forex markets (primary focus: **XAUUSD**). Combines Smart Money Concepts, technical indicators, multi-timeframe analysis, news sentiment, institutional risk controls, and a provider-agnostic AI narrative layer.

> Status: under active development. MT5 limit-order execution is the default.

**Stack:** Next.js 15 frontend · FastAPI backend · PostgreSQL · Redis · MT5 · APScheduler

**Supported symbols:** XAUUSD, XAGUSD, major FX pairs  

**Supported timeframes:** M1, M5, M15, M30, H1, H4, D1

---

## Authentication & accounts

- Register with username, email, password, and full name
- Login with JWT access + refresh tokens
- Token refresh and persistent session (Zustand auth store)
- Roles: **VIEWER**, **TRADER**, **ADMIN** with role-based API guards
- Self-service profile update and password change
- Account activate / deactivate (admin)
- Self-service account deletion (API)

---

## Dashboard

- Live API health, market session status, and WebSocket connection state
- Hero AI recommendation for the selected symbol and timeframe
- On-demand analysis trigger
- Price chart with live candle updates
- Multi-symbol watchlist with quotes
- High-impact news and economic calendar
- Open positions (MT5)
- Scanner preview and recent recommendations
- Activity timeline
- Global symbol / timeframe workspace state

---

## Markets & charts

- Browse symbols by category (metals, forex)
- Live bid / ask / mid quotes with price-flash animation
- Symbol detail pages with candlestick charts (TradingView Lightweight Charts)
- Timeframe selector synced to workspace state
- Live quote polling with WebSocket candle merge
- REST fallback when WebSocket is unavailable

---

## Athena AI

- Chat-style assistant UI with suggested prompts
- Context from live recommendations and news
- Can trigger a fresh analysis pipeline run
- Backend AI capabilities:
  - Trade explanation (narrative reasons on recommendations)
  - Market summary
  - News summary
  - Multi-turn advisory chat
  - Text embeddings
- Provider-agnostic LLM layer:
  - Google Gemini (default primary)
  - OpenAI-compatible (OpenAI, DeepSeek, Grok)
  - Anthropic Claude
  - Local Ollama (default fallback)
- Primary / fallback provider selection via config
- Provider health checks, retries, and automatic fallback
- Redis response caching with TTL and soft-fail if Redis is down
- Context filtering, structured response parsing, cost/metrics logging

> The `/ai` page and side assistant panel call backend `/ai/chat` with live market context.

---

## Scanner

- Rank opportunities across configured symbols
- Filter by signal, asset category, and minimum confidence
- Live stream indicator
- Links through to market detail pages

---

## Recommendations & history

- Full analysis pipeline: candles → indicators + SMC → confluence → risk plan → AI explanation → persist
- Signals: `BUY`, `SELL`, `HOLD`, `NO_TRADE`
- Latest and historical recommendation APIs
- Filterable history UI (signal, confidence, symbol, timeframe)
- Recommendation detail view (signal, levels, reasons, validation, trend/risk)

---

## Journal

- Persisted journal entries (`journal_entries`) with CRUD at `/journal`
- Entry types: note, trade review, recommendation review, auto-close
- Optional links to recommendations and historical positions; tags JSON
- “Add to journal review” from recommendation detail creates a review entry
- Journal page: timeline from API, create/edit/delete, suggest-pin from open positions and recent recommendations
- Closed trade history available at `GET /trade/history`

---

## Analytics

- Signal distribution
- Average confidence and risk/reward
- High-confidence recommendation counts
- Learning pattern win rates
- Adaptive confluence weights visibility
- Model accuracy / sample size from learning stats

---

## Strategies

- Strategy playbook cards (SMC, news-aware, multi-timeframe confluence, adaptive weights)
- Live signal and weight snapshot overlay

---

## Alerts

- Derived alert feed from:
  - High-impact news windows
  - Economic calendar events
  - Signal changes
  - Session notes
- Shared `useDerivedAlerts` hook powers `/alerts` and the shell notifications drawer

> User-defined alert rules and push subscriptions are not yet implemented.

---

## App shell search & notifications

- Global search palette (Topbar + Ctrl/Cmd+K): pages, markets, recommendations, journal
- Notifications drawer (bell): **Alerts** tab (derived) + **Inbox** tab (`GET /notifications/recent` with open/dismiss)
- Bell badge = high-severity derived alerts + unread inbox deliveries

---

## Settings

- Update profile (name, email)
- Change password
- Local workspace preferences (default symbol/timeframe, risk %, AI panel toggle)
- Sign out

---

## Admin & operations

### Overview
- System health dashboard
- MT5 connection status
- User counts
- AI provider / model and execution provider visibility
- Configured symbols and timeframes
- Trigger learning retrain and outcome labeling
- MT5 initialize / shutdown controls

### Users
- List users
- Change role (ADMIN / TRADER / VIEWER)
- Activate / deactivate accounts
- Toggle verified flag

### Ops
- Scheduler job status and next run times
- Manual market candle collection by timeframe
- Trigger individual scheduler jobs
- Sync news feeds on demand
- Delete candles before a timestamp (data retention)

### Bootstrap
- Optional admin user creation via `python -m app.scripts.create_admin`

---

## Market data pipeline

- MT5 candle collection scheduled per symbol / timeframe
- Auto-analysis when new candles are inserted
- REST APIs for latest candles, history ranges, quotes, and statistics
- Bulk and single candle insert
- Admin candle cleanup
- Graceful MT5 skip when terminal is unavailable (e.g. non-Windows Docker)

### MetaTrader 5 (admin API)
- Initialize / login / shutdown
- Connection status, account info, terminal info, version

---

## Technical analysis & Smart Money Concepts

### Indicators
- EMA (9 / 20 / 50 / 200)
- RSI, MACD, ATR
- Bollinger Bands, VWAP, moving averages

### SMC / structure patterns
- Swing detection and trend structure
- Break of structure (BOS)
- Change of character (CHOCH)
- Fair value gaps (FVG)
- Order blocks
- Liquidity sweeps
- Premium / discount zones

### Scoring & confluence
- Weighted confluence from EMA stack, RSI, MACD, BOS, CHOCH, FVG, order blocks, liquidity, and news
- Multi-timeframe analyzer for higher-timeframe bias
- News sentiment integration
- Adaptive weight multipliers from the learning system

---

## Institutional risk engine

Deterministic pipeline (risk engine owns signal, confidence, entry, SL, and TP; AI adds narrative only):

```text
trend → structure → liquidity → ATR → invalidation → SL → TP → entry → validate
```

- Structure context builder (SMC + HTF + news)
- Structure-based stop loss with ATR buffers and minimum pips
- Structure / POI entry service (limit preferred)
- Take-profit service with RR targets and liquidity objectives
- Confidence engine (0–100 weighted score)
- Trade validator gates: trend alignment, BOS/CHOCH, volume, ATR, news blocks, minimum RR
- Per-symbol pip / distance profiles
- Configurable limits: max open trades, max risk %, RR bounds, ATR multipliers, BOS/CHOCH requirements, news block windows

### Risk API
- View configured risk limits
- Assess open-trade count gate

---

## News & calendar

- RSS feed ingestion (scheduled + manual admin sync)
- Per-event sentiment scoring
- Currency → affected-symbol mapping
- Economic calendar events
- High-impact trade blocks during configured news windows
- Analysis-ready news context (headlines, sentiment, upcoming high-impact flag)
- AI news summarization

---

## Trading & portfolio

- MT5 execution by default (`EXECUTION_PROVIDER=mt5`) — BUY_LIMIT / SELL_LIMIT at entry + SL/TP
- Place order / close trade APIs
- Open positions listing (broker tickets)
- Portfolio summary (open position count + positions)
- Dashboard hero places an MT5 limit order from the latest recommendation
- Auto Trade header toggle uses the same MT5 execution path

---

## Watchlist (backend)

- List, add/update, and delete user watchlist entries (symbol + timeframe)

> Markets page can add/remove watchlist symbols; dashboard watchlist prefers the user's enabled entries and falls back to the static market list when empty.

---

## Learning & adaptive intelligence

- Outcome labeling for recommendation results
- Pattern win-rate statistics
- Adaptive confluence weight engine per symbol / timeframe
- scikit-learn logistic regression signal model (confluence, RSI, MACD, news, MTF features)
- Scheduled retrain jobs
- Admin-triggered retrain and labeling
- Learning stats API for analytics UI

---

## Real-time WebSocket

- Endpoint: `WS /ws?token=<access_jwt>` (JWT required)
- Subscribe / unsubscribe to `SYMBOL:TIMEFRAME` channels
- Ping / pong keepalive
- Server push: OHLCV candle updates, insert count, optional recommendation snapshot
- Frontend reconnect with backoff and multi-symbol subscribe
- Used on dashboard and market detail pages

---

## Schedulers

- **Market scheduler** — periodic MT5 collection; triggers analysis and WebSocket broadcast
- **News / learning scheduler** — RSS sync, outcome labeling, model retrain

---

## Infrastructure & observability

- Docker Compose: PostgreSQL, Redis, Ollama, FastAPI backend, Next.js frontend, pgAdmin (API runs Alembic on start)
- Structured logging (`athena.log`)
- Request ID middleware
- HTTP logging middleware
- AI call metrics and cost estimation logging
- OpenAPI docs at `/docs`
- Health check at `/api/v1/health`
- Backend pytest coverage for risk, AI, providers, recommendation engine, validators, and related units

---

## App shell (cross-cutting UI)

- Authenticated platform layout with sidebar and mobile nav
- Admin-gated admin navigation
- Topbar with route title, global search, notifications drawer, and user menu
- Global symbol / timeframe store
- AI assistant panel send path calls `/ai/chat`

---

## API surface (overview)

All REST routes under `/api/v1`:

| Group | Purpose |
|-------|---------|
| `/auth` | Register, login, refresh, profile, users (admin) |
| `/admin` | Ops overview, schedulers, news sync, market cleanup |
| `/market` | Candles, history, quotes, statistics |
| `/mt5` | MT5 lifecycle and account info |
| `/recommendations` | Latest and historical recommendations |
| `/ai` | Analyze, chat, market/news summary, embeddings |
| `/news` | Events, calendar, context, sync |
| `/watchlist` | User watchlist CRUD |
| `/learning` | Stats, weights, retrain, label |
| `/trade` | Order, close, positions, history |
| `/journal` | Journal CRUD |
| `/portfolio` | Portfolio summary |
| `/risk` | Limits and assess |
| `/notifications` | Recent deliveries and interact |

WebSocket: `WS /ws` — subscribe to `{SYMBOL}:{TIMEFRAME}` candle updates.

---

## Documentation

- [README](README.md)
- [Documentation Index](docs/New%20Documentation/00_Documentation_Index.md)
- [Project Overview](docs/New%20Documentation/01_Project_Overview.md)
- [REST API](docs/New%20Documentation/13_REST_API.md)
- [WebSocket Architecture](docs/New%20Documentation/14_WebSocket_Architecture.md)
- [Environment Variables](docs/New%20Documentation/35_Environment_Variables_Reference.md)
- [Security](SECURITY.md)
