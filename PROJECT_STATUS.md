# Athena Project Status

Version: 0.3.0-dev

Backend: ~95%

Frontend: ~75%

Overall Progress: ~85%

## Ready for local use

See [READY.md](READY.md) for the end-to-end checklist.

Working loop: auth → dashboard → analyze → AI chat → paper trade (DB-backed) → watchlist.

## Recently completed (readiness)

- Persisted paper positions (`paper_positions` table)
- Next.js AI chat + assistant panel wired to `/ai/chat`
- Watchlist UI CRUD on Markets; dashboard uses personal watchlist
- WebSocket JWT auth (`?token=`)
- MT5 close implementation; MetaTrader5 optional on non-Windows
- Docker Compose: frontend service + Alembic on API start
- Debug instrumentation removed from hot paths
- Dedicated journal persistence (`journal_entries` + `/journal` CRUD, auto-draft on paper close)
- Global search palette and dual-tab notifications drawer (Alerts + Inbox)

## Remaining polish

- User-defined alert rules and push subscriptions
- Broader automated test coverage for trading + WS auth
- Live MT5 execution still requires careful broker validation before real funds
