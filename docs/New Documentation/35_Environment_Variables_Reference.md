# Athena AI Terminal
# Environment Variables Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Environment Variables Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Developers, DevOps Engineers, System Administrators, AI Assistants |

---

# Table of Contents

1. Introduction
2. Environment Variable Philosophy
3. Loading Order
4. Variable Categories
5. Complete Environment Variable Reference
6. Example .env File
7. Environment Profiles
8. Secret Management
9. Validation Rules
10. Common Configuration Errors
11. Best Practices
12. Related Documents

---

# 1. Introduction

Athena uses environment variables to configure all runtime behavior.

No sensitive or deployment-specific configuration should ever be hardcoded in the source code.

Environment variables are loaded during application startup and validated before the application becomes available.

---

# 2. Environment Variable Philosophy

Environment variables should be:

- Explicit
- Typed
- Validated
- Secure
- Environment-specific
- Documented

Every environment variable must have:

- Name
- Description
- Type
- Default value (if applicable)
- Required/Optional status
- Consuming module
- Validation rules

---

# 3. Loading Order

Athena loads configuration in the following order:

```text
Application Defaults

↓

.env

↓

Operating System Environment

↓

Container Runtime

↓

CI/CD Runtime Variables

↓

Validated Settings Object
```

Variables loaded later override previous values.

---

# 4. Variable Categories

Athena groups variables into the following categories:

- Application
- Database
- MT5
- AI
- Scheduler
- Logging
- Security
- API
- Feature Flags

---

# 5. Complete Environment Variable Reference

---

# Application

---

## APP_NAME

Description

Application display name.

Type

```
String
```

Required

```
No
```

Default

```
Athena AI Terminal
```

Used By

```
Startup
Logging
```

Example

```env
APP_NAME=Athena AI Terminal
```

---

## APP_ENV

Description

Application runtime environment.

Allowed Values

```
development

testing

staging

production
```

Default

```
development
```

Example

```env
APP_ENV=development
```

---

## APP_VERSION

Description

Application version.

Example

```env
APP_VERSION=1.0.0
```

---

# Database

---

## DATABASE_URL

Description

Complete SQLAlchemy database connection string.

Type

```
String
```

Required

```
Yes
```

Example

```env
DATABASE_URL=postgresql://user:password@localhost:5432/athena
```

Security Classification

```
Secret
```

Consumed By

```
SQLAlchemy

Repositories
```

---

## DATABASE_POOL_SIZE

Type

```
Integer
```

Default

```
10
```

---

## DATABASE_MAX_OVERFLOW

Default

```
20
```

---

## DATABASE_POOL_TIMEOUT

Default

```
30
```

---

## DATABASE_ECHO

Type

```
Boolean
```

Default

```
False
```

---

# MetaTrader 5

---

## MT5_LOGIN

Description

Trading account login.

Type

```
Integer
```

Required

```
Yes
```

Security

```
Secret
```

---

## MT5_PASSWORD

Description

Trading account password.

Type

```
String
```

Required

```
Yes
```

Security

```
Secret
```

---

## MT5_SERVER

Example

```env
MT5_SERVER=MetaQuotes-Demo
```

---

## MT5_PATH

Description

Path to terminal executable.

Windows Example

```env
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

---

## MT5_TIMEOUT

Default

```
60000
```

Milliseconds.

---

## MT5_RECONNECT_DELAY

Default

```
5
```

Seconds.

---

# AI

---

## OLLAMA_URL

Example

```env
OLLAMA_URL=http://127.0.0.1:11434
```

Consumed By

```
client.py
```

---

## OLLAMA_MODEL

Example

```env
OLLAMA_MODEL=llama3.2
```

Validation

Model should exist:

```bash
ollama list
```

---

## AI_TIMEOUT

Default

```
120
```

Seconds.

---

## AI_RETRIES

Default

```
2
```

---

## AI_TEMPERATURE

Default

```
0.2
```

Range

```
0.0–2.0
```

---

## AI_MAX_TOKENS

Default

```
1024
```

---

# Scheduler

---

## ENABLE_SCHEDULER

Type

```
Boolean
```

Default

```
True
```

---

## COLLECTION_INTERVAL

Default

```
60
```

Seconds.

---

## ANALYSIS_INTERVAL

Default

```
60
```

Seconds.

---

## MAX_JOB_INSTANCES

Default

```
1
```

---

## MISFIRE_GRACE_TIME

Default

```
30
```

Seconds.

---

# Logging

---

## LOG_LEVEL

Allowed Values

```
DEBUG

INFO

WARNING

ERROR

