# Athena AI Terminal
# Deployment Guide

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Deployment Guide |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | DevOps Engineers, Backend Developers, System Administrators, AI Assistants |

---

# Table of Contents

1. Introduction
2. Deployment Goals
3. Supported Environments
4. System Requirements
5. Project Structure
6. Environment Variables
7. Local Development Deployment
8. Docker Deployment
9. Docker Compose Deployment
10. Production Deployment
11. Reverse Proxy
12. SSL Configuration
13. Database Deployment
14. MetaTrader 5 Deployment
15. Ollama Deployment
16. Background Scheduler
17. Monitoring
18. Logging
19. Backup Strategy
20. Disaster Recovery
21. CI/CD
22. Updating Athena
23. Scaling
24. Troubleshooting
25. Best Practices
26. Related Documents

---

# 1. Introduction

This document explains how Athena is deployed across development, testing, staging, and production environments.

Deployment includes:

- Backend API
- PostgreSQL
- MetaTrader 5
- Ollama
- Background Scheduler
- Frontend (future)
- Reverse Proxy
- SSL
- Monitoring

---

# 2. Deployment Goals

Athena deployments should be:

- Repeatable
- Secure
- Automated
- Observable
- Recoverable
- Scalable

---

# 3. Supported Environments

Development

```
Windows

Python

PostgreSQL

MetaTrader 5

Ollama
```

Testing

```
Docker

Temporary Database
```

Staging

```
Linux

Docker Compose

HTTPS
```

Production

```
Ubuntu Server

Docker

NGINX

PostgreSQL

Redis (future)

Monitoring
```

---

# 4. System Requirements

Minimum

| Component | Requirement |
|-----------|-------------|
| CPU | 4 Cores |
| RAM | 8 GB |
| Storage | 50 GB SSD |
| Python | 3.13 |
| PostgreSQL | 16+ |
| MetaTrader 5 | Latest Stable |
| Ollama | Latest Stable |

Recommended

| Component | Requirement |
|-----------|-------------|
| CPU | 8+ Cores |
| RAM | 16–32 GB |
| Storage | NVMe SSD |
| GPU | Optional (AI acceleration) |

---

# 5. Project Structure

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

---

# 6. Environment Variables

Environment configuration is stored in:

```
.env
```

Typical variables:

```
APP_NAME=Athena

APP_ENV=development

DEBUG=True

DATABASE_URL=

POSTGRES_HOST=

POSTGRES_PORT=

POSTGRES_DB=

POSTGRES_USER=

POSTGRES_PASSWORD=

MT5_LOGIN=

MT5_PASSWORD=

MT5_SERVER=

MT5_PATH=

OLLAMA_URL=http://127.0.0.1:11434

OLLAMA_MODEL=llama3.2

SECRET_KEY=

JWT_SECRET=

JWT_ALGORITHM=

ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Secrets must never be committed to Git.

---

# 7. Local Development Deployment

Steps:

### Clone repository

```bash
git clone <repository>
```

---

### Create virtual environment

```bash
python -m venv .venv
```

---

### Activate

Windows

```powershell
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

---

### Install dependencies

```bash
pip install -r requirements.txt
```

---

### Start PostgreSQL

Verify database connectivity.

---

### Start MetaTrader 5

Log in using a valid trading account.

---

### Start Ollama

```bash
ollama serve
```

Pull the configured model if it is not already installed:

```bash
ollama pull llama3.2
```

---

### Start Backend

```bash
uvicorn app.main:app --reload
```

---

### Verify

Open:

```
http://localhost:8000/docs
```

---

# 8. Docker Deployment

Example Dockerfile responsibilities:

- Python runtime
- Dependency installation
- Application copy
- Uvicorn startup

Future Docker images:

```
backend

frontend

postgres

redis

monitoring
```

---

# 9. Docker Compose Deployment

Typical services:

```yaml
backend

postgres

ollama

frontend

nginx
```

Future additions:

```
redis

grafana

prometheus

loki
```

---

# 10. Production Deployment

Recommended architecture:

```
Internet

↓

NGINX

↓

FastAPI

↓

PostgreSQL

↓

Ollama

↓

MetaTrader 5

↓

Scheduler
```

Only HTTPS traffic should be exposed publicly.

---

# 11. Reverse Proxy

Recommended:

```
NGINX
```

Responsibilities:

- HTTPS
- Compression
- Static assets
- WebSocket proxy
- Security headers
- Rate limiting

---

