# Athena AI Terminal
# AI Continuation Context

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | AI Continuation Context |
| Version | 1.0 |
| Status | Critical |
| Last Updated | July 2026 |
| Audience | AI Assistants, Backend Developers, Architects |

---

# IMPORTANT

If you are an AI assistant reading this document, read this file completely before making **any** code changes.

This document contains the project's engineering philosophy, architecture, implementation status, coding conventions, development rules, and continuation instructions.

Treat this document as the authoritative onboarding guide.

---

# Table of Contents

1. Project Overview
2. Mission
3. Product Vision
4. System Architecture
5. Technology Stack
6. Repository Structure
7. Core Design Principles
8. Development Philosophy
9. Current Implementation Status
10. Major Components
11. Data Flow
12. AI Workflow
13. MT5 Workflow
14. Scheduler Workflow
15. Database Workflow
16. Coding Rules
17. Modification Rules
18. Testing Expectations
19. Documentation Rules
20. Known Technical Debt
21. Common Pitfalls
22. Future Roadmap
23. AI Working Guidelines
24. Context Recovery Checklist
25. Session Continuation Prompt

---

# 1. Project Overview

Athena AI Terminal is an AI-powered market analysis platform built around MetaTrader 5.

The system:

- Collects live market data
- Stores historical candles
- Calculates indicators
- Detects Smart Money Concepts (SMC) patterns
- Performs market analysis
- Uses an LLM to generate structured trading recommendations
- Exposes results through REST APIs and WebSockets

Athena is **not** a simple chatbot.

It is a modular backend platform with AI as one subsystem.

---

# 2. Mission

Build a professional, production-ready trading intelligence platform that is:

- Modular
- Testable
- Extensible
- AI-assisted
- Well documented
- Enterprise grade

---

# 3. Product Vision

Long-term capabilities include:

- Multi-symbol analysis
- Multi-timeframe analysis
- AI-generated trade ideas
- Portfolio management
- Automated backtesting
- Strategy builder
- Risk management
- Multi-user authentication
- Notifications
- Mobile clients
- Web dashboard
- Multi-broker support
- Optional trade execution

---

# 4. System Architecture

```text
FastAPI

↓

REST API

↓

Service Layer

↓

Repository Layer

↓

PostgreSQL

↑

Indicator Engine

↓

Pattern Engine

↓

Market Analysis

↓

Recommendation Engine

↓

AI Provider

↓

Response Parser

↓

Recommendation Repository

↓

REST API / WebSocket
```

The architecture is intentionally layered.

Never bypass layers without a compelling architectural reason.

---

# 5. Technology Stack

Backend

- Python 3.13+
- FastAPI
- SQLAlchemy
- Pydantic v2
- APScheduler
- Uvicorn

Database

- PostgreSQL

AI

- Ollama (current)
- Provider abstraction planned

Trading

- MetaTrader 5 Python API

Testing

- Pytest

---

# 6. Repository Structure

```
backend/

app/

api/

ai/

analysis/

core/

database/

indicators/

models/

mt5/

patterns/

repositories/

scheduler/

schemas/

services/

websocket/
```

Documentation

```
docs/
```

---

# 7. Core Design Principles

Always preserve:

- Separation of concerns
- Dependency injection
- Repository pattern
- Service layer abstraction
- Typed models
- Validation
- Structured logging
- Testability

Avoid shortcuts that increase coupling.

---

# 8. Development Philosophy

Before implementing a feature:

1. Understand the requirement.
2. Review related documentation.
3. Preserve architecture.
4. Prefer extending existing components.
5. Avoid duplicate logic.
6. Keep changes cohesive.
7. Update documentation.

---

# 9. Current Implementation Status

Implemented:

- Project structure
- Configuration
- Database layer
- ORM models
- Repository layer
- Service layer
- MT5 integration
- Candle collection
- Scheduler
- Indicator engine
- Pattern engine
- Market analysis
- AI integration
- Recommendation engine
- REST API
- WebSocket infrastructure

Planned:

- Authentication
- Portfolio
- Orders
- Strategy engine
- Notifications
- Multi-provider AI
- Multi-broker support

---

# 10. Major Components

Key subsystems

```
MT5

↓

Candle Collector

↓

Repository

↓

Indicators

↓

Patterns

↓

Market Analysis

↓

Recommendation Engine

↓

AI

↓

Response Parser

↓

Database

↓

REST API

↓

WebSocket
```

---

# 11. Data Flow

```text
MT5

↓

Candles

↓

Database

↓

Indicators

↓

Patterns

↓

Analysis

↓

AI

↓

Recommendation

↓

Database

↓

Client
```

---

# 12. AI Workflow

```
Analysis

↓

Prompt Builder

↓

AI Client

↓

Provider

↓

JSON Response

↓

Response Parser

↓

Validation

↓

Recommendation
```

The AI must return structured JSON.

Never depend on free-form text.

---

# 13. MT5 Workflow

