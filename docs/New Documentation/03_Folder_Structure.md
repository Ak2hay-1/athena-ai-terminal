# Athena AI Terminal
# Folder Structure

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Folder Structure |
| Version | 1.0 |
| Status | Draft |
| Last Updated | July 2026 |
| Audience | Developers, DevOps, AI Assistants |

---

# Table of Contents

1. Purpose
2. Philosophy
3. Project Layout
4. Backend Structure
5. Frontend Structure
6. Documentation Structure
7. Configuration Files
8. Naming Conventions
9. Layer Responsibilities
10. Dependency Rules
11. Adding New Modules
12. Best Practices

---

# 1. Purpose

The project structure is designed to provide:

- Maximum maintainability
- Easy navigation
- Separation of concerns
- Independent modules
- High scalability
- Predictable organization

Every directory has a single responsibility.

---

# 2. Philosophy

Athena follows a layered architecture.

Each layer has one purpose.

```
Presentation

↓

Business Logic

↓

Repository

↓

Database
```

No module should violate this architecture.

---

# 3. Project Layout

```
Athena-AI-Terminal/

│

├── backend/

├── frontend/

├── docs/

├── scripts/

├── docker/

├── .github/

├── README.md

├── LICENSE

└── .gitignore
```

---

# 4. Backend Structure

```
backend/

│

├── app/

├── migrations/

├── tests/

├── requirements.txt

├── pyproject.toml

├── alembic.ini

└── .env
```

---

# 5. app/

The application source code.

```
app/

│

├── api/

├── ai/

├── analysis/

├── auth/

├── backtesting/

├── core/

├── database/

├── indicators/

├── models/

├── mt5/

├── patterns/

├── repositories/

├── scheduler/

├── schemas/

├── services/

├── websocket/

└── main.py
```

---

# 6. api/

Contains every REST endpoint.

```
api/

│

├── router.py

├── websocket.py

└── v1/
```

Responsibilities

- HTTP Endpoints
- Request validation
- Response models

Never place business logic here.

---

# 7. ai/

Artificial Intelligence layer.

Contains

```
client.py

prompt_builder.py

response_parser.py

recommendation_engine.py

models.py
```

Responsibilities

- Prompt generation
- LLM communication
- AI validation
- Recommendation generation

---

# 8. analysis/

Market intelligence.

Responsibilities

- Trend analysis
- Indicator aggregation
- Pattern aggregation
- Confluence calculation

This layer combines every analysis module.

---

# 9. auth/

Authentication.

Contains

- JWT
- Password hashing
- Login
- Registration
- Dependencies

---

# 10. backtesting/

Historical testing.

Responsibilities

- Strategy replay
- Trade simulation
- Performance metrics

---

# 11. core/

Application infrastructure.

Contains

- Logger
- Settings
- Constants
- Middleware
- Exceptions
- Configuration

Nothing outside the application should depend on implementation details here.

---

# 12. database/

Database configuration.

Contains

```
engine

session

base

initialization

migrations
```

---

# 13. indicators/

Technical indicators.

Each indicator lives in its own file.

Example

```
ema.py

rsi.py

macd.py

atr.py
```

Each file implements one indicator only.

---

# 14. models/

SQLAlchemy ORM models.

Example

```
user.py

market_candle.py

recommendation.py
```

No business logic.

Models represent database tables only.

---

# 15. mt5/

MetaTrader integration.

Contains

```
connection.py

client.py

manager.py

providers.py

interfaces.py

mappers.py

candle_collector.py
```

Responsibilities

- MT5 Connection
- Market retrieval
- Symbol management

---

# 16. patterns/

Smart Money Concepts.

Contains

```
BOS

CHOCH

FVG

Liquidity

Order Block

Premium Discount

Trend Structure
```

Each pattern detector is independent.

---

# 17. repositories/

Database access.

Responsibilities

- CRUD
- Queries
- Pagination
- Search

Repositories never contain business logic.

---

# 18. scheduler/

Background jobs.

Responsibilities

- Candle collection
- Recommendation generation
- Future maintenance jobs

---

# 19. schemas/

Pydantic models.

Responsibilities

- Request validation
- Response validation
- Serialization

---

# 20. services/

Business logic.

Responsibilities

- Market Service
- User Service
- Auth Service
- MT5 Service

Services coordinate repositories.

---

# 21. websocket/

Real-time communication.

Responsibilities

- Live prices
- Recommendations
- Notifications

---

# 22. tests/

Testing suite.

```
unit/

integration/

performance/

fixtures/
```

---

# 23. frontend/

Frontend application.

```
frontend/

src/

components/

pages/

hooks/

services/

store/

styles/

assets/
```

---

# 24. docs/

Project documentation.

Contains every document describing Athena.

Documentation is treated as source code.

---

# 25. Configuration Files

```
.env

.env.example

pyproject.toml

requirements.txt

alembic.ini
```

---

# 26. Naming Convention

Directories

snake_case

Python files

snake_case.py

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

---

# 27. Dependency Rules

Allowed

```
API

↓

Service

↓

Repository

↓

Database
```

Forbidden

```
Repository

↓

Service

Repository

↓

API

Model

↓

Repository

Pattern

↓

API
```

Always depend downward.

---

# 28. Adding New Modules

Before creating a new module ask

Does it already belong somewhere?

If yes

Do not create another directory.

If no

Create

Directory

README

Tests

Documentation

---

# 29. Best Practices

Keep modules small.

One responsibility per class.

Avoid circular imports.

Prefer dependency injection.

Use type hints everywhere.

Document every public function.

Write tests for new features.

Never duplicate business logic.

---

# Folder Ownership

| Folder | Responsibility |
|---------|----------------|
| api | HTTP |
| ai | AI |
| analysis | Market Intelligence |
| auth | Authentication |
| core | Infrastructure |
| database | Persistence |
| indicators | Technical Analysis |
| models | ORM |
| mt5 | MT5 Integration |
| patterns | Smart Money |
| repositories | Data Access |
| scheduler | Automation |
| schemas | Validation |
| services | Business Logic |
| websocket | Live Communication |

---

# Related Documents

01_Project_Overview.md

02_System_Architecture.md

04_Technology_Stack.md

05_Backend_Architecture.md

10_Developer_Guide.md

99_AI_Continuation_Context.md

---

Document End

© Athena AI Terminal Project
