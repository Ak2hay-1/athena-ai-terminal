# Athena AI Terminal
# Backend Package Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Backend Package Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Software Architects, AI Engineers, QA Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Backend Overview
3. Package Dependency Rules
4. Package Directory Structure
5. Package Reference
6. Data Flow
7. Extension Guidelines
8. Package Ownership Matrix
9. Package Relationships
10. Future Packages
11. Related Documents

---

# 1. Introduction

The backend is the heart of Athena.

It contains every major subsystem responsible for:

- REST API
- WebSockets
- AI
- MT5 Integration
- Database
- Scheduler
- Business Logic
- Technical Analysis
- Recommendation Generation

The backend is implemented as a **modular monolith**, where each package has a clearly defined responsibility.

---

# 2. Backend Overview

```
backend/

└── app/

    api/
    ai/
    analysis/
    backtesting/
    config/
    core/
    database/
    indicators/
    middleware/
    models/
    mt5/
    patterns/
    repositories/
    scheduler/
    schemas/
    services/
    utils/
    websocket/

    main.py
```

Each package is documented below.

---

# 3. Package Dependency Rules

Allowed dependency direction:

```
API

↓

Services

↓

Repositories

↓

Database
```

Additional integrations:

```
Services

↓

AI

↓

MT5

↓

Scheduler
```

Repositories never call Services.

Services never call API routes.

Database models never contain business logic.

---

# 4. Package Directory Structure

```
backend/app/

api/

ai/

analysis/

backtesting/

config/

core/

database/

indicators/

middleware/

models/

mt5/

patterns/

repositories/

scheduler/

schemas/

services/

utils/

websocket/

main.py
```

---

# 5. Package Reference

---

# api/

## Purpose

Expose REST endpoints.

---

## Responsibilities

- Route registration
- Request validation
- Response serialization
- HTTP status codes
- OpenAPI generation

---

## Contains

Typical modules:

```
health.py

market.py

recommendation.py

user.py

watchlist.py
```

---

## Depends On

- Services
- Schemas

---

## Must Never Access

- SQLAlchemy
- Database sessions
- MT5
- AI directly

---

# ai/

## Purpose

Provide AI integration.

---

## Responsibilities

- Prompt construction
- LLM communication
- Response validation
- Recommendation generation
- AI provider abstraction

---

## Current Modules

```
client.py

prompt_builder.py

recommendation_engine.py

response_parser.py
```

---

## Future Modules

```
provider_manager.py

conversation_memory.py

prompt_templates.py

token_counter.py
```

---

## Depends On

- requests
- Pydantic
- Services

---

# analysis/

## Purpose

Combine technical analysis into market intelligence.

---

## Responsibilities

- Trend analysis
- Market structure
- Confluence scoring
- Volatility analysis
- Multi-timeframe analysis

---

## Typical Outputs

```
Trend

Momentum

Market Bias

Confluence Score
```

---

## Depends On

- Indicators
- Patterns

---

# backtesting/

## Purpose

Evaluate strategies using historical data.

---

## Responsibilities

- Historical simulation
- Trade statistics
- Win rate
- Profit factor
- Drawdown

---

## Current Status

Early implementation.

Future expansion planned.

---

# config/

## Purpose

Application configuration.

---

## Responsibilities

- Environment variables
- Settings
- Feature flags
- Defaults

---

## Typical Files

```
settings.py

constants.py
```

---

## Depends On

- Pydantic Settings

---

# core/

## Purpose

Shared infrastructure.

---

## Responsibilities

- Logging
- Exceptions
- Startup
- Middleware
- Utilities
- Request IDs

---

## Contains

```
logging.py

exceptions.py

startup.py
```

---

# database/

## Purpose

Database infrastructure.

---

## Responsibilities

- Engine creation
- Sessions
- Base model
- Initialization

---

## Contains

```
database.py

session.py

base.py
```

---

## Used By

Repositories

---

# indicators/

## Purpose

Calculate technical indicators.

---

## Responsibilities

- RSI
- EMA
- SMA
- ATR
- MACD
- Bollinger Bands
- ADX
- VWAP
- Volume indicators

---

## Characteristics

Pure calculations.

No database access.

---

# middleware/

## Purpose

HTTP middleware.

---

## Responsibilities

- Request timing
- Logging
- Request IDs
- CORS
- Compression

---

## Depends On

FastAPI

---

# models/

## Purpose

SQLAlchemy ORM models.

---

## Responsibilities

Represent database tables.

---

## Current Models

```
MarketCandle

Recommendation

User

Watchlist
```

---

## Future Models

```
Portfolio

Position

Trade

AuditLog
```

---

# mt5/

## Purpose

MetaTrader integration.

---

