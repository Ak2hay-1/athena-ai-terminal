# Athena AI Terminal
# Error Code Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Error Code Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Developers, DevOps Engineers, QA Engineers, Support Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Error Handling Philosophy
3. Error Code Format
4. Error Categories
5. General Application Errors
6. Database Errors
7. MT5 Errors
8. AI Errors
9. Validation Errors
10. Scheduler Errors
11. REST API Errors
12. Authentication Errors
13. Repository Errors
14. Service Errors
15. WebSocket Errors
16. Logging Requirements
17. Troubleshooting Guide
18. Error Recovery Strategy
19. Best Practices
20. Related Documents

---

# 1. Introduction

This document defines every standardized application error used by Athena.

Goals:

- Consistent error reporting
- Easier debugging
- Better monitoring
- Stable API responses
- Faster incident resolution

Every error should have:

- Error Code
- Category
- Description
- Root Cause
- Recovery Action
- Logging Level

---

# 2. Error Handling Philosophy

Athena follows these principles:

- Fail fast during startup
- Fail safely during runtime
- Log useful context
- Never expose internal implementation details to API clients
- Recover automatically whenever possible

Errors should be deterministic and predictable.

---

# 3. Error Code Format

Format

```
CATEGORY-NUMBER
```

Examples

```
APP-001

DB-005

MT5-003

AI-002

API-004
```

Category prefixes

| Prefix | Description |
|---------|-------------|
| APP | Application |
| DB | Database |
| MT5 | MetaTrader 5 |
| AI | Artificial Intelligence |
| VAL | Validation |
| API | REST API |
| AUTH | Authentication |
| REP | Repository |
| SRV | Service |
| WS | WebSocket |
| SCH | Scheduler |

---

# 4. Error Categories

Athena classifies errors into:

- Application
- Database
- MT5
- AI
- Validation
- Scheduler
- API
- Authentication
- Repository
- Service
- WebSocket

Each category is documented separately.

---

# 5. General Application Errors

| Code | Description | Typical Cause | Recovery |
|------|-------------|---------------|----------|
| APP-001 | Application startup failed | Invalid configuration | Fix configuration and restart |
| APP-002 | Invalid runtime configuration | Missing environment variable | Correct configuration |
| APP-003 | Unexpected internal error | Unhandled exception | Investigate logs |
| APP-004 | Feature disabled | Feature flag disabled | Enable feature or use alternative |
| APP-005 | Unsupported operation | Feature not implemented | Return HTTP 501 or equivalent |

Recommended logging level

```
ERROR
```

---

# 6. Database Errors

| Code | Description | Cause | Recovery |
|------|-------------|-------|----------|
| DB-001 | Database unavailable | Server offline | Retry connection |
| DB-002 | Connection timeout | Network/database latency | Retry |
| DB-003 | Integrity constraint violation | Duplicate/invalid data | Correct input |
| DB-004 | Transaction failed | Rollback required | Retry if safe |
| DB-005 | Migration mismatch | Schema out of date | Run migrations |
| DB-006 | Record not found | Missing entity | Return 404 if applicable |
| DB-007 | Duplicate record | Unique constraint violated | Prevent duplicate insert |

Typical exception mapping

```
IntegrityError

↓

DB-003
```

---

# 7. MT5 Errors

| Code | Description | Cause | Recovery |
|------|-------------|-------|----------|
| MT5-001 | Initialization failed | Terminal unavailable | Restart MT5 |
| MT5-002 | Authorization failed | Invalid credentials | Verify login |
| MT5-003 | IPC timeout | Terminal not responding | Retry/reconnect |
| MT5-004 | Connection lost | Broker disconnected | Reconnect |
| MT5-005 | Invalid symbol | Unknown symbol | Validate symbol |
| MT5-006 | Historical data unavailable | No history | Retry later |
| MT5-007 | Terminal not running | Terminal closed | Start terminal |
| MT5-008 | Symbol not selected | Symbol hidden in Market Watch | Select symbol before use |

Logging

```
ERROR

WARNING (recoverable)
```

---

# 8. AI Errors

| Code | Description | Cause | Recovery |
|------|-------------|-------|----------|
| AI-001 | Provider unavailable | Ollama stopped | Retry |
| AI-002 | Request timeout | Slow model | Retry |
| AI-003 | Invalid model | Model not installed | Install model |
| AI-004 | Malformed JSON | LLM formatting error | Fallback parser |
| AI-005 | Validation failed | Invalid schema | Generate fallback recommendation |
| AI-006 | Empty response | Provider issue | Retry |
| AI-007 | Unsupported response | Unexpected payload | Update parser |
| AI-008 | Prompt generation failed | Invalid analysis input | Log and abort recommendation |

Current examples

```
404 /api/generate

↓

AI-003
```

```
signal="WAIT"

↓

AI-005
```

---

# 9. Validation Errors

| Code | Description | Recovery |
|------|-------------|----------|
| VAL-001 | Required field missing | Correct request |
| VAL-002 | Invalid enum value | Use supported value |
| VAL-003 | Invalid number | Provide numeric value |
| VAL-004 | Invalid date | Use ISO-8601 |
| VAL-005 | Invalid timeframe | Use supported timeframe |
| VAL-006 | Invalid symbol | Verify trading symbol |

