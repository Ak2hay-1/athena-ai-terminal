# Athena — Local Ready Checklist

Use this to verify a working end-to-end MT5 trading loop on Windows.

## 1. Infrastructure

- [ ] PostgreSQL 16 running (Compose: `docker compose up postgres redis -d`, or local install)
- [ ] Redis running (`redis://localhost:6379/0`)
- [ ] (Optional) Ollama running if using local AI (`http://127.0.0.1:11434`)

## 2. Backend env

```bash
cd backend
copy .env.example .env
```

Edit `backend/.env`:

| Variable | Action |
|----------|--------|
| `SECRET_KEY` | Replace `change-me-...` with a long random string |
| `DATABASE_URL` | Local: `postgresql+psycopg://postgres:postgres@localhost:5432/athena`. Docker API container: host must be `postgres`, not `localhost` |
| `AI_PROVIDER` | `gemini` (default) or `local` |
| `GEMINI_API_KEY` | Required if `AI_PROVIDER=gemini` |
| `OLLAMA_*` | Required if using local / fallback; pull model: `ollama pull llama3.2` |
| `REDIS_URL` | Default `redis://localhost:6379/0` |
| `EXECUTION_PROVIDER` | `mt5` (required for live limit orders) |
| `MT5_*` | **Required for charts/ticks on Windows:** login, password, server; optional `MT5_PATH` to `terminal64.exe`. Run the API on the same Windows host as MT5 (not Linux Docker). |
| `TICK_STREAM_ENABLED` / `TICK_POLL_MS` | Realtime ticks over WebSocket (default on / 200ms). |
| `BACKEND_CORS_ORIGINS` | Includes `http://localhost:3000` by default |

## 3. Database

```bash
cd backend
alembic upgrade head
```

> In `APP_ENV=development` + `DEBUG=true`, tables may also be created on startup, but Alembic is preferred.

## 4. Start API

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

- [ ] http://127.0.0.1:8000/api/v1/health returns healthy
- [ ] http://127.0.0.1:8000/docs opens OpenAPI

## 5. Admin / user

```bash
python -m app.scripts.create_admin
```

Or register via the UI at `/register`.

## 6. Frontend

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Confirm `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000/ws
```

- [ ] http://localhost:3000 loads
- [ ] Login / register works

## 7. Live market data (Windows)

- [ ] MetaTrader 5 terminal installed and logged in
- [ ] `MT5_*` credentials match the terminal
- [ ] Dashboard shows candles / quotes for `DEFAULT_SYMBOL` (usually XAUUSD)
- [ ] Trigger analysis from the dashboard or AI page

Without MT5, the API still runs; charts and recommendations stay empty until candles exist.

## 8. MT5 trade smoke test

- [ ] Latest recommendation appears (or run Analyze) with entry / SL / TP
- [ ] Place order from the recommendation hero (“Execute trade”)
- [ ] Response shows `status: "PENDING"` with an MT5 ticket
- [ ] Pending limit appears in MetaTrader 5 (not an Athena DB paper row)
- [ ] Open positions list shows the pending / live trade
- [ ] Close or cancel from Athena / MT5 as needed

## 9. AI path

- [ ] Analyze produces a recommendation with narrative reasons
- [ ] AI chat page talks to backend `/ai/chat` (not only templated client replies)
- [ ] If Gemini key is missing, fallback to Ollama works when models are pulled

WebSocket streams require a valid access token (`ws://…/ws?token=…`); sign in before expecting live WS badges.

## 10. Docker notes

```bash
docker compose up
```

- API: http://localhost:8000 — set `DATABASE_URL` host to `postgres`
- Compose does not start the frontend; run Next.js on the host
- Linux containers cannot use Windows MT5; run the API on the Windows host with MT5 installed
- Pull Ollama models separately: `docker exec -it athena-ollama ollama pull llama3.2`

## Quick verify script

From repo root (with API up):

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

Optional deeper check (requires a logged-in token): health + MT5 status via Admin → Overview in the UI.