# 12. SSL Configuration

Recommended provider:

```
Let's Encrypt
```

Certificates should be renewed automatically.

All production traffic should use HTTPS/WSS.

---

# 13. Database Deployment

Database:

```
PostgreSQL
```

Deployment checklist:

- Create database
- Create user
- Configure permissions
- Run migrations
- Verify connectivity

Future:

- Read replicas
- Partitioning
- Automatic failover

---

# 14. MetaTrader 5 Deployment

Requirements:

- Installed terminal
- Logged-in account
- Stable internet connection
- Configured credentials

Health checks:

- Connection status
- Account status
- Symbol availability
- Historical data retrieval

---

# 15. Ollama Deployment

Verify installation:

```bash
ollama --version
```

Verify server:

```bash
curl http://127.0.0.1:11434/api/tags
```

Install model:

```bash
ollama pull llama3.2
```

Verify generation:

```bash
ollama run llama3.2
```

Health endpoint:

```
/api/tags
```

Future:

- Multiple models
- GPU inference
- Model switching

---

# 16. Background Scheduler

Scheduler starts during FastAPI startup.

Responsibilities:

- Market synchronization
- Analysis
- Recommendations

Deployment verification:

- Scheduler started
- Jobs registered
- Next execution scheduled

---

# 17. Monitoring

Recommended metrics:

- CPU
- Memory
- Disk
- Database connections
- MT5 connection
- Scheduler status
- API latency
- AI latency
- Recommendation count

Recommended tools:

```
Prometheus

Grafana
```

---

# 18. Logging

Recommended log files:

```
application.log

scheduler.log

mt5.log

ai.log

api.log
```

Future:

- Loki
- ELK Stack
- OpenSearch

---

# 19. Backup Strategy

Daily

- PostgreSQL backup

Weekly

- Full backup

Monthly

- Archive

Also back up:

- Configuration
- Environment files (encrypted)
- Documentation

Never back up plaintext secrets.

---

# 20. Disaster Recovery

Recovery procedure:

1. Restore PostgreSQL
2. Restore configuration
3. Start MT5
4. Start Ollama
5. Start Backend
6. Verify scheduler
7. Verify recommendations

Recovery objectives should be documented:

- RPO (Recovery Point Objective)
- RTO (Recovery Time Objective)

---

# 21. CI/CD

Recommended pipeline:

```text
Git Push

↓

Lint

↓

Unit Tests

↓

Integration Tests

↓

Build

↓

Docker Image

↓

Deploy

↓

Health Check
```

Suggested tools:

- GitHub Actions
- GitLab CI
- Azure DevOps
- Jenkins

---

# 22. Updating Athena

Deployment update procedure:

1. Pull latest code
2. Install dependencies
3. Run migrations
4. Restart backend
5. Verify MT5
6. Verify Ollama
7. Confirm scheduler
8. Execute smoke tests

---

# 23. Scaling

Current architecture:

```
Single Backend

Single Database
```

Future architecture:

```text
Load Balancer

↓

Multiple FastAPI Instances

↓

Redis

↓

PostgreSQL

↓

Read Replica

↓

Monitoring
```

Future scalability goals:

- Horizontal API scaling
- Distributed schedulers
- AI worker pools
- Multi-region deployment

---

# 24. Troubleshooting

Common issues:

## Database Connection

Check:

- Credentials
- Port
- Firewall
- Service status

---

## MT5 Authorization Failed

Check:

- Login
- Password
- Server
- Terminal status

---

## Ollama Model Missing

Verify:

```bash
ollama list
```

Pull the required model if absent.

---

## Scheduler Not Running

Verify:

- Startup logs
- APScheduler configuration
- Registered jobs

---

## API Unreachable

Verify:

- Uvicorn
- Reverse proxy
- Firewall
- SSL
- Port bindings

---

# 25. Best Practices

- Keep secrets outside the repository.
- Use HTTPS in production.
- Monitor every service.
- Automate deployments.
- Test backups regularly.
- Document infrastructure changes.
- Pin dependency versions.
- Keep deployment scripts under version control.

---

# 26. Related Documents

- 04_Technology_Stack.md
- 05_Backend_Architecture.md
- 06_Database_Design.md
- 07_MT5_Integration.md
- 13_REST_API.md
- 14_WebSocket_Architecture.md
- 16_Background_Scheduler.md
- 22_Security_Guide.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial deployment guide |

---

**Document End**

© Athena AI Terminal Project
