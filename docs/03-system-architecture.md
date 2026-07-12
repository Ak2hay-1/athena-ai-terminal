# Athena AI Terminal

## System Architecture

**Version:** 1.0

---

# 1. System Overview

Athena AI Terminal is a modular AI-assisted trading platform.

The system is divided into independent modules so each component can be developed, tested, and maintained separately.

```
                        User
                          │
                          ▼
                React Dashboard
                          │
                 REST API / WebSocket
                          │
                    FastAPI Backend
                          │
      ┌──────────┬────────┼────────┬─────────┐
      │          │        │        │         │
 Configuration Database Market   AI Engine Risk Engine
                          │
                    Trading Engine
                          │
                    MetaTrader 5
```

---

# 2. High-Level Modules

## Core

Responsible for the application's foundation.

Components:

* Configuration
* Logging
* Utilities
* Error Handling

---

## Market Engine

Responsibilities:

* Connect to MT5
* Read live candles
* Read live ticks
* Manage symbols
* Manage timeframes

---

## Indicator Engine

Responsibilities:

* EMA
* RSI
* MACD
* ATR
* Bollinger Bands
* VWAP

---

## Market Structure Engine

Responsibilities:

* Trend detection
* Support & Resistance
* Break of Structure (BOS)
* Change of Character (CHOCH)
* Fair Value Gap (FVG)
* Order Blocks

---

## News Engine

Responsibilities:

* Economic calendar
* News collection
* News categorization
* Impact scoring

---

## AI Engine

Responsibilities:

* Technical analysis
* News analysis
* Trade explanation
* Confidence scoring

Local AI:

* Ollama
* Qwen

---

## Risk Engine

Responsibilities:

* Position sizing
* Stop-loss validation
* Take-profit calculation
* Daily loss limits
* Risk/Reward validation

---

## Trading Engine

Modes:

* Paper Trading
* Backtesting
* Live Trading (future)

Responsibilities:

* Trade execution
* Position management
* Trade journal

---

## Dashboard

Responsibilities:

* Live market view
* Charts
* Indicators
* AI analysis
* News
* Trade history
* System status

---

# 3. Data Flow

```
MetaTrader 5
      │
      ▼
Market Engine
      │
      ▼
Database
      │
      ▼
Indicator Engine
      │
      ▼
Market Structure Engine
      │
      ▼
News Engine
      │
      ▼
AI Engine
      │
      ▼
Risk Engine
      │
      ▼
Trading Engine
      │
      ▼
Dashboard & Telegram
```

---

# 4. Folder Structure

```
athena-ai-terminal/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── indicators/
│   │   ├── market/
│   │   ├── ai/
│   │   ├── risk/
│   │   ├── trading/
│   │   ├── websocket/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│
├── docs/
│
├── scripts/
│
├── docker/
│
└── tests/
```

---

# 5. Technology Stack

Backend

* Python 3.13
* FastAPI
* SQLAlchemy
* Alembic

Frontend

* React
* TypeScript
* Tailwind CSS

Database

* PostgreSQL

Cache

* Redis

AI

* Ollama
* Qwen

Trading

* MetaTrader 5 Python API

Deployment

* Docker
* Docker Compose

---

# 6. Development Rules

* One module at a time.
* Every module must compile successfully.
* Every module must be tested.
* Every module must be committed to Git.
* No unfinished features on the main branch.

---

# 7. Initial Development Order

1. Backend Foundation
2. Configuration
3. Logging
4. Database
5. Docker
6. MetaTrader 5 Connection
7. Market Data
8. Technical Indicators
9. Market Structure
10. News Engine
11. AI Engine
12. Paper Trading
13. Dashboard
14. Telegram Bot
15. Backtesting

---

# 8. Future Expansion

The architecture is designed to support:

* Multiple symbols
* Multiple brokers
* Additional AI models
* Live trading
* Cloud deployment
* User authentication
* Mobile application

without major changes to the core structure.
