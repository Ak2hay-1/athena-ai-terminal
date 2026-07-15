# Athena AI Terminal
# REST API Documentation

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | REST API Documentation |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Frontend Developers, Mobile Developers, QA Engineers, API Consumers, AI Assistants |

---

# Table of Contents

1. Introduction
2. API Goals
3. API Architecture
4. Versioning
5. Base URL
6. Authentication
7. Request Standards
8. Response Standards
9. HTTP Status Codes
10. API Modules
11. Health API
12. Authentication API
13. MT5 API
14. Market Data API
15. Recommendation API
16. AI API
17. Watchlist API
18. Settings API
19. WebSocket Endpoint
20. Error Handling
21. Rate Limiting
22. Security
23. OpenAPI Documentation
24. API Lifecycle
25. Future Endpoints
26. Best Practices
27. Related Documents

---

# 1. Introduction

Athena exposes a RESTful API that allows external systems to interact with the backend.

Supported clients include:

- React Dashboard
- Mobile Applications
- CLI Tools
- AI Agents
- Third-party Integrations
- Internal Services

The REST API is the primary communication interface for synchronous operations.

---

# 2. API Goals

The API is designed to be:

- RESTful
- Predictable
- Versioned
- Secure
- Consistent
- Documented
- Backward Compatible

---

# 3. API Architecture

```text
Client

↓

REST API

↓

FastAPI Router

↓

Service Layer

↓

Repository Layer

↓

Database

↓

Response
```

No endpoint should communicate directly with the database.

---

# 4. Versioning

Current Version

```
/api/v1
```

Future versions

```
/api/v2

/api/v3
```

Breaking changes must introduce a new API version.

---

# 5. Base URL

Development

```
http://localhost:8000/api/v1
```

Production

```
https://api.athena.ai/api/v1
```

---

# 6. Authentication

Current

Public endpoints are available during development.

Future

JWT Authentication

OAuth2

API Keys

Refresh Tokens

Role-Based Access Control (RBAC)

---

# 7. Request Standards

## Content Type

```
application/json
```

---

## Headers

Example

```
Content-Type: application/json

Authorization: Bearer <token>

Accept: application/json
```

---

## Query Parameters

Example

```
GET /recommendations?symbol=XAUUSD&timeframe=M1
```

---

## Path Parameters

Example

```
GET /market/XAUUSD
```

---

# 8. Response Standards

Every successful response should follow a consistent structure.

Example

```json
{
  "success": true,
  "message": "Operation completed.",
  "data": {}
}
```

Error example

```json
{
  "success": false,
  "message": "Recommendation not found.",
  "errors": []
}
```

---

# 9. HTTP Status Codes

| Code | Meaning |
|------|----------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

# 10. API Modules

The REST API is organized into logical modules.

Current modules

```
Health

Authentication

MT5

Market

Recommendations

AI

Watchlists

Settings
```

Future modules

```
Portfolio

Orders

Strategies

Notifications

Analytics

Backtesting

Users
```

---

# 11. Health API

Purpose

Application health monitoring.

Example endpoints

```
GET /health

GET /health/live

GET /health/ready
```

Typical response

```json
{
  "status": "healthy",
  "database": "connected",
  "mt5": "connected",
  "scheduler": "running"
}
```

---

# 12. Authentication API

Future endpoints

```
POST /auth/login

POST /auth/logout

POST /auth/refresh

GET /auth/me

PATCH /auth/password
```

Responsibilities

- Login
- Token generation
- User profile
- Password management

---

# 13. MT5 API

Purpose

Interact with MetaTrader integration.

Example endpoints

```
GET /mt5/status

POST /mt5/connect

POST /mt5/disconnect

GET /mt5/symbols

GET /mt5/account
```

Possible responses

- Connected
- Disconnected
- Authorization Failed
- IPC Timeout

---

# 14. Market Data API

Purpose

Retrieve historical and current market data.

Example endpoints

```
GET /market/candles

GET /market/latest

GET /market/history

GET /market/symbols

GET /market/timeframes
```

Typical query parameters

```
symbol

timeframe

limit

start

end
```

---

# 15. Recommendation API

Purpose

Access generated recommendations.

Example endpoints

```
GET /recommendations

GET /recommendations/latest

GET /recommendations/history

GET /recommendations/{id}
```

Example response

```json
{
  "symbol": "XAUUSD",
  "timeframe": "M1",
  "signal": "BUY",
  "confidence": 82,
  "entry": 3358.40,
  "stop_loss": 3352.80,
  "take_profit": 3371.50,
  "risk_reward": 2.3
}
```

---

# 16. AI API

Purpose

Expose AI-related operations.

Future endpoints

```
POST /ai/analyze

GET /ai/models

GET /ai/status

PATCH /ai/model
```

Future capabilities

- Change AI model
- Compare models
- Prompt testing
- AI diagnostics

---

# 17. Watchlist API

Example endpoints

```
GET /watchlist

POST /watchlist

DELETE /watchlist/{id}

PATCH /watchlist/{id}
```

Responsibilities

- Manage favorite symbols
- Personal watchlists

---

# 18. Settings API

Example endpoints

```
GET /settings

PATCH /settings

POST /settings/reset
```

Future settings

- Preferred timeframe
- AI model
- Theme
- Notification preferences

---

# 19. WebSocket Endpoint

REST provides historical data.

Real-time updates are provided through WebSocket.

Typical endpoint

```
ws://localhost:8000/ws
```

See

```
14_WebSocket_Architecture.md
```

---

# 20. Error Handling

Errors should always return structured JSON.

Example

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": [
    {
      "field": "symbol",
      "reason": "Unknown symbol."
    }
  ]
}
```

Avoid returning raw exception traces to clients.

---

# 21. Rate Limiting

Current

Not enforced.

Future

- Per-user limits
- Per-IP limits
- API key quotas
- Burst protection

---

# 22. Security

Current

- CORS
- Input validation
- Pydantic schemas

Future

- JWT
- HTTPS
- CSRF protection
- API keys
- Audit logging
- Request signing

---

# 23. OpenAPI Documentation

FastAPI automatically exposes interactive API documentation.

Development URLs

```
/docs

/redoc

/openapi.json
```

These documents should always reflect the current API implementation.

---

# 24. API Lifecycle

```text
Client

↓

HTTP Request

↓

FastAPI Router

↓

Pydantic Validation

↓

Service Layer

↓

Repository

↓

Database

↓

Response Model

↓

JSON Response
```

---

# 25. Future Endpoints

Planned APIs

```
Portfolio

Trade History

Orders

Positions

Risk Management

Notifications

Analytics

Economic Calendar

News

Backtesting

Strategy Builder
```

---

# 26. Best Practices

- Keep endpoints resource-oriented.
- Validate all request payloads.
- Return consistent response structures.
- Use appropriate HTTP status codes.
- Avoid exposing internal implementation details.
- Version breaking changes.
- Document every endpoint.
- Prefer idempotent operations where appropriate.

---

# 27. Related Documents

- 05_Backend_Architecture.md
- 06_Database_Design.md
- 07_MT5_Integration.md
- 12_Recommendation_Engine.md
- 14_WebSocket_Architecture.md
- 15_Authentication_Authorization.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial REST API documentation |

---

**Document End**

© Athena AI Terminal Project
