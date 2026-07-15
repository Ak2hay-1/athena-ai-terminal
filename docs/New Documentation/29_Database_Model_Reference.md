# Athena AI Terminal
# Database Model Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Database Model Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Database Engineers, QA Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. ORM Architecture
3. Model Standards
4. Current Models
5. MarketCandle
6. Recommendation
7. User
8. Watchlist
9. Future Models
10. Relationships
11. Index Strategy
12. Constraints
13. Repository Mapping
14. Service Mapping
15. Migration Guidelines
16. Best Practices
17. Related Documents

---

# 1. Introduction

This document describes every SQLAlchemy ORM model used by Athena.

Each model section includes:

- Purpose
- Database table
- Fields
- Data types
- Constraints
- Relationships
- Indexes
- Validation
- Repository usage
- Service usage
- Example record

---

# 2. ORM Architecture

Athena uses SQLAlchemy ORM.

Architecture

```text
Service

↓

Repository

↓

SQLAlchemy Model

↓

PostgreSQL
```

Repositories are the only components that directly manipulate ORM models.

---

# 3. Model Standards

Every ORM model should follow these standards.

Required:

- Explicit table name
- Primary key
- Type annotations
- Docstrings
- Created timestamp (where applicable)
- Updated timestamp (where applicable)

Avoid:

- Business logic
- API validation
- HTTP concerns

Models should represent persistence only.

---

# 4. Current Models

Current production models:

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

BacktestRun

RiskProfile
```

---

# 5. MarketCandle

## Purpose

Represents a single OHLCV candle.

---

## Table

```
market_candles
```

---

## Used By

Repositories

```
MarketRepository
```

Services

```
MarketService
```

Scheduler

```
MarketScheduler
```

Indicator Engine

Pattern Engine

Recommendation Engine

---

## Fields

| Field | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| symbol | String | Trading symbol |
| timeframe | String | Candle timeframe |
| timestamp | DateTime | Candle open time |
| open | Float | Open price |
| high | Float | High price |
| low | Float | Low price |
| close | Float | Close price |
| tick_volume | Integer | Tick volume |
| spread | Integer | Broker spread |
| real_volume | Integer | Exchange volume (if available) |
| created_at | DateTime | Insert timestamp |

---

## Primary Key

```
id
```

---

## Recommended Unique Constraint

```
(symbol, timeframe, timestamp)
```

Prevents duplicate candles.

---

## Recommended Indexes

```
symbol

timeframe

timestamp

(symbol,timeframe)

(symbol,timeframe,timestamp)
```

---

## Relationships

None.

Market candles are independent records.

---

## Validation Rules

- High ≥ Open
- High ≥ Close
- Low ≤ Open
- Low ≤ Close
- Volume ≥ 0

---

## Example

```text
Symbol

XAUUSD

Timeframe

M1

Timestamp

2026-07-15 12:30:00

Open

3362.10

High

3363.20

Low

3361.90

Close

3362.75
```

---

# 6. Recommendation

## Purpose

Stores AI-generated trading recommendations.

---

## Table

```
recommendations
```

---

## Used By

RecommendationRepository

RecommendationService

RecommendationEngine

REST API

WebSocket

---

## Fields

| Field | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| symbol | String | Trading symbol |
| timeframe | String | Candle timeframe |
| signal | Enum | BUY / SELL / HOLD |
| entry | Float | Entry price |
| stop_loss | Float | Stop loss |
| take_profit | Float | Take profit |
| confidence | Integer | Confidence score |
| risk_reward | Float | Risk-reward ratio |
| trend | String | Trend classification |
| summary | Text | AI explanation |
| created_at | DateTime | Recommendation timestamp |

---

## Indexes

```
symbol

timeframe

signal

created_at
```

---

## Validation

Signal values:

```
BUY

SELL

HOLD
```

Confidence

```
0–100
```

Risk reward

```
>=0
```

---

## Example

```text
Signal

BUY

Entry

3360.25

Stop Loss

3354.00

Take Profit

3374.50

Confidence

