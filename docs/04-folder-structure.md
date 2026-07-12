# Athena AI Terminal

## Folder Structure & Development Standards

**Version:** 1.0

---

# 1. Project Structure

```text
athena-ai-terminal/
│
├── backend/                 # FastAPI Backend
│
├── frontend/                # React Application
│
├── docs/                    # Project Documentation
│
├── scripts/                 # Utility Scripts
│
├── docker/                  # Docker Files
│
├── tests/                   # End-to-End Tests
│
├── .github/                 # GitHub Actions
│
├── .env.example             # Environment Variables Example
│
├── docker-compose.yml
│
├── README.md
│
└── LICENSE
```

---

# 2. Backend Structure

```text
backend/
│
├── app/
│   │
│   ├── api/
│   │
│   ├── core/
│   │
│   ├── database/
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │
│   ├── market/
│   │
│   ├── indicators/
│   │
│   ├── patterns/
│   │
│   ├── news/
│   │
│   ├── ai/
│   │
│   ├── risk/
│   │
│   ├── trading/
│   │
│   ├── websocket/
│   │
│   ├── utils/
│   │
│   └── main.py
│
├── tests/
│
├── requirements.txt
│
├── .env
│
└── Dockerfile
```

---

# 3. Responsibility of Each Folder

## app/api

Contains REST API endpoints.

Example:

* health.py
* market.py
* indicators.py
* news.py
* trading.py

No business logic should be written here.

---

## app/core

Contains application configuration.

Examples:

* config.py
* logging.py
* constants.py

---

## app/database

Database-related code.

Examples:

* connection
* session
* migrations

---

## app/models

Database models.

Each table gets one model.

Examples:

* candle.py
* trade.py
* news.py

---

## app/schemas

API request and response models.

Examples:

* TradeRequest
* TradeResponse
* MarketResponse

---

## app/services

Business logic.

Examples:

* TradeService
* IndicatorService
* NewsService

---

## app/market

Everything related to MetaTrader 5.

Examples:

* MT5 connection
* Candle collector
* Tick collector
* Symbol manager

---

## app/indicators

Technical indicators.

Examples:

* EMA
* RSI
* MACD
* ATR
* VWAP

---

## app/patterns

Market structure detection.

Examples:

* BOS
* CHOCH
* Order Blocks
* FVG

---

## app/news

News collection and analysis.

---

## app/ai

Local AI integration.

Responsibilities:

* Prompt generation
* AI requests
* AI responses

---

## app/risk

Risk management.

Examples:

* Position sizing
* Stop Loss
* Risk validation

---

## app/trading

Trading engine.

Examples:

* Paper Trading
* Order Manager
* Trade Journal

---

## app/websocket

Real-time communication with the frontend.

---

## app/utils

Small helper functions shared across the project.

---

# 4. Frontend Structure

```text
frontend/
│
├── src/
│   │
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── hooks/
│   ├── stores/
│   ├── types/
│   ├── assets/
│   └── App.tsx
│
└── package.json
```

---

# 5. Naming Rules

Folders

* lowercase

Files

* snake_case.py

Classes

* PascalCase

Functions

* snake_case()

Constants

* UPPER_CASE

Variables

* snake_case

---

# 6. Git Workflow

Branches

main

Stable code only.

develop

Daily development.

Feature branches

feature/backend

feature/database

feature/mt5

feature/dashboard

feature/ai

---

# 7. Commit Convention

Examples

```
feat: add MT5 connector

fix: resolve websocket issue

docs: update architecture

refactor: simplify indicator engine

test: add market tests

chore: update dependencies
```

---

# 8. Coding Standards

* Type hints required.
* Docstrings for public classes and functions.
* No hardcoded secrets.
* Keep functions small and focused.
* Handle exceptions where appropriate.
* Use logging instead of print().

---

# 9. Development Process

For every module:

1. Create folders.
2. Implement feature.
3. Test locally.
4. Commit to Git.
5. Push to GitHub.
6. Update documentation.

Only then move to the next module.

---

# 10. Definition of Complete Module

A module is complete only when:

* Code runs without errors.
* APIs are tested.
* Documentation is updated.
* Changes are committed to Git.
* Code is pushed to GitHub.

```
```
