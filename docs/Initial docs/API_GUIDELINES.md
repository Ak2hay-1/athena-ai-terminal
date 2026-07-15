# Athena API Guidelines

---

# API Versioning

/api/v1/

Future

/api/v2/

---

# REST Principles

Use nouns.

Good

GET /positions

POST /orders

DELETE /orders/{id}

Bad

GET /getPositions

POST /createOrder

---

# HTTP Status Codes

200

Success

201

Created

204

Deleted

400

Validation Error

401

Unauthorized

403

Forbidden

404

Not Found

409

Conflict

422

Validation Error

500

Server Error

---

# Response Format

Success

{
    "success": true,
    "data": {}
}

Failure

{
    "success": false,
    "error": {
        "code": "ORDER_FAILED",
        "message": "Insufficient margin."
    }
}

---

# Pagination

GET

?page=1&page_size=50

---

# Filtering

GET

?symbol=EURUSD

?timeframe=M15

---

# Sorting

GET

?sort=created_at

?order=desc

---

# Authentication

JWT

Bearer Token

Authorization

Bearer <token>

---

# Validation

All request bodies

Pydantic

All responses

Pydantic

---

# Documentation

Every endpoint

Summary

Description

Request Example

Response Example

Error Responses

Authentication Requirements
