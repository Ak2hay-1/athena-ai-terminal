# Athena AI Terminal
# REST API Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | REST API Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Frontend Developers, QA Engineers, API Consumers, AI Assistants |

---

# Table of Contents

1. Introduction
2. API Overview
3. Base URL
4. Authentication
5. Common Headers
6. Response Format
7. Error Response Format
8. Status Codes
9. Endpoint Reference
10. Health API
11. Market API
12. Recommendation API
13. Watchlist API
14. User API
15. Authentication API (Future)
16. Administration API (Future)
17. Pagination
18. Filtering
19. Rate Limiting
20. Versioning
21. OpenAPI Documentation
22. Best Practices
23. Related Documents

---

# 1. Introduction

The Athena REST API provides access to:

- Market Data
- AI Recommendations
- User Management
- Watchlists
- Health Monitoring
- Future Trading Features

The API follows RESTful principles and returns JSON responses.

---

# 2. API Overview

Architecture:

```text
Client

↓

REST API

↓

Service Layer

↓

Repository Layer

↓

Database
```

Current API Categories:

```
Health

Market

Recommendations

Watchlists

Users
```

Future Categories:

```
Authentication

Portfolio

Orders

Strategies

Admin
```

---

# 3. Base URL

Development

```
http://localhost:8000
```

Production

```
https://api.athena.example.com
```

API documentation

```
/docs
```

OpenAPI JSON

```
/openapi.json
```

---

# 4. Authentication

Current Status

Authentication is not yet enabled.

Future authentication:

```
Authorization: Bearer <JWT>
```

Protected endpoints will require valid access tokens.

---

# 5. Common Headers

Request

```http
Content-Type: application/json
Accept: application/json
```

Future

```http
Authorization: Bearer <token>
```

Optional

```http
X-Request-ID
```

---

# 6. Response Format

Successful responses follow a consistent JSON structure.

Example:

```json
{
  "success": true,
  "data": {
    "symbol": "XAUUSD"
  }
}
```

Future enhancement:

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "timestamp": "2026-07-15T12:00:00Z"
}
```

---

# 7. Error Response Format

Standard format:

```json
{
  "success": false,
  "error": {
    "code": "MARKET_NOT_FOUND",
    "message": "Requested market does not exist."
  }
}
```

Future enhancement:

```json
{
  "success": false,
  "error": {
    "code": "...",
    "message": "...",
    "request_id": "...",
    "details": {}
  }
}
```

---

# 8. HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Resource Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

# 9. Endpoint Reference

Current endpoint groups:

```
GET    /health

GET    /market

GET    /recommendations

GET    /watchlist

POST   /watchlist

DELETE /watchlist

GET    /users
```

Future endpoint groups:

```
/auth

/portfolio

/orders

/admin

/strategies
```

---

# 10. Health API

## GET /health

Purpose

Overall application health.

Response

```json
{
  "status": "healthy"
}
```

Status Codes

```
200
503
```

---

## GET /health/live

Purpose

Liveness probe.

Response

```json
{
  "status": "alive"
}
```

---

## GET /health/ready

Purpose

Readiness probe.

Checks:

- Database
- MT5
- Scheduler
- AI

Example

```json
{
  "database": "connected",
  "mt5": "connected",
  "scheduler": "running",
  "ai": "available"
}
```

---

# 11. Market API

## GET /market/latest

Purpose

Retrieve latest candles.

Parameters

| Name | Required | Description |
|------|----------|-------------|
| symbol | Yes | Trading symbol |
| timeframe | Yes | Candle timeframe |
| limit | No | Number of candles |

Example

```
GET /market/latest?symbol=XAUUSD&timeframe=M1
```

Response

```json
[
  {
    "time":"...",
    "open":0,
    "high":0,
    "low":0,
    "close":0,
    "volume":0
  }
]
```

---

## GET /market/history

Purpose

Historical candles.

Parameters

```
symbol

timeframe

start