## Responsibilities

- Connection
- Authentication
- Market data
- Historical candles
- Trading (future)

---

## Current Modules

```
manager.py

interfaces.py

candle_collector.py
```

---

## Future Modules

```
order_manager.py

position_manager.py

account_manager.py
```

---

# patterns/

## Purpose

Smart Money Concepts detection.

---

## Responsibilities

- BOS
- CHoCH
- FVG
- Liquidity
- Order Blocks
- Premium/Discount
- Swing Detection

---

## Characteristics

Pure analytical logic.

---

# repositories/

## Purpose

Database persistence.

---

## Responsibilities

- CRUD
- Queries
- Batch inserts
- Transactions

---

## Current Repositories

```
MarketRepository

RecommendationRepository

UserRepository

WatchlistRepository
```

---

## Depends On

Database

Models

---

# scheduler/

## Purpose

Background automation.

---

## Responsibilities

- Market synchronization
- AI execution
- Periodic analysis
- Cleanup jobs

---

## Current Jobs

```
collect_xauusd_m1()
```

---

## Future Jobs

```
cleanup_database()

backup_database()

health_check()

analytics_refresh()
```

---

# schemas/

## Purpose

Pydantic models.

---

## Responsibilities

- Request validation
- Response serialization
- API contracts

---

## Characteristics

No business logic.

---

# services/

## Purpose

Business logic.

---

## Responsibilities

- Workflow orchestration
- AI coordination
- Repository coordination
- MT5 coordination

---

## Current Services

```
MarketService

RecommendationService

MT5Service

UserService

WatchlistService
```

---

## Central Rule

Business logic belongs here.

---

# utils/

## Purpose

Reusable helper functions.

---

## Examples

```
Date utilities

Timeframe conversion

Formatting

Validation helpers
```

---

## Characteristics

Independent.

Stateless.

Reusable.

---

# websocket/

## Purpose

Real-time communication.

---

## Responsibilities

- Connections
- Broadcast
- Subscription management
- Streaming

---

## Current Modules

```
connection_manager.py

market_stream.py

routes.py
```

---

## Future

```
notifications.py

presence.py

heartbeat.py
```

---

# main.py

## Purpose

Application entry point.

---

## Responsibilities

- Create FastAPI app
- Register middleware
- Register routers
- Initialize database
- Initialize MT5
- Start scheduler
- Shutdown cleanup

---

# 6. Data Flow

Typical workflow:

```
HTTP Request

↓

API

↓

Service

↓

Repository

↓

Database

↓

Service

↓

API Response
```

Recommendation workflow:

```
Scheduler

↓

MT5

↓

Indicators

↓

Patterns

↓

Analysis

↓

AI

↓

Repository

↓

WebSocket
```

---

# 7. Extension Guidelines

When adding a feature:

### API

Create a new route.

↓

### Schema

Add request/response models.

↓

### Service

Implement business logic.

↓

### Repository

Add persistence methods.

↓

### Tests

Add unit/integration tests.

↓

### Documentation

Update relevant documents.

---

# 8. Package Ownership Matrix

| Package | Owns |
|----------|------|
| api | HTTP Interface |
| ai | AI Communication |
| analysis | Market Intelligence |
| backtesting | Historical Evaluation |
| config | Configuration |
| core | Infrastructure |
| database | Database Infrastructure |
| indicators | Technical Indicators |
| middleware | HTTP Pipeline |
| models | ORM Entities |
| mt5 | Broker Integration |
| patterns | Smart Money Concepts |
| repositories | Persistence |
| scheduler | Automation |
| schemas | Validation |
| services | Business Logic |
| utils | Shared Utilities |
| websocket | Real-Time Communication |

---

# 9. Package Relationships

```
main.py

↓

API

↓

Services

↓

Repositories

↓

Database
```

Additional interactions:

```
Services

↓

Indicators

↓

Patterns

↓

Analysis

↓

AI

↓

MT5
```

---

# 10. Future Packages

Potential future additions:

```
portfolio/

orders/

risk/

analytics/

notifications/

plugins/

news/

reports/

ml/

telemetry/
```

Each new package should have:

- A single responsibility
- Clear ownership
- Minimal dependencies
- Dedicated documentation

---

# 11. Related Documents

Architecture

- 05_Backend_Architecture.md
- 17_Repository_Layer.md
- 18_Service_Layer.md

Reference

- 28_API_Reference.md
- 29_Database_Model_Reference.md
- 30_Service_Class_Reference.md
- 31_Repository_Class_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md
- 34_Configuration_Reference.md
- 35_Environment_Variables_Reference.md
- 36_Error_Code_Reference.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial backend package reference |

---

**Document End**

© Athena AI Terminal Project
