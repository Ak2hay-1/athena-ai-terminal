# Athena AI Terminal
# Developer Onboarding Guide

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Developer Onboarding Guide |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | New Developers, Contributors, Contractors, DevOps Engineers, AI Assistants |

---

# Table of Contents

1. Welcome to Athena
2. Project Overview
3. Development Philosophy
4. Architecture at a Glance
5. Technology Stack
6. Development Environment
7. Required Software
8. Repository Structure
9. Getting the Project
10. Running Athena
11. Project Workflow
12. Coding Standards
13. Git Workflow
14. Branching Strategy
15. Debugging Guide
16. Testing
17. Common Issues
18. Pull Request Process
19. Code Review Checklist
20. Documentation Standards
21. AI-Assisted Development
22. Development Roadmap
23. First Contribution Guide
24. Helpful Commands
25. FAQ
26. Related Documents

---

# 1. Welcome to Athena

Welcome to the Athena AI Terminal project.

Athena is an AI-assisted trading intelligence platform designed to:

- Collect market data
- Analyze technical indicators
- Detect Smart Money Concepts
- Generate AI-assisted trading recommendations
- Deliver recommendations through REST APIs and WebSockets

The goal is to build a modular, scalable, and production-ready trading platform.

---

# 2. Project Overview

Athena is organized into multiple layers:

```
Frontend

↓

REST API / WebSocket

↓

Service Layer

↓

Repository Layer

↓

Database

↓

MetaTrader 5

↓

AI Engine
```

Every feature should respect this architecture.

---

# 3. Development Philosophy

Every contribution should follow these principles:

- Readability over cleverness
- Explicit is better than implicit
- Modular design
- Test before merge
- Document major changes
- Keep business logic deterministic
- Separate infrastructure from business rules

---

# 4. Architecture at a Glance

Main subsystems:

- Backend API
- AI Engine
- MT5 Integration
- Scheduler
- Indicator Engine
- Pattern Engine
- Recommendation Engine
- Repository Layer
- Database
- WebSocket Layer

Refer to:

```
docs/02_System_Architecture.md
```

---

# 5. Technology Stack

Backend

- Python 3.13
- FastAPI
- SQLAlchemy
- Pydantic
- APScheduler

Database

- PostgreSQL

Trading

- MetaTrader 5

AI

- Ollama
- Llama 3.2 (default)

Frontend (planned)

- React
- TypeScript

Deployment

- Docker
- NGINX
- GitHub Actions

---

# 6. Development Environment

Recommended IDEs:

- PyCharm Professional
- Visual Studio Code

Operating Systems:

- Windows (primary)
- Ubuntu Linux
- macOS (supported)

---

# 7. Required Software

Install before starting:

- Python 3.13
- PostgreSQL
- Git
- MetaTrader 5
- Ollama
- Docker Desktop (optional)
- Node.js (frontend work)

Verify installations:

```bash
python --version
git --version
ollama --version
docker --version
```

---

# 8. Repository Structure

```
athena-ai-terminal/

backend/

frontend/

docs/

docker/

scripts/

.env

README.md
```

Backend modules:

```
api/

services/

repositories/

models/

schemas/

mt5/

analysis/

indicators/

patterns/

scheduler/

websocket/

core/
```

---

# 9. Getting the Project

Clone the repository:

```bash
git clone <repository-url>
```

Enter the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

Windows

```powershell
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 10. Running Athena

Start PostgreSQL.

Start MetaTrader 5 and log in.

Start Ollama:

```bash
ollama serve
```

Ensure the model exists:

```bash
ollama list
```

If required:

```bash
ollama pull llama3.2
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Verify:

```
http://localhost:8000/docs
```

---

# 11. Project Workflow

Typical feature flow:

```
Issue

↓

Discussion

↓

Branch

↓

Implementation

↓

Tests

↓

Documentation

↓

Pull Request

↓

Review

↓

Merge
```

---

# 12. Coding Standards

Follow:

- PEP 8
- Type hints
- Docstrings
- Small functions
- Clear variable names

Avoid:

- Hardcoded values
- Global mutable state
- Duplicate logic
- Large functions

---

# 13. Git Workflow

Always begin with the latest main branch:

```bash
git checkout main
git pull
```

Create a feature branch:

```bash
git checkout -b feature/short-description
```

Commit frequently with meaningful messages.

---

# 14. Branching Strategy

Examples:

```
feature/add-watchlist

feature/new-indicator

bugfix/mt5-timeout

bugfix/recommendation-parser

docs/security-guide

refactor/market-service
```

Never commit directly to the main branch.

---

# 15. Debugging Guide

Useful tools:

- FastAPI `/docs`
- PyCharm Debugger
- VS Code Debugger
- PostgreSQL client
- MT5 logs
- Application logs

When debugging:

1. Read the logs.
2. Reproduce the issue.
3. Isolate the failing component.
4. Write a regression test if applicable.
5. Verify the fix.

---

# 16. Testing

Run tests before committing:

```bash
pytest
```

Run coverage:

```bash
pytest --cov=app
```

All tests should pass before creating a pull request.

---

# 17. Common Issues

## MT5 Authorization Failed

Check:

- Login
- Password
- Server
- Terminal status

---

## Ollama Model Missing

```bash
ollama list
```

If absent:

```bash
ollama pull llama3.2
```

---

## Database Connection Failed

Verify:

- PostgreSQL service
- Environment variables
- Connection string

---

## Scheduler Not Running

Check:

- Startup logs
- APScheduler configuration
- Job registration

---

# 18. Pull Request Process

Before opening a PR:

- Rebase if necessary.
- Run all tests.
- Update documentation.
- Review your own changes.
- Remove debug code.
- Ensure formatting is consistent.

PR description should include:

- Summary
- Motivation
- Testing performed
- Breaking changes (if any)

---

# 19. Code Review Checklist

Reviewers should verify:

- Architecture compliance
- Readability
- Correctness
- Error handling
- Logging
- Tests
- Documentation
- Performance impact
- Security implications

---

# 20. Documentation Standards

Document:

- New modules
- Public APIs
- Configuration changes
- Database changes
- New environment variables
- New workflows

Keep documentation synchronized with implementation.

---

# 21. AI-Assisted Development

Athena encourages AI-assisted development, but all generated code must be reviewed.

When using an AI assistant:

- Provide relevant architecture documents.
- Request complete, production-ready code.
- Verify generated code manually.
- Add tests.
- Update documentation.

Never merge AI-generated code without human review.

---

# 22. Development Roadmap

Current priorities:

- Stabilize backend
- Expand recommendation engine
- Frontend dashboard
- Multi-symbol support
- Multi-timeframe analysis
- Authentication
- Auto-trading integration
- Monitoring
- Cloud deployment

See:

```
docs/25_Project_Roadmap.md
```

---

# 23. First Contribution Guide

Suggested first tasks:

- Fix a bug.
- Improve documentation.
- Add a unit test.
- Optimize a query.
- Refactor a service.
- Improve logging.

Recommended workflow:

1. Read the related documentation.
2. Understand the existing code.
3. Discuss major design changes.
4. Implement the change.
5. Write tests.
6. Update documentation.
7. Open a pull request.

---

# 24. Helpful Commands

Start backend:

```bash
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

Run coverage:

```bash
pytest --cov=app
```

View installed AI models:

```bash
ollama list
```

Pull AI model:

```bash
ollama pull llama3.2
```

Check Git status:

```bash
git status
```

---

# 25. FAQ

### Where should business logic live?

Service Layer.

---

### Where should database queries live?

Repository Layer.

---

### Where should indicator calculations live?

Indicator Engine.

---

### Where should AI prompts be built?

Prompt Builder.

---

### Where should API validation happen?

Pydantic Schemas.

---

### Where should recommendation rules live?

Recommendation Engine.

---

### Can I call SQLAlchemy directly from an API route?

No.

Use the Service Layer.

---

# 26. Related Documents

- 02_System_Architecture.md
- 05_Backend_Architecture.md
- 08_AI_Architecture.md
- 12_Recommendation_Engine.md
- 17_Repository_Layer.md
- 18_Service_Layer.md
- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md
- 22_Security_Guide.md
- 24_Coding_Standards.md
- 99_AI_Continuation_Context.md

---

# New Developer Checklist

Before making your first contribution:

- [ ] Development environment configured
- [ ] Backend starts successfully
- [ ] PostgreSQL connected
- [ ] MetaTrader 5 connected
- [ ] Ollama running with required model
- [ ] Tests pass
- [ ] Documentation reviewed
- [ ] Git workflow understood
- [ ] Coding standards reviewed
- [ ] First issue selected

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial developer onboarding guide |

---

**Document End**

© Athena AI Terminal Project