end
```

---

## GET /market/summary

Purpose

Retrieve latest market analysis.

Returns

- Trend
- Volatility
- Momentum
- Confluence
- Recommendation summary

---

# 12. Recommendation API

## GET /recommendations/latest

Purpose

Latest recommendation.

Parameters

```
symbol

timeframe
```

Example

```
GET /recommendations/latest?symbol=XAUUSD&timeframe=M1
```

Example Response

```json
{
  "signal":"BUY",
  "entry":3360.10,
  "stop_loss":3350.00,
  "take_profit":3380.00,
  "confidence":82
}
```

---

## GET /recommendations/history

Purpose

Recommendation history.

Supports filtering by:

- Symbol
- Timeframe
- Date Range

---

## POST /recommendations/analyze

Purpose

Force immediate recommendation generation.

Current Status

Development endpoint.

Future access:

Admin only.

---

# 13. Watchlist API

## GET /watchlist

Retrieve user watchlist.

---

## POST /watchlist

Add symbol.

Request

```json
{
  "symbol":"EURUSD"
}
```

---

## DELETE /watchlist/{symbol}

Remove symbol.

Example

```
DELETE /watchlist/EURUSD
```

---

# 14. User API

## GET /users/me

Future endpoint.

Retrieve current user.

---

## PATCH /users/me

Update profile.

---

## DELETE /users/me

Delete account.

Future.

---

# 15. Authentication API (Future)

```
POST /auth/login

POST /auth/logout

POST /auth/refresh

POST /auth/register

POST /auth/reset-password
```

---

# 16. Administration API (Future)

```
GET /admin/users

GET /admin/system

GET /admin/jobs

POST /admin/jobs/run

POST /admin/cache/clear
```

---

# 17. Pagination

Collection endpoints should support:

```
page

page_size

sort
```

Example

```
?page=2&page_size=100
```

Future response:

```json
{
  "data": [],
  "pagination": {
    "page":2,
    "page_size":100,
    "total":540
  }
}
```

---

# 18. Filtering

Recommended query parameters:

```
symbol

timeframe

start

end

signal

trend
```

Example

```
GET /recommendations/history?symbol=XAUUSD&signal=BUY
```

---

# 19. Rate Limiting

Future limits:

| Endpoint | Limit |
|-----------|-------|
| Public | 100/min |
| Authenticated | 1000/min |
| Admin | Unlimited (configurable) |

Rate limiting headers:

```
X-RateLimit-Limit

X-RateLimit-Remaining

Retry-After
```

---

# 20. Versioning

Current

```
v1
```

Future

```
/api/v1/

/api/v2/
```

Breaking changes should require a new API version.

---

# 21. OpenAPI Documentation

Automatically generated by FastAPI.

Available at:

```
/docs
```

Machine-readable specification:

```
/openapi.json
```

---

# 22. Best Practices

API consumers should:

- Validate responses.
- Handle non-200 status codes.
- Use pagination for large datasets.
- Retry transient failures with backoff.
- Respect rate limits.
- Cache infrequently changing responses.
- Include request IDs when troubleshooting.

API developers should:

- Maintain backward compatibility within a version.
- Keep response schemas stable.
- Document new endpoints before release.
- Add automated tests for every endpoint.

---

# 23. Related Documents

Architecture

- 13_REST_API.md
- 14_WebSocket_Architecture.md
- 18_Service_Layer.md

Implementation

- 27_Backend_Package_Reference.md
- 29_Database_Model_Reference.md
- 30_Service_Class_Reference.md
- 31_Repository_Class_Reference.md

Operations

- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md
- 22_Security_Guide.md

---

# API Evolution Checklist

Before adding a new endpoint:

- [ ] Define request schema
- [ ] Define response schema
- [ ] Document status codes
- [ ] Add authentication requirements
- [ ] Implement service logic
- [ ] Add repository methods (if needed)
- [ ] Write unit and integration tests
- [ ] Update OpenAPI documentation
- [ ] Update this reference document

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial REST API reference |

---

**Document End**

© Athena AI Terminal Project
