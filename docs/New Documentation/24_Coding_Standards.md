# Athena AI Terminal
# Coding Standards

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Coding Standards |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Frontend Developers, AI Engineers, QA Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Engineering Principles
3. General Coding Standards
4. Python Standards
5. Project Architecture Rules
6. Naming Conventions
7. File Organization
8. Class Design
9. Function Design
10. Type Hints
11. Docstrings
12. Error Handling
13. Logging Standards
14. Configuration Standards
15. Database Standards
16. API Standards
17. AI Development Standards
18. Testing Standards
19. Git Standards
20. Code Review Standards
21. Performance Guidelines
22. Security Guidelines
23. Documentation Standards
24. Best Practices
25. Related Documents

---

# 1. Introduction

This document defines the coding standards used throughout the Athena AI Terminal project.

Every contribution—whether written by a human developer or generated with AI—must follow these standards.

Objectives:

- Consistency
- Readability
- Maintainability
- Testability
- Scalability
- Security

---

# 2. Engineering Principles

Athena follows these engineering principles:

- Readability over cleverness
- Explicit over implicit
- Simplicity over complexity
- Composition over inheritance
- Business logic over framework logic
- Small, focused modules
- Predictable behaviour
- Fail safely

---

# 3. General Coding Standards

Always:

- Write readable code
- Keep functions focused
- Avoid duplication (DRY)
- Use descriptive names
- Remove dead code
- Keep imports organized
- Prefer composition over global state

Never:

- Commit commented-out code
- Leave debug print statements
- Hardcode secrets
- Ignore exceptions silently
- Mix unrelated responsibilities

---

# 4. Python Standards

Athena follows:

- PEP 8
- PEP 257 (Docstrings)
- PEP 484 (Type Hints)

Formatting:

- 4-space indentation
- UTF-8 encoding
- One statement per line
- Maximum line length: 100 characters

Recommended tools:

- Black
- Ruff
- isort
- mypy

---

# 5. Project Architecture Rules

The following dependencies are allowed:

```text
API

↓

Service

↓

Repository

↓

Database
```

Services may call:

- AI
- MT5
- Repositories

Repositories may only access:

- SQLAlchemy
- Database

API routes must never access the database directly.

---

# 6. Naming Conventions

## Files

```text
market_service.py

recommendation_engine.py

mt5_manager.py
```

Use:

- lowercase
- snake_case

---

## Classes

```python
MarketService

RecommendationEngine

MT5Manager
```

Use:

- PascalCase

---

## Functions

```python
get_latest_candles()

generate_summary()

save_recommendation()
```

Use:

- snake_case
- Verb-based names

---

## Variables

```python
market_summary

current_price

risk_reward
```

Avoid:

```python
x

data1

temp2
```

---

## Constants

```python
MAX_RETRIES

DEFAULT_TIMEFRAME

API_TIMEOUT
```

Use uppercase with underscores.

---

# 7. File Organization

Preferred structure:

```python
Imports

Constants

Classes

Private Functions

Public Functions
```

Avoid multiple unrelated classes in a single file.

---

# 8. Class Design

Classes should:

- Have one responsibility
- Be cohesive
- Hide implementation details
- Expose a clear public interface

Avoid "God classes" that manage unrelated concerns.

---

# 9. Function Design

Guidelines:

- One responsibility
- Short where practical (target <50 lines)
- Descriptive name
- Explicit parameters
- Minimal side effects

Prefer returning values over mutating global state.

---

# 10. Type Hints

Every public function should use type hints.

Example:

```python
def get_latest(
    symbol: str,
    timeframe: str,
) -> list[MarketCandle]:
    ...
```

Avoid using `Any` unless no better type exists.

---

# 11. Docstrings

Public modules, classes, and functions should include docstrings.

Example:

```python
def calculate_rsi(df: DataFrame) -> DataFrame:
    """
    Calculate the Relative Strength Index (RSI).

    Args:
        df: Market data DataFrame.

    Returns:
        DataFrame with RSI values.
    """
```

Docstrings should describe intent, not restate the code.

---

# 12. Error Handling

Always:

- Catch expected exceptions
- Log meaningful context
- Raise domain-specific exceptions where appropriate

Never:

```python
except:
    pass
```

Prefer:

```python
except DatabaseError as exc:
    logger.exception("Failed to save recommendation.")
    raise
```

---

# 13. Logging Standards

Use the project logger.

Example:

```python
logger.info(
    "Stored recommendation for %s (%s)",
    symbol,
    timeframe,
)
```

Log:

- Major events
- Errors
- Warnings
- Execution time (where useful)

Do not log:

- Passwords
- Secrets
- Tokens
- Sensitive user information

---

# 14. Configuration Standards

Configuration must come from:

- Environment variables
- Settings classes

Never hardcode:

- Credentials
- API URLs
- Ports
- Timeouts

Bad:

```python
url = "http://localhost:11434"
```

Good:

```python
url = settings.ollama_url
```

---

# 15. Database Standards

Repositories own persistence.

Guidelines:

- Use transactions
- Prefer bulk operations
- Avoid N+1 queries
- Keep transactions short
- Use indexes appropriately

Services should never execute SQL.

---

# 16. API Standards

Use:

- Pydantic request models
- Pydantic response models
- Consistent HTTP status codes
- Resource-oriented routes

Avoid exposing internal exceptions or ORM models directly.

---

# 17. AI Development Standards

AI-generated output must:

- Be validated
- Conform to schemas
- Never bypass business rules
- Use deterministic prompts where possible

Prompt templates should be version controlled.

Never trust raw LLM output without validation.

---

# 18. Testing Standards

Every new feature should include:

- Unit tests
- Integration tests (when applicable)
- Regression tests for bug fixes

Recommended coverage:

| Layer | Target |
|--------|--------:|
| Utilities | 100% |
| Indicators | 95% |
| Services | 90% |
| Repositories | 90% |
| API | 85% |

---

# 19. Git Standards

Branch naming:

```text
feature/new-indicator

bugfix/mt5-timeout

docs/security-guide

refactor/repository-layer
```

Commit message format:

```text
feat: add recommendation confidence scoring

fix: prevent duplicate candle insertion

docs: update deployment guide

refactor: simplify market service
```

Follow Conventional Commits where practical.

---

# 20. Code Review Standards

Reviewers should evaluate:

- Correctness
- Architecture compliance
- Readability
- Error handling
- Logging
- Tests
- Documentation
- Security
- Performance

Every pull request should be reviewed by at least one other contributor before merging.

---

# 21. Performance Guidelines

Prefer:

- Vectorized operations
- Batch database writes
- Lazy loading where appropriate
- Caching for expensive computations

Avoid:

- Repeated database queries
- Unnecessary object creation
- Blocking operations in request handlers
- Premature optimization

Measure before optimizing.

---

# 22. Security Guidelines

- Never commit secrets.
- Validate all inputs.
- Escape outputs where applicable.
- Use parameterized queries.
- Store passwords securely.
- Use HTTPS/WSS in production.
- Keep dependencies up to date.

Review security implications during every code review.

---

# 23. Documentation Standards

Documentation is required for:

- Public APIs
- Configuration changes
- Database schema changes
- New services
- New repositories
- New environment variables
- Architectural decisions

Update documentation in the same pull request as the code change whenever possible.

---

# 24. Best Practices

- Keep code simple.
- Keep modules focused.
- Prefer readability over cleverness.
- Write tests alongside features.
- Document important decisions.
- Refactor when complexity grows.
- Avoid duplicated business logic.
- Keep AI prompts version controlled.
- Treat warnings as opportunities to improve.

---

# 25. Related Documents

- 05_Backend_Architecture.md
- 08_AI_Architecture.md
- 17_Repository_Layer.md
- 18_Service_Layer.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md
- 22_Security_Guide.md
- 23_Developer_Onboarding.md
- 99_AI_Continuation_Context.md

---

# Coding Checklist

Before committing code:

- [ ] Code follows PEP 8
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] No hardcoded secrets
- [ ] Logging added where appropriate
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No debug code remains
- [ ] Pull request reviewed

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial coding standards document |

---

**Document End**

© Athena AI Terminal Project
