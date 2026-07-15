# Athena AI Terminal
# Project Decision Log (Architecture Decision Records)

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Project Decision Log |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Architects, Developers, DevOps Engineers, AI Assistants |

---

# Purpose

This document records **major engineering decisions** made throughout the Athena project.

It answers:

- Why was this technology chosen?
- What alternatives were considered?
- What trade-offs were accepted?
- What consequences does the decision have?

Every significant architectural decision should be documented before implementation whenever practical.

---

# Decision Format

Each decision follows the same structure.

```
Decision ID

Title

Status

Date

Context

Decision

Alternatives

Advantages

Disadvantages

Consequences

Future Reconsideration
```

---

# ADR-001

## Title

Layered Architecture

Status

Accepted

Date

July 2026

---

### Context

Athena is expected to grow significantly over time.

The system will include:

- AI
- MT5
- REST APIs
- WebSockets
- Scheduler
- Authentication
- Portfolio Management

A maintainable architecture is required.

---

### Decision

Use a layered architecture.

```
API

↓

Service

↓

Repository

↓

Database
```

---

### Alternatives Considered

- Monolithic controllers
- Active Record
- Direct ORM access
- Repository-less architecture

---

### Advantages

- Separation of concerns
- Easier testing
- Maintainability
- Scalability

---

### Disadvantages

- More files
- Slightly more boilerplate

---

### Consequences

All new features must respect architectural layers.

---

# ADR-002

## Title

FastAPI

Status

Accepted

---

### Context

Need a modern Python web framework.

---

### Decision

Use FastAPI.

---

### Alternatives

- Flask
- Django
- Sanic
- Tornado

---

### Why FastAPI?

- Type hints
- Automatic OpenAPI
- Excellent performance
- Async support
- Pydantic integration

---

### Consequences

API schemas are defined using Pydantic.

---

# ADR-003

## Title

Repository Pattern

Status

Accepted

---

### Context

Database access should remain isolated.

---

### Decision

Repositories own persistence.

Services own business logic.

---

### Benefits

- Easier testing
- Database abstraction
- Cleaner services

---

### Consequences

Services must never execute SQL.

---

# ADR-004

## Title

SQLAlchemy ORM

Status

Accepted

---

### Decision

Use SQLAlchemy ORM.

---

### Alternatives

- Raw SQL
- Django ORM
- SQLModel
- Peewee

---

### Reasons

- Mature ecosystem
- Flexible
- Excellent PostgreSQL support

---

# ADR-005

## Title

PostgreSQL

Status

Accepted

---

### Decision

Use PostgreSQL.

---

### Alternatives

- SQLite
- MySQL
- MariaDB

---

### Reasons

- Reliability
- JSON support
- Extensions
- Performance
- Production ready

---

# ADR-006

## Title

MetaTrader 5 Integration

Status

Accepted

---

### Decision

Use official MetaTrader5 Python package.

---

### Alternatives

- FIX API
- REST Broker APIs
- cTrader

---

### Reasons

- Native support
- Stable API
- Existing broker compatibility

---

### Consequences

Requires local MT5 terminal.

---

# ADR-007

## Title

Ollama as Initial AI Provider

Status

Accepted

---

### Context

Need an AI model without recurring cloud costs.

---

### Decision

Use Ollama locally.

---

### Alternatives

- OpenAI
- Anthropic
- Gemini
- Azure OpenAI

---

### Reasons

- Offline capable
- Privacy
- No API costs
- Local inference

---

### Consequences

Provider abstraction should allow future migration.

---

# ADR-008

## Title

Provider Abstraction

Status

Accepted

---

### Decision

AI providers must be replaceable.

Current

```
Ollama
```

Future

```
OpenAI

Anthropic

Gemini

Azure
```

---

### Consequences

Business logic must not depend on provider-specific APIs.

---

# ADR-009

## Title

JSON-only AI Responses

Status

Accepted

---

### Decision

LLMs must return structured JSON.

---

### Reasons

- Easier validation
- Reliable parsing
- Stable APIs

---

