# Athena AI Terminal
# Service Class Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Service Class Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Architects, QA Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Service Layer Overview
3. Service Design Rules
4. Service Lifecycle
5. MarketService
6. RecommendationService
7. MT5Service
8. UserService
9. WatchlistService
10. Service Interactions
11. Error Handling
12. Logging
13. Performance Considerations
14. Extension Guidelines
15. Related Documents

---

# 1. Introduction

This document describes every service class within Athena.

For every service this document explains:

- Purpose
- Responsibilities
- Dependencies
- Constructor
- Public methods
- Internal methods
- Workflow
- Error handling
- Logging
- Performance
- Extension points

---

# 2. Service Layer Overview

The Service Layer contains Athena's business logic.

Architecture

```text
REST API

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

MT5

↓

AI

↓

Indicators

↓

Patterns

↓

Scheduler
```

---

# 3. Service Design Rules

Every service should:

- Own one business domain
- Coordinate repositories
- Coordinate AI
- Coordinate MT5
- Never expose SQLAlchemy
- Never implement HTTP routing
- Never contain UI logic

Services should be reusable from:

- REST API
- Scheduler
- CLI
- Tests
- Future background workers

---

# 4. Service Lifecycle

Typical request flow

```text
API Request

↓

Service

↓

Validation

↓

Repository

↓

AI

↓

Repository

↓

Response
```

Scheduler flow

```text
Scheduler

↓

MarketService

↓

RecommendationEngine

↓

Repository
```

---

# 5. MarketService

## Purpose

MarketService is the primary orchestration service responsible for processing market data and generating trading intelligence.

---

## Responsibilities

- Retrieve candles
- Store candles
- Calculate indicators
- Detect patterns
- Perform market analysis
- Generate recommendations
- Retrieve market history

---

## Dependencies

```
MarketRepository

RecommendationRepository

RecommendationEngine

Indicator Engine

Pattern Engine

Market Analyzer
```

---

## Constructor

Example

```python
MarketService(
    repository: MarketRepository
)
```

Dependencies should be injected rather than created internally.

---

## Public Methods

Typical methods

```python
collect_market_data()

get_latest()

get_history()

analyze_latest()

generate_summary()

save_market_data()
```

---

## Internal Methods

Typical private helpers

```python
_prepare_dataframe()

_validate_market_data()

_run_analysis()

_build_summary()
```

---

## Workflow

```text
Receive Candles

↓

Repository

↓

Indicators

↓

Patterns

↓

Analysis

↓

AI

↓

Recommendation Repository

↓

Return Result
```

---

## Repository Interaction

Reads

```
MarketRepository
```

Writes

```
RecommendationRepository
```

---

## Error Handling

Typical failures

- Missing candles
- MT5 unavailable
- Database unavailable
- AI timeout

Service should:

- Log
- Recover where possible
- Raise service-level exceptions

---

## Logging

Example

```
Retrieved 500 candles

Generated recommendation

Stored recommendation
```

---

## Performance

Current

- Batch inserts
- Vectorized indicators

Future

- Async execution
- Parallel analysis

---

# 6. RecommendationService

## Purpose

Manage recommendation persistence and retrieval.

---

## Responsibilities

- Store recommendations
- Retrieve latest recommendation
- Retrieve history
- Filter recommendations

---

## Dependencies

```
RecommendationRepository
```

---

## Public Methods

```python
save()

get_latest()

get_history()

delete()

filter()
```

---

## Workflow

```text
Recommendation

↓

Repository

↓

Database
```

---

## Logging

```
Recommendation Saved

Recommendation Retrieved
```

---

# 7. MT5Service

## Purpose

Broker abstraction layer.

---

## Responsibilities

- Connect
- Disconnect
- Download candles
- Retrieve account info
- Retrieve symbol info

---

## Dependencies

```
MT5Manager
```

---

## Public Methods

```python
connect()

disconnect()

get_candles()

get_symbols()

account_info()
```

---

## Error Handling

Possible failures

- Login failure
- IPC timeout
- Connection lost

Recovery

Reconnect when appropriate.

---

## Logging

```
Connected

Disconnected

Retrieved 500 candles
```

---

# 8. UserService

## Purpose

Manage users.

(Currently planned.)

---

## Responsibilities

- Create user
- Update profile
- Change password
- Retrieve profile

---

## Dependencies

```
UserRepository
```

---

## Future Methods

```python
register()

login()

update()

change_password()

delete()
```

---

# 9. WatchlistService

## Purpose

Manage user watchlists.

---

## Responsibilities

- Add symbol
- Remove symbol
- Retrieve watchlist

---

## Dependencies

```
WatchlistRepository
```

---

## Methods

```python
add_symbol()

remove_symbol()

get_watchlist()
```

---

# 10. Service Interactions

Current interactions

```text
MarketService

↓

RecommendationEngine

↓

RecommendationRepository
```

Future

```text
UserService

↓

NotificationService

↓

EmailService
```

Rules

- Avoid circular dependencies.
- Prefer dependency injection.
- Keep interactions explicit.

---

# 11. Error Handling

Services should convert infrastructure exceptions into business-level exceptions.

Example

```text
DatabaseError

↓

ServiceException

↓

API Response
```

Common service exceptions

- MarketDataUnavailable
- RecommendationFailed
- UserNotFound
- WatchlistExists
- InvalidTimeframe

---

# 12. Logging

Every service should log:

Start

```
Market analysis started.
```

Success

```
Recommendation generated.
```

Failure

```
Recommendation generation failed.
```

Include:

- Symbol
- Timeframe
- Duration
- Result

Do not log sensitive information.

---

# 13. Performance Considerations

Services should:

- Batch repository operations
- Minimize database round trips
- Reuse repositories
- Avoid repeated indicator calculations
- Cache immutable configuration

Future improvements

- Async services
- Parallel AI analysis
- Distributed workers

---

# 14. Extension Guidelines

When creating a new service

1. Create service class

↓

2. Inject repositories

↓

3. Implement business logic

↓

4. Add logging

↓

5. Add tests

↓

6. Document service

Future services

```
PortfolioService

OrderService

RiskService

StrategyService

NotificationService

AnalyticsService
```

Each service should own exactly one business capability.

---

# 15. Related Documents

Architecture

- 18_Service_Layer.md
- 17_Repository_Layer.md

Implementation

- 27_Backend_Package_Reference.md
- 29_Database_Model_Reference.md
- 31_Repository_Class_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md

Operations

- 20_Testing_Strategy.md
- 21_Logging_Observability.md

---

# Service Checklist

Before adding a new service:

- [ ] Single responsibility
- [ ] Dependency injection
- [ ] Repository abstraction respected
- [ ] Logging implemented
- [ ] Error handling added
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Documentation updated
- [ ] API integrated (if applicable)

---

# Service Dependency Matrix

| Service | Repository | AI | MT5 | Scheduler |
|----------|------------|----|-----|-----------|
| MarketService | ✅ | ✅ | ✅ | ✅ |
| RecommendationService | ✅ | ❌ | ❌ | ❌ |
| MT5Service | ❌ | ❌ | ✅ | ❌ |
| UserService | ✅ | ❌ | ❌ | ❌ |
| WatchlistService | ✅ | ❌ | ❌ | ❌ |

---

# Future Improvements

Future versions of this document should include:

- UML class diagrams
- Method signatures
- Sequence diagrams
- Thread safety notes
- Performance benchmarks
- Example code snippets
- Dependency graphs for each service
- Call hierarchy diagrams

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Service Class Reference |

---

**Document End**

© Athena AI Terminal Project