CRITICAL
```

Default

```
INFO
```

---

## LOG_FILE

Example

```env
LOG_FILE=logs/athena.log
```

---

## LOG_ROTATION

Example

```
10 MB
```

---

## LOG_RETENTION

Example

```
30 days
```

---

# Security

---

## SECRET_KEY

Purpose

Application secret.

Security

```
Highly Confidential
```

---

## JWT_SECRET

Purpose

JWT signing.

---

## JWT_ALGORITHM

Default

```
HS256
```

---

## JWT_EXPIRATION

Default

```
60
```

Minutes.

---

## PASSWORD_HASH_ROUNDS

Default

```
12
```

---

## CORS_ORIGINS

Example

```env
CORS_ORIGINS=http://localhost:3000
```

---

# Feature Flags

---

## ENABLE_AI

Default

```
True
```

---

## ENABLE_MT5

Default

```
True
```

---

## ENABLE_WEBSOCKET

Default

```
True
```

---

## ENABLE_BACKTESTING

Default

```
False
```

---

## ENABLE_AUTH

Default

```
False
```

---

# API

---

## API_HOST

Default

```
127.0.0.1
```

---

## API_PORT

Default

```
8000
```

---

## API_PREFIX

Default

```
/api/v1
```

---

# 6. Example .env File

```env
APP_NAME=Athena AI Terminal
APP_ENV=development
APP_VERSION=1.0.0

DATABASE_URL=postgresql://postgres:password@localhost:5432/athena
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=False

MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_TIMEOUT=60000
MT5_RECONNECT_DELAY=5

OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
AI_TIMEOUT=120
AI_RETRIES=2
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=1024

ENABLE_SCHEDULER=True
COLLECTION_INTERVAL=60
ANALYSIS_INTERVAL=60
MAX_JOB_INSTANCES=1
MISFIRE_GRACE_TIME=30

LOG_LEVEL=INFO
LOG_FILE=logs/athena.log
LOG_ROTATION=10 MB
LOG_RETENTION=30 days

SECRET_KEY=replace_me
JWT_SECRET=replace_me
JWT_ALGORITHM=HS256
JWT_EXPIRATION=60
PASSWORD_HASH_ROUNDS=12
CORS_ORIGINS=http://localhost:3000

ENABLE_AI=True
ENABLE_MT5=True
ENABLE_WEBSOCKET=True
ENABLE_BACKTESTING=False
ENABLE_AUTH=False

API_HOST=127.0.0.1
API_PORT=8000
API_PREFIX=/api/v1
```

---

# 7. Environment Profiles

## Development

- Debug logging
- Local PostgreSQL
- Local Ollama
- Demo MT5 account

---

## Testing

- Mock AI
- Mock MT5
- Temporary database
- Fast execution

---

## Staging

- Production-like infrastructure
- Limited users
- Full monitoring

---

## Production

- Real trading account (if enabled)
- Secure secrets
- Monitoring
- Backup enabled
- Restricted logging

---

# 8. Secret Management

Secrets include:

- DATABASE_URL
- MT5_PASSWORD
- SECRET_KEY
- JWT_SECRET

Never:

- Commit secrets to Git
- Share secrets in documentation
- Log secrets
- Send secrets to clients

Recommended storage:

- GitHub Actions Secrets
- Azure Key Vault
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

---

# 9. Validation Rules

Startup validation includes:

Database

- Valid connection string

MT5

- Login present
- Password present
- Server present

AI

- Valid URL
- Model configured

Scheduler

- Positive intervals

Logging

- Valid log level

Application startup should fail if required configuration is invalid.

---

# 10. Common Configuration Errors

| Problem | Possible Cause | Resolution |
|----------|----------------|------------|
| Database connection failed | Incorrect DATABASE_URL | Verify connection string |
| MT5 authorization failed | Wrong login/password | Verify MT5 credentials |
| MT5 IPC timeout | Terminal not running | Start MetaTrader 5 |
| Ollama connection failed | Ollama service stopped | Start Ollama |
| Model not found | Invalid OLLAMA_MODEL | Run `ollama list` |
| Scheduler not running | Disabled or invalid interval | Verify scheduler settings |
| JWT errors | Invalid secret | Generate a secure secret key |

---

# 11. Best Practices

- Use `.env.example` as a template.
- Never commit `.env` files containing secrets.
- Use different values for each environment.
- Validate all required variables at startup.
- Rotate secrets periodically.
- Keep development defaults safe.
- Document every new variable before use.

---

# 12. Related Documents

Architecture

- 05_Backend_Architecture.md
- 07_MT5_Integration.md
- 08_AI_Architecture.md

Implementation

- 34_Configuration_Reference.md
- 32_AI_Module_Reference.md
- 33_MT5_Module_Reference.md

Operations

- 19_Deployment_Guide.md
- 21_Logging_Observability.md
- 22_Security_Guide.md

---

# Environment Variable Checklist

Before introducing a new environment variable:

- [ ] Added to `settings.py`
- [ ] Type validated
- [ ] Default value reviewed
- [ ] Security classification assigned
- [ ] `.env.example` updated
- [ ] Deployment documentation updated
- [ ] Tests updated
- [ ] This document updated

---

# Security Classification

| Classification | Examples |
|----------------|----------|
| Public | APP_NAME, API_PORT |
| Internal | LOG_LEVEL, ENABLE_AI |
| Secret | DATABASE_URL, MT5_PASSWORD |
| Highly Confidential | SECRET_KEY, JWT_SECRET |

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Environment Variables Reference |

---

**Document End**

© Athena AI Terminal Project
