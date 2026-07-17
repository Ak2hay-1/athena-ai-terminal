# Athena Frontend

Enterprise AI Trading Intelligence Platform — Next.js App Router.

## Stack

- Next.js (App Router)
- React + TypeScript
- Tailwind CSS + shadcn/ui patterns
- TanStack Query + Zustand
- Framer Motion
- TradingView Lightweight Charts
- Recharts

## Getting started

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Architecture

```
src/
  app/           # App Router pages & layouts
  components/    # Shared UI + layout shell
  features/      # Domain feature modules
  hooks/         # Shared hooks
  lib/           # Utilities
  services/      # API / WebSocket clients
  store/         # Zustand UI state
  types/         # Shared TypeScript types
  constants/     # Navigation, theme tokens
```

Legacy Vite sources are preserved under `_legacy/` for reference during migration.