```
Scheduler

↓

Candle Collector

↓

MT5 Manager

↓

MetaTrader 5

↓

Broker

↓

Database
```

The MT5 manager is the only component that communicates with the MetaTrader5 library.

---

# 14. Scheduler Workflow

```
Scheduler

↓

Collect Market Data

↓

Store Candles

↓

Run Analysis

↓

Generate Recommendation

↓

Persist Results

↓

Notify Clients
```

Scheduler jobs should be idempotent whenever possible.

---

# 15. Database Workflow

```
Repository

↓

SQLAlchemy

↓

PostgreSQL
```

Repositories own persistence.

Services own business logic.

---

# 16. Coding Rules

Always:

- Use type hints.
- Use descriptive names.
- Keep methods focused.
- Add docstrings.
- Log important events.
- Validate external input.
- Keep functions reasonably small.

Never:

- Put business logic in repositories.
- Access SQLAlchemy models directly from APIs.
- Duplicate code.
- Hardcode secrets.
- Ignore exceptions silently.

---

# 17. Modification Rules

Before changing code:

- Understand the call chain.
- Check dependent modules.
- Maintain backward compatibility where practical.
- Update tests.
- Update documentation.
- Preserve public interfaces unless intentionally versioned.

Large refactors should be incremental.

---

# 18. Testing Expectations

Every meaningful change should include:

- Unit tests
- Integration tests (where appropriate)
- Regression verification

Critical paths:

- Candle collection
- AI recommendation generation
- Repository operations
- Scheduler jobs
- REST endpoints

---

# 19. Documentation Rules

Documentation is part of the codebase.

Whenever architecture or behavior changes:

- Update the relevant reference document.
- Update diagrams if needed.
- Update examples.
- Record breaking changes.

Documentation should remain synchronized with implementation.

---

# 20. Known Technical Debt

Typical areas to monitor:

- AI provider abstraction (currently Ollama-focused)
- Scheduler scalability
- Multi-symbol scheduling
- Authentication (planned)
- Async optimization
- WebSocket scaling
- Repository query optimization

Technical debt should be documented rather than hidden.

---

# 21. Common Pitfalls

Avoid:

- Bypassing services
- Mixing persistence with business logic
- Returning ORM models directly from APIs
- Changing AI response schema without updating parser
- Adding MT5 calls outside the manager
- Introducing circular dependencies

---

# 22. Future Roadmap

Major milestones:

1. Stabilize current backend
2. Complete authentication
3. Improve AI reliability
4. Multi-symbol support
5. Multi-timeframe scheduling
6. Portfolio management
7. Strategy engine
8. Notifications
9. Web frontend
10. Mobile applications
11. Multi-provider AI
12. Trade execution (optional)

---

# 23. AI Working Guidelines

If you are modifying Athena:

1. Read relevant documentation before coding.
2. Prefer existing abstractions.
3. Preserve architecture.
4. Write maintainable code.
5. Explain trade-offs.
6. Do not invent missing modules.
7. Ask for clarification if requirements conflict.

When generating code:

- Produce complete files when requested.
- Keep imports organized.
- Preserve formatting conventions.
- Avoid unnecessary rewrites.

When reviewing code:

- Focus on correctness first.
- Then architecture.
- Then performance.
- Then style.

---

# 24. Context Recovery Checklist

Before starting work, verify:

- [ ] Read this document.
- [ ] Read the relevant architecture document(s).
- [ ] Read the relevant implementation reference(s).
- [ ] Understand current project status.
- [ ] Identify affected modules.
- [ ] Preserve architectural boundaries.
- [ ] Update documentation after implementation.

---

# 25. Session Continuation Prompt

If you are a new AI assistant taking over this project, use the following prompt before making changes:

```
You are continuing development of the Athena AI Terminal project.

Read the AI Continuation Context first.

Treat the existing architecture as intentional unless there is a compelling engineering reason to change it.

Respect the layered architecture:
API → Service → Repository → Database.

Use dependency injection.

Avoid introducing duplicate logic.

Maintain compatibility with existing modules whenever practical.

When modifying code:
- Produce complete updated files if requested.
- Preserve logging.
- Preserve type hints.
- Preserve documentation.
- Keep implementations modular.
- Update relevant documentation if behavior changes.

If information appears incomplete, state your assumptions clearly instead of inventing behavior.

Prioritize correctness, maintainability, and architectural consistency over minimal code changes.
```

---

# Related Documents

Read these alongside this document when working on Athena:

### Architecture

- 01_Project_Overview.md
- 02_System_Architecture.md
- 05_Backend_Architecture.md
- 08_AI_Architecture.md
- 17_Repository_Layer.md
- 18_Service_Layer.md

### Implementation

- 26_Codebase_Reference.md
- 27_Backend_Package_Reference.md
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
| 1.0 | July 2026 | Initial AI Continuation Context |

---

**Document End**

© Athena AI Terminal Project