87
```

---

# 7. User

## Purpose

Represents an authenticated Athena user.

(Currently planned for future authentication.)

---

## Table

```
users
```

---

## Fields

| Field | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String | Login name |
| email | String | Email address |
| password_hash | String | Hashed password |
| role | String | User role |
| is_active | Boolean | Active account |
| created_at | DateTime | Account creation |
| updated_at | DateTime | Last update |

---

## Relationships

```
Watchlist

Recommendations (future)

Strategies (future)
```

---

## Unique Constraints

```
username

email
```

---

## Roles

Future roles:

```
Admin

Trader

Viewer
```

---

# 8. Watchlist

## Purpose

Stores user-selected trading symbols.

---

## Table

```
watchlists
```

---

## Fields

| Field | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Owner |
| symbol | String | Trading symbol |
| created_at | DateTime | Added date |

---

## Foreign Keys

```
user_id

↓

users.id
```

---

## Relationships

```
User

↓

Watchlist
```

One user

↓

Many watchlist entries

---

## Unique Constraint

```
(user_id,symbol)
```

Prevents duplicate watchlist items.

---

# 9. Future Models

Planned additions

### Portfolio

Tracks investment portfolios.

---

### Position

Tracks open broker positions.

---

### Trade

Historical executed trades.

---

### Strategy

Stores algorithmic strategies.

---

### RiskProfile

User risk configuration.

---

### Notification

System notifications.

---

### AuditLog

Security auditing.

---

### BacktestRun

Historical strategy evaluation.

---

# 10. Relationships

Current

```text
User

↓

Watchlist
```

Future

```text
User

↓

Strategies

↓

Recommendations

↓

Trades

↓

Portfolio
```

Market candles remain intentionally independent for performance.

---

# 11. Index Strategy

General rules

Index

- Frequently queried fields
- Foreign keys
- Timestamp columns
- Composite search keys

Avoid indexing:

- Low-cardinality fields without query value
- Large text columns

---

# 12. Constraints

Examples

Unique

```
(symbol,timeframe,timestamp)
```

Foreign key

```
watchlist.user_id

↓

users.id
```

Check constraints (future)

```
confidence

0–100
```

```
risk_reward >= 0
```

---

# 13. Repository Mapping

| Repository | Models |
|------------|--------|
| MarketRepository | MarketCandle |
| RecommendationRepository | Recommendation |
| UserRepository | User |
| WatchlistRepository | Watchlist |

Future repositories should maintain one primary model ownership while supporting read-only access to related models as needed.

---

# 14. Service Mapping

| Service | Models |
|----------|--------|
| MarketService | MarketCandle |
| RecommendationService | Recommendation |
| UserService | User |
| WatchlistService | Watchlist |

Services coordinate workflows but do not expose ORM models directly to API consumers.

---

# 15. Migration Guidelines

Schema changes should follow this process:

```text
Model Update

↓

Migration Generation

↓

Migration Review

↓

Apply to Development

↓

Integration Testing

↓

Staging Validation

↓

Production Deployment
```

Migration guidelines:

- Never edit applied migrations.
- Prefer additive changes.
- Backfill new columns where required.
- Test downgrade paths when practical.
- Review index impact before deployment.

---

# 16. Best Practices

- Keep ORM models focused on persistence.
- Use descriptive column names.
- Prefer explicit constraints.
- Index frequently queried columns.
- Store timestamps in UTC.
- Do not place business logic inside models.
- Keep migrations small and reviewable.
- Document every schema change.

---

# 17. Related Documents

Architecture

- 06_Database_Design.md
- 17_Repository_Layer.md
- 18_Service_Layer.md

Implementation

- 26_Codebase_Reference.md
- 27_Backend_Package_Reference.md
- 28_API_Reference.md
- 31_Repository_Class_Reference.md

Operations

- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 22_Security_Guide.md

---

# Model Change Checklist

Before modifying an ORM model:

- [ ] Schema reviewed
- [ ] Migration created
- [ ] Constraints updated
- [ ] Indexes reviewed
- [ ] Repository updated
- [ ] Service updated
- [ ] API schema updated (if required)
- [ ] Tests updated
- [ ] Documentation updated

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial database model reference |

---

**Document End**

© Athena AI Terminal Project
