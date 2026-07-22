# Local AI Intelligence Layer (Ollama)

Athena’s LLM stack is a **communication layer only**. Deterministic engines finalize signal, confidence, entry, SL/TP, risk, and probability. Ollama (or any configured provider) explains and teaches after that.

## Architecture

```text
Frozen recommendation / market context
        ↓
PromptBuilder (sanitize — no OHLC)
        ↓
Prompt templates (explain / teach / chat / summary)
        ↓
AIProvider → LocalProvider (Ollama)
        ↓
ResponseCache (Redis)  |  WebSocket ai_chunk stream
        ↓
UI: explanation, chat, indicator help, session wrap
```

**Do not** invent BUY/SELL, levels, confidence, or probability in the LLM path.

## Configuration

Default ops config (see `backend/.env.example`):

```env
AI_PROVIDER=local
AI_FALLBACK_PROVIDER=local
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.3
OLLAMA_TOP_P=0.9
OLLAMA_MAX_TOKENS=1024
OLLAMA_TIMEOUT=300
AI_CACHE_TTL_SECONDS=3600
```

Model names are **Ollama tags** (e.g. `llama3`, `mistral`, `qwen`, `deepseek`, `phi`). There is no hardcoded allowlist — `GET /ai/models` lists whatever Ollama reports via `/api/tags`.

Cloud providers (Azure, Gemini, OpenAI, Claude, …) remain available through the same factory; switch `AI_PROVIDER` when needed.

### Ollama setup

1. Install [Ollama](https://ollama.com).
2. `ollama pull llama3.2` (or your preferred tag).
3. Ensure the daemon listens on `OLLAMA_HOST`.
4. Start Athena with `AI_PROVIDER=local`.

## REST API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/ai/explain-trade` | Sectioned explanation from recommendation id / snapshot / symbol+tf |
| POST | `/api/v1/ai/market-summary` | Structured market summary |
| POST | `/api/v1/ai/explain-indicator` | Educational indicator help |
| POST | `/api/v1/ai/teach` | Strategy teacher lesson |
| POST | `/api/v1/ai/chat` | Multi-turn chat (safety redirect for decision asks) |
| POST | `/api/v1/ai/session-summary` | Live / replay session wrap |
| GET | `/api/v1/ai/health` | Provider health + model list |
| GET | `/api/v1/ai/models` | Available model tags |

## WebSocket streaming

On existing `/ws` (authenticated):

**Client → server**

```json
{
  "action": "AI_CHAT",
  "request_id": "chat-1",
  "messages": [{"role": "user", "content": "Explain the trend"}],
  "symbol": "XAUUSD",
  "timeframe": "M5"
}
```

```json
{
  "action": "AI_EXPLAIN",
  "request_id": "explain-1",
  "symbol": "XAUUSD",
  "timeframe": "M5"
}
```

**Server → client**

- `{ "type": "ai_chunk", "request_id", "delta" }`
- `{ "type": "ai_done", "request_id", "full" }`
- `{ "type": "ai_error", "request_id", "message" }`

HTTP `/ai/chat` remains the non-stream fallback (sidebar / offline WS).

## Cache keys

Redis keys: `ai:{task}:{sha256(canonical_json(state))}` via `ResponseCache`.

Cached tasks: `trade_explanation`, `market_summary`, `indicator_explainer`, `strategy_teacher`, `session_summary`, `news_summary`.

**Not cached:** chat (stream and non-stream). Streaming explain skips cache.

## Safety

`app/ai/safety.py`:

- Detects decision intents (“Should I BUY?”, entry/SL/TP asks, price prediction).
- Returns a canned redirect to Athena’s frozen recommendation (no LLM call).
- Light post-filter on advice-like phrases.

Chat system prompt hard-codes: Athena already decided; explain only.

## Frontend

- `/ai` — full chat + market summary (WS stream preferred)
- `/chat` — redirects to `/ai`
- Recommendation detail — `AiExplanationCard`
- Markets — `IndicatorHelp`
- Replay end — `SessionSummary`
- Hook: `useAiStream` (`AI_CHAT` / `AI_EXPLAIN`)

## Code map

| Concern | Location |
|---------|----------|
| Provider interface + stream | `backend/app/ai/providers/base.py` |
| Ollama | `backend/app/ai/providers/local_provider.py` |
| PromptBuilder | `backend/app/ai/prompts/prompt_builder.py` |
| Templates | `backend/app/ai/prompts/*.py` |
| Safety | `backend/app/ai/safety.py` |
| Orchestration | `backend/app/ai/services/ai_service.py` |
| Thin wrappers | `backend/app/ai/services/*_explainer.py`, `chat_service.py`, … |
| REST | `backend/app/api/v1/ai.py` |
| WS | `backend/app/api/websocket.py` |

## Out of scope

- AI-generated trades / levels / confidence / probability
- Parallel `app/services/ai/` package
- Redesigning recommendation / risk / replay engines
