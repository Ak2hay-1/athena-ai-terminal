# Athena AI Terminal

AI-powered trading intelligence platform for MetaTrader 5 and forex markets (primary focus: **XAUUSD**). Combines Smart Money Concepts, technical indicators, multi-timeframe analysis, news sentiment, and a provider-agnostic AI layer (Gemini primary, Local/Ollama fallback) to produce trade recommendations with risk controls.

> Status: under active development.

## Features

- **Market data** — Multi-symbol / multi-timeframe candles via MT5, REST + WebSocket streaming
- **Analysis** — Indicators, SMC patterns (FVG, order blocks, BOS/CHoCH), confluence scoring
- **AI recommendations** — Provider-agnostic narrative layer (Gemini / OpenAI / Claude / DeepSeek / Grok / Local) with Redis response caching; risk engine owns trade levels
- **News** — RSS sync, sentiment weighting, pre-event trade blocks
- **Trading** — Paper execution by default; MT5 execution provider available
- **Learning** — Adaptive signal model (scikit-learn) with periodic retrain
- **Auth** — JWT register / login / refresh; role-aware admin bootstrap
- **Frontend** — Next.js trading terminal (dashboard, markets, charts, AI, scanner, settings)

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, APScheduler |
| Market | MetaTrader 5 Python API |
| AI | Provider-agnostic (`AI_PROVIDER`); Gemini default, Local/Ollama fallback |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Zustand |
| Charts | TradingView Lightweight Charts, Recharts |
| Infra | Docker Compose (Postgres, Redis, Ollama, API, pgAdmin) |

## Repository layout

```text
athena-ai-terminal/
├── backend/          # FastAPI API, schedulers, MT5, AI, trading
├── frontend/         # Next.js App Router UI
├── docs/             # Architecture & onboarding docs
├── docker-compose.yml
└── SECURITY.md
```

## Quick start

### Option A — Docker (API + infra)

```bash
docker compose up
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| pgAdmin | http://localhost:5050 |
| Ollama | http://localhost:11434 |

> MT5 is Windows-native. Full live market features need a local Windows MT5 terminal; the API container can run without it for non-MT5 paths.

### Option B — Local backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then edit secrets / MT5 / AI_PROVIDER / API keys
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `AI_PROVIDER=gemini` (default) with `GEMINI_API_KEY`, or `AI_PROVIDER=local` for Ollama. On Gemini failure or missing key, Athena falls back to `AI_FALLBACK_PROVIDER` (default `local`).

Optional admin user:

```bash
python -m app.scripts.create_admin
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local    # Windows
npm run dev
```

Open http://localhost:3000.

Default env (align with backend port **8000**):

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000/ws
```

## API surface (overview)

All REST routes are under `/api/v1`:

| Group | Purpose |
|-------|---------|
| `/auth` | Register, login, refresh, profile |
| `/market` | Symbols, candles, sync, watchlist data |
| `/mt5` | Connection, account, positions, history |
| `/recommendations` | AI trading recommendations |
| `/ai` | Analysis endpoints |
| `/news` | Events, sync, sentiment |
| `/watchlist` | User watchlists |
| `/learning` | Model stats / retrain |
| `/trade` | Trade execution |
| `/portfolio` | Portfolio summary |
| `/risk` | Risk metrics / validation |

WebSocket: `WS /ws` — subscribe to `{SYMBOL}:{TIMEFRAME}` candle updates.

## Configuration

- Backend: copy `backend/.env.example` → `backend/.env`
- Frontend: copy `frontend/.env.example` → `frontend/.env.local`

Key backend knobs: `DATABASE_URL`, JWT secrets, `MT5_*`, `MARKET_SYMBOLS`, `OLLAMA_*`, `EXECUTION_PROVIDER` (`paper` default), news and learning settings. See [Environment Variables Reference](docs/New%20Documentation/35_Environment_Variables_Reference.md).

## Documentation

Start here:

- [Documentation Index](docs/New%20Documentation/00_Documentation_Index.md)
- [Project Overview](docs/New%20Documentation/01_Project_Overview.md)
- [Developer Onboarding](docs/New%20Documentation/23_Developer_Onboarding.md)
- [REST API](docs/New%20Documentation/13_REST_API.md)
- [WebSocket Architecture](docs/New%20Documentation/14_WebSocket_Architecture.md)
- [Deployment Guide](docs/New%20Documentation/19_Deployment_Guide.md)
- [Contributing](docs/Initial%20docs/CONTRIBUTING.md)
- [Security](SECURITY.md)

Frontend-specific notes: [frontend/README.md](frontend/README.md).

## Development notes

- **Python** 3.12 · **Node** 22 (CI)
- Backend tests: `cd backend && pytest`
- Frontend build: `cd frontend && npm run build`
- CORS defaults include `http://localhost:3000`
- Paper trading is the safe default; point `EXECUTION_PROVIDER` at MT5 only when intentionally live

## License

See [LICENSE](LICENSE).
