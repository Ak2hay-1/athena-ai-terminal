# Athena AI Terminal
# Configuration Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Configuration Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, DevOps Engineers, Architects, AI Assistants |

---

# Table of Contents

1. Introduction
2. Configuration Philosophy
3. Configuration Architecture
4. Configuration Loading Order
5. Configuration Sources
6. settings.py
7. Configuration Categories
8. Database Configuration
9. MT5 Configuration
10. AI Configuration
11. Scheduler Configuration
12. Logging Configuration
13. Security Configuration
14. Feature Flags
15. Runtime Configuration
16. Environment Profiles
17. Validation Rules
18. Best Practices
19. Troubleshooting
20. Related Documents

---

# 1. Introduction

Athena is entirely configuration driven.

The application should behave differently across:

- Development
- Testing
- Staging
- Production

without requiring source code changes.

Every configurable value must originate from configuration rather than being hardcoded.

---

# 2. Configuration Philosophy

Configuration should be:

- Explicit
- Version controlled (except secrets)
- Environment specific
- Strongly validated
- Typed
- Immutable after startup (unless explicitly designed otherwise)

Configuration must never contain business logic.

---

# 3. Configuration Architecture

```
Environment Variables

↓

.env

↓

Pydantic Settings

↓

Application Startup

↓

Dependency Injection

↓

Application Components
```

Every subsystem reads configuration through the central settings object.

---

# 4. Configuration Loading Order

Athena resolves configuration in the following order:

```
Default Values

↓

.env File

↓

System Environment Variables

↓

Runtime Overrides (Future)

↓

Validated Settings Object
```

Later sources override earlier ones.

---

# 5. Configuration Sources

Primary sources

```
.env

Operating System Environment

Docker Compose

Kubernetes Secrets (Future)

CI/CD Variables
```

Configuration should never be hardcoded inside application code.

---

# 6. settings.py

## Purpose

Provides a single strongly typed configuration object for the application.

---

## Responsibilities

- Load environment variables
- Apply defaults
- Validate configuration
- Expose settings through dependency injection

---

## Typical Structure

```python
class Settings(BaseSettings):
    database_url: str
    ollama_url: str
    mt5_login: int
```

All configuration should be represented by typed fields.

---

# 7. Configuration Categories

Athena configuration is grouped into:

- Application
- Database
- MT5
- AI
- Scheduler
- Logging
- Security
- API
- Feature Flags

Each category should remain logically independent.

---

# 8. Database Configuration

Purpose

Configure PostgreSQL connectivity.

Typical settings

```
DATABASE_URL

DATABASE_POOL_SIZE

DATABASE_MAX_OVERFLOW

DATABASE_POOL_TIMEOUT

DATABASE_ECHO
```

Used by

- SQLAlchemy
- Repository Layer

Validation

- Valid connection string
- Positive pool sizes
- Reasonable timeout values

---

# 9. MT5 Configuration

Purpose

Configure MetaTrader 5 integration.

Typical settings

```
MT5_LOGIN

MT5_PASSWORD

MT5_SERVER

MT5_PATH

MT5_TIMEOUT

MT5_RECONNECT_DELAY
```

Used by

- MT5 Manager
- Candle Collector

Validation

- Login present
- Password present
- Server configured
- Terminal path exists (where applicable)

---

# 10. AI Configuration

Purpose

Configure AI provider communication.

Typical settings

```
OLLAMA_URL

OLLAMA_MODEL

AI_TIMEOUT

AI_RETRIES

AI_TEMPERATURE

AI_MAX_TOKENS
```

Used by

- AI Client
- Recommendation Engine

Validation

- Valid URL
- Positive timeout
- Existing model name
- Retry count ≥ 0

---

# 11. Scheduler Configuration

Purpose

Control background jobs.

Typical settings

```
SCHEDULER_ENABLED

COLLECTION_INTERVAL

ANALYSIS_INTERVAL

MAX_JOB_INSTANCES

MISFIRE_GRACE_TIME
```

Used by

- Market Scheduler

Validation

- Positive intervals
- Positive retry limits

---

# 12. Logging Configuration

Purpose

Configure application logging.

Typical settings

```
LOG_LEVEL

LOG_FORMAT

LOG_FILE

LOG_ROTATION

LOG_RETENTION
```