Example

```
WAIT

↓

VAL-002
```

---

# 10. Scheduler Errors

| Code | Description | Recovery |
|------|-------------|----------|
| SCH-001 | Scheduler startup failed | Verify configuration |
| SCH-002 | Job execution failed | Retry next cycle |
| SCH-003 | Maximum instances reached | Increase limit or reduce execution time |
| SCH-004 | Misfire occurred | Review scheduler timing |
| SCH-005 | Job registration failed | Verify scheduler initialization |

Example

```
Maximum running instances reached

↓

SCH-003
```

---

# 11. REST API Errors

| Code | HTTP | Description |
|------|------|-------------|
| API-001 | 400 | Invalid request |
| API-002 | 401 | Unauthorized |
| API-003 | 403 | Forbidden |
| API-004 | 404 | Resource not found |
| API-005 | 405 | Method not allowed |
| API-006 | 409 | Conflict |
| API-007 | 422 | Validation failed |
| API-008 | 429 | Rate limit exceeded |
| API-009 | 500 | Internal server error |
| API-010 | 503 | Service unavailable |

---

# 12. Authentication Errors

(Future implementation)

| Code | Description |
|------|-------------|
| AUTH-001 | Invalid credentials |
| AUTH-002 | Expired token |
| AUTH-003 | Invalid token |
| AUTH-004 | Missing token |
| AUTH-005 | Permission denied |

---

# 13. Repository Errors

| Code | Description |
|------|-------------|
| REP-001 | Query failed |
| REP-002 | Batch insert failed |
| REP-003 | Duplicate detection failed |
| REP-004 | Repository unavailable |

Repositories should translate ORM exceptions into repository-specific errors.

---

# 14. Service Errors

| Code | Description |
|------|-------------|
| SRV-001 | Market analysis failed |
| SRV-002 | Recommendation generation failed |
| SRV-003 | Recommendation persistence failed |
| SRV-004 | Market data unavailable |
| SRV-005 | Business rule violation |

Services should not expose database-specific errors.

---

# 15. WebSocket Errors

| Code | Description |
|------|-------------|
| WS-001 | Connection failed |
| WS-002 | Authentication failed |
| WS-003 | Subscription failed |
| WS-004 | Broadcast failed |
| WS-005 | Client disconnected unexpectedly |

Transient connection issues should not affect scheduler execution.

---

# 16. Logging Requirements

Every logged error should include:

- Error code
- Timestamp
- Module
- Class
- Method
- Symbol (if applicable)
- Timeframe (if applicable)
- Exception type
- Stack trace (internal logs only)
- Request ID (if available)

Example

```
ERROR AI-005

RecommendationEngine.analyze()

Symbol=XAUUSD

Timeframe=M1

Validation failed.
```

---

# 17. Troubleshooting Guide

| Symptom | Likely Error | Resolution |
|---------|--------------|------------|
| MT5 login failed | MT5-002 | Verify credentials |
| IPC timeout | MT5-003 | Restart terminal |
| Scheduler skips jobs | SCH-003 | Increase interval or optimize job |
| AI returns invalid JSON | AI-004 | Improve prompt or parser |
| Recommendation validation fails | AI-005 / VAL-002 | Review response schema |
| Duplicate candles | DB-007 | Check repository filtering |
| API returns 500 | API-009 | Review application logs |

---

# 18. Error Recovery Strategy

Athena uses layered recovery.

```
Exception

↓

Log

↓

Translate to domain error

↓

Recover (if possible)

↓

Return standardized error

↓

Continue application
```

Recovery priorities:

1. Preserve application availability
2. Avoid data corruption
3. Retry transient failures
4. Return meaningful errors
5. Escalate unrecoverable failures

---

# 19. Best Practices

- Use standardized error codes.
- Log contextual information.
- Never expose stack traces to clients.
- Translate infrastructure exceptions into domain errors.
- Keep error messages actionable.
- Document new errors before release.
- Review error codes during code review.

---

# 20. Related Documents

Architecture

- 16_Background_Scheduler.md
- 18_Service_Layer.md
- 22_Security_Guide.md

Implementation

- 30_Service_Class_Reference.md
- 31_Repository_Class_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md
- 34_Configuration_Reference.md
- 35_Environment_Variables_Reference.md

Operations

- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md

---

# Error Registration Checklist

Before introducing a new error:

- [ ] Error code assigned
- [ ] Category selected
- [ ] Root cause documented
- [ ] Recovery action documented
- [ ] Logging level defined
- [ ] API mapping reviewed
- [ ] Tests added
- [ ] Documentation updated

---

# Error Severity Levels

| Severity | Description |
|-----------|-------------|
| INFO | Informational events |
| WARNING | Recoverable issues |
| ERROR | Operation failed but application continues |
| CRITICAL | Startup failure or unrecoverable application state |

---

# Future Improvements

Future versions of this document should include:

- Complete exception hierarchy
- HTTP error mapping diagrams
- Sequence diagrams for recovery flows
- Retry policy matrix
- Error telemetry integration
- OpenTelemetry event mapping
- Sentry integration guidelines
- Incident response procedures
- SLA/SLO error budget mappings
- Automated troubleshooting playbooks

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Error Code Reference |

---

**Document End**

© Athena AI Terminal Project