### Alternatives

Free-form text

Rejected.

---

# ADR-010

## Title

Pydantic Validation

Status

Accepted

---

### Decision

Every AI response must pass Pydantic validation.

---

### Reasons

- Prevent malformed recommendations
- Type safety
- Early error detection

---

# ADR-011

## Title

Scheduler-based Market Collection

Status

Accepted

---

### Decision

Use APScheduler.

---

### Alternatives

- Celery
- Cron
- Manual execution

---

### Reasons

- Lightweight
- Simple deployment
- Fits current requirements

---

### Future

Evaluate distributed schedulers if workload increases.

---

# ADR-012

## Title

Structured Logging

Status

Accepted

---

### Decision

Every subsystem logs consistently.

Required context

- Module
- Symbol
- Timeframe
- Error
- Duration

---

### Consequences

Print statements are prohibited.

---

# ADR-013

## Title

Strong Documentation Culture

Status

Accepted

---

### Decision

Documentation evolves with implementation.

---

### Reasons

- Easier onboarding
- Better AI assistance
- Reduced knowledge loss

---

### Consequences

Every architectural change requires documentation updates.

---

# ADR-014

## Title

Dependency Injection

Status

Accepted

---

### Decision

Dependencies are injected rather than instantiated internally.

---

### Reasons

- Easier testing
- Better modularity
- Lower coupling

---

# ADR-015

## Title

One Responsibility Per Module

Status

Accepted

---

### Decision

Each module should have one clearly defined responsibility.

Examples

Repository

↓

Persistence

Service

↓

Business Logic

AI Client

↓

Provider Communication

MT5 Manager

↓

Broker Communication

---

# ADR-016

## Title

Database-first Candle Storage

Status

Accepted

---

### Decision

Persist candles before analysis.

Workflow

```
MT5

↓

Database

↓

Indicators

↓

Patterns

↓

AI
```

---

### Reasons

- Historical traceability
- Backtesting
- Repeatable analysis

---

# ADR-017

## Title

Recommendation Persistence

Status

Accepted

---

### Decision

Store every recommendation.

---

### Reasons

- Auditing
- Analytics
- Model comparison
- Backtesting

---

# ADR-018

## Title

Configuration via Environment Variables

Status

Accepted

---

### Decision

All runtime configuration comes from environment variables.

---

### Reasons

- Twelve-Factor App compatibility
- Easier deployment
- Environment isolation

---

# ADR-019

## Title

Comprehensive Documentation

Status

Accepted

---

### Decision

Athena documentation is treated as part of the source code.

---

### Consequences

Documentation changes are expected alongside implementation changes.

---

# ADR-020

## Title

AI-Assisted Development

Status

Accepted

---

### Context

Athena is developed collaboratively with AI assistants.

---

### Decision

Maintain dedicated documentation enabling future AI systems to continue development.

Primary documents

- AI Continuation Context
- Package Reference
- Service Reference
- Repository Reference
- Decision Log

---

### Consequences

AI context should not rely on previous conversations.

---

# Future Decisions

The following future decisions should be documented when implemented:

- Authentication Provider
- Trade Execution
- Portfolio Engine
- Notification System
- Multi-Broker Support
- Multi-AI Provider Strategy
- Distributed Scheduler
- Kubernetes Deployment
- Horizontal Scaling
- Event Bus
- CQRS (if adopted)
- Microservices (if adopted)

---

# Decision Checklist

Before recording a new decision:

- [ ] Problem clearly identified
- [ ] Context documented
- [ ] Alternatives considered
- [ ] Trade-offs evaluated
- [ ] Decision justified
- [ ] Consequences documented
- [ ] Related documentation updated

---

# Related Documents

### Architecture

- 02_System_Architecture.md
- 05_Backend_Architecture.md
- 08_AI_Architecture.md
- 17_Repository_Layer.md
- 18_Service_Layer.md

### Implementation

- 30_Service_Class_Reference.md
- 31_Repository_Class_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Architecture Decision Log |

---

**Document End**

© Athena AI Terminal Project
