# Athena AI Terminal
# Repository Class Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Repository Class Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Database Engineers, Architects, AI Assistants |

---

# Table of Contents

1. Introduction
2. Repository Architecture
3. Repository Design Rules
4. Session Lifecycle
5. BaseRepository
6. MarketRepository
7. RecommendationRepository
8. UserRepository
9. WatchlistRepository
10. Transactions
11. Query Optimization
12. Error Handling
13. Logging
14. Performance Guidelines
15. Extension Guidelines
16. Related Documents

---

# 1. Introduction

Repositories are responsible for every interaction with PostgreSQL.

Repositories provide:

- CRUD operations
- Query abstraction
- Transaction management
- Batch operations
- Database isolation

Repositories never contain business logic.

---

# 2. Repository Architecture

```
REST API

↓

Service

↓

Repository

↓

SQLAlchemy

↓

PostgreSQL
```

Repositories are the only layer permitted to manipulate ORM models.

---

# 3. Repository Design Rules

Repositories should:

- Own one persistence domain
- Expose clear methods
- Hide SQLAlchemy details
- Handle transactions safely
- Return domain-friendly objects

Repositories should never:

- Call services
- Call APIs
- Generate AI prompts
- Perform indicator calculations
- Implement trading logic

---

# 4. Session Lifecycle

Typical flow

```
Create Session

↓

Execute Query

↓

Commit

↓

Close Session
```

For read-only operations

```
Session

↓

SELECT

↓

Return

↓

Close
```

For writes

```
Session

↓

INSERT / UPDATE / DELETE

↓

Commit

↓

Close
```

---

# 5. BaseRepository

## Purpose

Provides shared functionality used by specialized repositories.

---

## Responsibilities

- Session management
- Common CRUD helpers
- Transaction helpers
- Utility methods

---

## Typical Methods

```python
create()

update()

delete()

get_by_id()

exists()

commit()

rollback()
```

---

## Constructor

```python
BaseRepository(
    session: Session
)
```

Repositories receive sessions through dependency injection.

---

## Notes

Avoid placing business-specific queries here.

---

# 6. MarketRepository

## Purpose

Manage market candle persistence.

---

## Table

```
market_candles
```

---

## Used By

```
MarketService

MarketScheduler

Indicator Engine
```

---

## Responsibilities

- Save candles
- Retrieve history
- Retrieve latest candles
- Prevent duplicates
- Batch inserts

---

## Public Methods

```python
save_candles()

save_batch()

get_latest()

get_history()

existing_times()

delete_old_data()

count()

exists()
```

---

## Query Patterns

Latest candles

```sql
ORDER BY timestamp DESC
LIMIT n
```

Historical range

```sql
WHERE

symbol = ?

AND timeframe = ?

AND timestamp BETWEEN ...
```

Duplicate detection

```sql
WHERE

timestamp IN (...)
```

---

## Bulk Operations

Preferred workflow

```
Download

↓

Filter Existing

↓

Bulk Insert

↓

Commit
```

---

## Performance

Indexes

```
symbol

timeframe

timestamp

(symbol,timeframe)

(symbol,timeframe,timestamp)
```

---

## Logging

```
Inserted 500 candles.

Retrieved 300 candles.

Duplicate candles skipped.
```

---

# 7. RecommendationRepository

## Purpose

Persist AI recommendations.

---

## Table

```
recommendations
```

---

## Responsibilities

- Save recommendation
- Retrieve latest
- Recommendation history
- Filter recommendations

---

## Methods

```python
save()

get_latest()

get_history()

get_by_symbol()

get_between_dates()

delete()
```

---

## Typical Query

Latest recommendation

```sql
ORDER BY created_at DESC

LIMIT 1
```

---

## Logging

```
Recommendation stored.

History retrieved.
```

---

# 8. UserRepository

(Current implementation planned.)

---

## Purpose

User persistence.

---

## Responsibilities

- Create user
- Retrieve user
- Update profile
- Delete account

---

## Methods

```python
create()

get_by_email()

get_by_username()

update()

delete()
```

---

## Constraints

Unique

```
username

email
```

---

# 9. WatchlistRepository

## Purpose

Manage watchlist persistence.

---

## Responsibilities

- Add symbol
- Remove symbol
- Retrieve watchlist

---

## Methods

```python
add()

remove()

get_symbols()

exists()
```

---

## Unique Constraint

```
(user_id,symbol)
```

---

# 10. Transactions

Repositories should use explicit transactions.

Typical flow

```
Begin

↓

Repository Operations

↓

Commit

↓

Rollback (on failure)
```

Batch inserts should execute within a single transaction whenever possible.

---

# 11. Query Optimization

Guidelines

Use:

- Indexes
- Bulk inserts
- Pagination
- Projection
- Composite indexes

Avoid:

- N+1 queries
- SELECT *
- Long-running transactions

Always retrieve only required columns where practical.

---

# 12. Error Handling

Typical exceptions

```
IntegrityError

OperationalError

NoResultFound

DatabaseError
```

Repository strategy

```
Catch

↓

Rollback

↓

Log

↓

Raise Repository Exception
```

Do not expose raw SQL errors to higher layers.

---

# 13. Logging

Repositories should log:

Read

```
Retrieved 250 candles.
```

Write

```
Inserted 500 records.
```

Update

```
Updated recommendation.
```

Delete

```
Deleted 100 expired rows.
```

Include:

- Execution time
- Record count
- Table name
- Result

Never log sensitive values.

---

# 14. Performance Guidelines

Current optimizations

- Batch inserts
- Composite indexes
- Duplicate filtering

Future improvements

- Read replicas
- Partitioned tables
- Connection pooling
- Query caching
- Materialized views

Measure database performance before introducing additional complexity.

---

# 15. Extension Guidelines

When adding a repository

1. Create repository class

↓

2. Inject Session

↓

3. Implement CRUD

↓

4. Add query helpers

↓

5. Add logging

↓

6. Add tests

↓

7. Update documentation

Future repositories

```
PortfolioRepository

TradeRepository

PositionRepository

StrategyRepository

NotificationRepository

AuditRepository
```

Each repository should own a single primary persistence domain.

---

# 16. Related Documents

Architecture

- 06_Database_Design.md
- 17_Repository_Layer.md
- 18_Service_Layer.md

Implementation

- 29_Database_Model_Reference.md
- 30_Service_Class_Reference.md
- 32_AI_Module_Reference.md

Operations

- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md

---

# Repository Checklist

Before adding a repository:

- [ ] Single responsibility
- [ ] Session injection
- [ ] CRUD methods implemented
- [ ] Transactions handled correctly
- [ ] Logging added
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Documentation updated

---

# Repository Dependency Matrix

| Repository | Primary Model | Used By |
|------------|---------------|---------|
| MarketRepository | MarketCandle | MarketService, Scheduler |
| RecommendationRepository | Recommendation | RecommendationService, MarketService |
| UserRepository | User | UserService |
| WatchlistRepository | Watchlist | WatchlistService |

---

# Future Improvements

Future versions of this document should include:

- Complete method signatures
- SQLAlchemy query examples
- Transaction sequence diagrams
- Query execution benchmarks
- Index usage analysis
- Repository UML diagrams
- Async repository patterns
- Migration impact notes

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Repository Class Reference |

---

**Document End**

© Athena AI Terminal Project
