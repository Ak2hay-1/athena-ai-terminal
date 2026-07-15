# Athena AI Terminal
# Codebase Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Codebase Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Developers, Architects, QA Engineers, DevOps Engineers, AI Assistants |

---

# Table of Contents

1. Purpose
2. Documentation Strategy
3. Source Code Organization
4. Backend Package Map
5. Frontend Package Map
6. Core Workflows
7. Dependency Graph
8. Package Reference Index
9. Class Reference Index
10. Configuration Files
11. Environment Variables
12. Database Models
13. API Endpoints
14. Scheduler Jobs
15. AI Modules
16. MT5 Modules
17. Testing Structure
18. Documentation Cross Reference
19. Navigation Guide
20. Future Expansion

---

# 1. Purpose

This document serves as the master index for the Athena codebase.

Unlike architecture documents that describe design decisions, this document explains:

- Where code lives
- What each module does
- How modules interact
- Where developers should implement changes
- Where to find detailed documentation

Every source directory should eventually be documented.

---

# 2. Documentation Strategy

Athena documentation is divided into two categories.

## Architecture Documentation

Describes:

- Why the system is built
- Design decisions
- System architecture
- Business workflows

Located in:

```
docs/01_*.md
...
docs/25_*.md
```

---

## Code Reference Documentation

Describes:

- Packages
- Modules
- Classes
- Functions
- Interfaces
- Configurations

Located in:

```
docs/26_*.md
...
docs/40_*.md
```

---

# 3. Source Code Organization

Current repository structure

```text
athena-ai-terminal/

backend/
frontend/
docs/
scripts/
docker/
```

Backend contains all business logic.

Frontend (future) contains user interface.

Documentation contains engineering handbook and code reference.

---

# 4. Backend Package Map

```text
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

Each package will have its own reference document.

---

# 5. Frontend Package Map

Planned structure

```text
frontend/

components/
pages/
hooks/
services/
contexts/
stores/
assets/
styles/
utils/
```

Frontend documentation will be added after implementation.

---

# 6. Core Workflows

Primary workflows currently implemented

---

## Application Startup

```text
main.py

↓

Configuration

↓

Logger

↓

Database

↓

MT5

↓

Scheduler

↓

REST API

↓

WebSocket
```

---

## Market Collection

```text
Scheduler

↓

MT5

↓

Repository

↓

Database
```

---

## Recommendation Generation

```text
Scheduler

↓

MarketService

↓

Indicator Engine

↓

Pattern Engine

↓

AI

↓

Recommendation Repository
```

---

## REST API

```text
Request

↓

Router

↓

Service

↓

Repository

↓

Database

↓

Response
```

---

## WebSocket

```text
Client

↓

Connection Manager

↓

Broadcast

↓

Client
```

---

# 7. Dependency Graph

Allowed dependencies

```text
API

↓

Service

↓

Repository

↓

Database
```

Additional integrations

```text
Service

↓

AI

↓

MT5

↓

Scheduler
```

Repositories must never call Services.

Services must never call API routes.

---

# 8. Package Reference Index

The following documents provide package-level references.

| Document | Description |
|----------|-------------|
| 27_Backend_Package_Reference.md | Every backend package |
| 28_API_Reference.md | REST API implementation |
| 29_Database_Model_Reference.md | SQLAlchemy models |
| 30_Service_Class_Reference.md | Business services |
| 31_Repository_Class_Reference.md | Repository implementations |
| 32_AI_Module_Reference.md | AI subsystem |
| 33_MT5_Module_Reference.md | MT5 integration |
| 34_Configuration_Reference.md | Configuration system |
| 35_Environment_Variables_Reference.md | Environment variables |
| 36_Error_Code_Reference.md | Error catalog |

---

# 9. Class Reference Index

Every major class should eventually be documented.

Current core classes include:

```
Settings

Database

MarketRepository

RecommendationRepository

MarketService

RecommendationService

RecommendationEngine

PromptBuilder

OllamaClient

MT5Manager

MarketScheduler

ConnectionManager
```

Each class reference should include:

- Purpose
- Constructor
- Dependencies
- Public methods
- Internal methods
- Usage examples
- Thread safety
- Error conditions

---

# 10. Configuration Files

Current configuration files

```
.env

requirements.txt

pyproject.toml (future)

alembic.ini (future)

docker-compose.yml

Dockerfile
```

Each file will have dedicated documentation.

---

# 11. Environment Variables

Examples

```
DATABASE_URL

MT5_LOGIN

MT5_PASSWORD

MT5_SERVER

MT5_PATH

OLLAMA_URL

OLLAMA_MODEL

SECRET_KEY

JWT_SECRET
```

Detailed documentation:

```
35_Environment_Variables_Reference.md
```

---

# 12. Database Models

Current models include:

```
MarketCandle

Recommendation

User

Watchlist
```

Future models:

```
Portfolio

Position

Trade

Strategy

Notification

AuditLog
```

Reference:

```
29_Database_Model_Reference.md
```

---

# 13. API Endpoints

Current API groups

```
/health

/market

/recommendations

/watchlist

/users

/ws
```

Future groups

```
/portfolio

/orders

/positions

/strategies

/auth

/admin
```

Reference:

```
28_API_Reference.md
```

---

# 14. Scheduler Jobs

Current jobs

```
collect_xauusd_m1()

analyze_market()
```

Future jobs

```
cleanup_database()

retrain_models()

generate_reports()

health_check()

backup_database()
```

---

# 15. AI Modules

Current AI modules

```
client.py

prompt_builder.py

recommendation_engine.py

response_parser.py
```

Future modules

```
provider_manager.py

token_counter.py

prompt_versioning.py

conversation_memory.py
```

---

# 16. MT5 Modules

Current modules

```
manager.py

interfaces.py

candle_collector.py
```

Future modules

```
order_manager.py

position_manager.py

account_manager.py
```

---

# 17. Testing Structure

Planned test layout

```text
tests/

unit/

integration/

e2e/

performance/

fixtures/

data/
```

Every package should have corresponding tests.

---

# 18. Documentation Cross Reference

Architecture documents explain **why**.

Reference documents explain **how**.

Developers should consult both when making changes.

Example:

```
Need to understand Recommendation Engine

↓

Read:

12_Recommendation_Engine.md

↓

Then:

32_AI_Module_Reference.md
```

---

# 19. Navigation Guide

Common tasks

### Add API

Read:

```
28_API_Reference.md

18_Service_Layer.md
```

---

### Add Database Table

Read:

```
29_Database_Model_Reference.md

17_Repository_Layer.md
```

---

### Improve AI

Read:

```
08_AI_Architecture.md

32_AI_Module_Reference.md
```

---

### Fix Scheduler

Read:

```
16_Background_Scheduler.md

33_MT5_Module_Reference.md
```

---

# 20. Future Expansion

As Athena grows, this reference will expand to include:

- Every package
- Every module
- Every class
- Every function
- Every environment variable
- Every configuration file
- Every API endpoint
- Every scheduler job
- Every database model
- Every WebSocket event
- Every error code
- Every migration
- Every deployment script

The objective is for a developer—or another AI assistant—to understand the entire implementation without needing to inspect the source code first.

---

# Related Documents

### Engineering Handbook

01–25

### Implementation Reference

27–40

### AI Continuation

99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial codebase reference |

---

**Document End**

© Athena AI Terminal Project