Supported levels

```
DEBUG

INFO

WARNING

ERROR

CRITICAL
```

Logging should be configurable without code changes.

---

# 13. Security Configuration

Purpose

Configure authentication and security behavior.

Typical settings

```
SECRET_KEY

JWT_SECRET

JWT_ALGORITHM

JWT_EXPIRATION

PASSWORD_HASH_ROUNDS

CORS_ORIGINS
```

Secrets must never be committed to source control.

---

# 14. Feature Flags

Feature flags enable controlled rollout of functionality.

Examples

```
ENABLE_AI

ENABLE_MT5

ENABLE_SCHEDULER

ENABLE_WEBSOCKET

ENABLE_BACKTESTING
```

Benefits

- Safe deployments
- Incremental releases
- Easier testing
- Temporary feature disabling

---

# 15. Runtime Configuration

Current configuration is loaded during startup.

Future enhancements may include:

- Dynamic feature flag updates
- Configuration reload
- Remote configuration service
- Administrative configuration API

Runtime changes should be limited to settings designed for hot reload.

---

# 16. Environment Profiles

Development

Purpose

Local development.

Characteristics

- Verbose logging
- Debug enabled
- Local database
- Local Ollama

---

Testing

Purpose

Automated testing.

Characteristics

- In-memory or isolated database
- Mock MT5
- Mock AI providers
- Deterministic configuration

---

Staging

Purpose

Pre-production validation.

Characteristics

- Production-like infrastructure
- Real integrations
- Reduced traffic

---

Production

Purpose

Live environment.

Characteristics

- Secure secrets
- Optimized logging
- Monitoring enabled
- High availability

---

# 17. Validation Rules

Every configuration value should be validated during startup.

Examples

Database URL

- Must be a valid connection string

Timeouts

- Must be positive integers

URLs

- Must include protocol

Feature Flags

- Boolean values only

Validation failures should prevent application startup.

---

# 18. Best Practices

- Keep secrets out of version control.
- Prefer environment variables over constants.
- Use typed configuration objects.
- Validate everything at startup.
- Document every new setting.
- Remove obsolete configuration promptly.
- Keep defaults safe for development.

---

# 19. Troubleshooting

Common issues

Database connection failed

Possible causes

- Incorrect DATABASE_URL
- Database unavailable
- Firewall restrictions

---

MT5 initialization failed

Possible causes

- Invalid credentials
- Terminal not running
- Incorrect terminal path

---

AI unavailable

Possible causes

- Ollama not running
- Incorrect model name
- Invalid OLLAMA_URL

---

Scheduler not running

Possible causes

- Scheduler disabled
- Invalid interval
- Startup exception

---

Logging missing

Possible causes

- Invalid log level
- Missing log directory
- Permission issues

---

# 20. Related Documents

Architecture

- 05_Backend_Architecture.md
- 07_MT5_Integration.md
- 08_AI_Architecture.md

Implementation

- 26_Codebase_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md
- 35_Environment_Variables_Reference.md

Operations

- 19_Deployment_Guide.md
- 21_Logging_Observability.md
- 22_Security_Guide.md

---

# Configuration Checklist

Before introducing a new configuration option:

- [ ] Added to settings.py
- [ ] Type annotated
- [ ] Default value evaluated
- [ ] Validation implemented
- [ ] Environment variable documented
- [ ] Deployment guide updated
- [ ] Tests updated
- [ ] Documentation updated

---

# Configuration Dependency Matrix

| Category | Primary Consumer |
|-----------|------------------|
| Application | Startup |
| Database | SQLAlchemy |
| MT5 | MT5 Manager |
| AI | AI Client |
| Scheduler | APScheduler |
| Logging | Logger |
| Security | Authentication |
| API | FastAPI |
| Feature Flags | Services |

---

# Future Improvements

Future versions of this document should include:

- Complete `settings.py` field reference
- Configuration UML diagrams
- Environment variable precedence diagrams
- Kubernetes ConfigMap examples
- Docker Compose examples
- Helm chart mappings
- Configuration migration strategy
- Runtime configuration API specification

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Configuration Reference |

---

**Document End**

© Athena AI Terminal Project
