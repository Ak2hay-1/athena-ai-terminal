# Athena AI Terminal
# Background Scheduler

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Background Scheduler |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, DevOps Engineers, System Architects, AI Assistants |

---

# Table of Contents

1. Introduction
2. Objectives
3. Scheduler Overview
4. Scheduler Architecture
5. Current Implementation
6. Folder Structure
7. Job Lifecycle
8. Application Startup
9. Application Shutdown
10. Job Registration
11. Market Data Collection Job
12. Market Analysis Job
13. Recommendation Generation Job
14. Scheduler Configuration
15. Concurrency Management
16. Error Handling
17. Logging
18. Monitoring
19. Performance
20. Scaling Strategy
21. Future Scheduled Jobs
22. Best Practices
23. Related Documents

---

# 1. Introduction

The Background Scheduler is responsible for executing all automated tasks within Athena.

Rather than waiting for a user request, the scheduler continuously performs predefined jobs according to configured schedules.

Examples include:

- Collect market candles
- Analyze market conditions
- Generate AI recommendations
- Broadcast updates
- Future maintenance tasks

The scheduler acts as the heartbeat of the system.

---

# 2. Objectives

The scheduler provides:

- Automated execution
- Reliable timing
- Continuous market monitoring
- Centralized orchestration
- Fault tolerance
- Extensibility

---

# 3. Scheduler Overview

Current scheduler implementation:

```
APScheduler
```

Responsibilities:

- Register jobs
- Execute jobs
- Track execution
- Handle failures
- Prevent overlapping runs
- Shutdown gracefully

---

# 4. Scheduler Architecture

```text
FastAPI Startup

↓

Scheduler Initialization

↓

Job Registration

↓

Timed Execution

↓

Service Layer

↓

Repository Layer

↓

Database

↓

WebSocket Broadcast
```

---

# 5. Current Implementation

Current scheduler file:

```
app/scheduler/market_scheduler.py
```

The scheduler is started during FastAPI startup and stopped during application shutdown.

Primary responsibilities:

- Collect candles
- Trigger market analysis
- Trigger recommendation generation

---

# 6. Folder Structure

```
app/

└── scheduler/

    ├── market_scheduler.py
    ├── __init__.py
```

Future expansion:

```
scheduler/

market_scheduler.py

maintenance_scheduler.py

cleanup_scheduler.py

notification_scheduler.py

health_scheduler.py

backtest_scheduler.py
```

---

# 7. Job Lifecycle

Every scheduled task follows the same lifecycle.

```text
Register Job

↓

Wait

↓

Execute

↓

Success / Failure

↓

Log

↓

Next Execution
```

---

# 8. Application Startup

During application startup:

```text
FastAPI Startup

↓

Initialize Database

↓

Initialize MT5

↓

Initialize Scheduler

↓

Register Jobs

↓

Start Scheduler
```

If scheduler initialization fails, the application should log the error and prevent incomplete startup.

---

# 9. Application Shutdown

Shutdown sequence:

```text
Receive Shutdown Signal

↓

Stop Scheduler

↓

Wait for Running Jobs

↓

Disconnect MT5

↓

Close Database

↓

Application Exit
```

Jobs should be allowed to finish gracefully whenever possible.

---

# 10. Job Registration

Jobs are registered during scheduler initialization.

Current example:

```text
collect_xauusd_m1
```

Typical configuration:

- Interval Trigger
- Execution Frequency
- Max Instances
- Misfire Handling
- Next Run Time

Future jobs should be registered through a centralized configuration.

---

# 11. Market Data Collection Job

Current responsibility:

Collect the latest candles from MT5.

Workflow:

```text
Scheduler

↓

MT5 Manager

↓

Copy Rates

↓

Validate Data

↓

Remove Duplicates

↓

Save Database
```

Current symbol:

```
XAUUSD
```

Current timeframe:

```
M1
```

Future support:

- Multiple symbols
- Multiple timeframes
- Parallel execution

---

# 12. Market Analysis Job

After new candles are stored:

```text
Load Latest Candles

↓

Calculate Indicators

↓

Detect Patterns

↓

Generate Market Summary
```

The analysis engine prepares structured data for the recommendation engine.

---

# 13. Recommendation Generation Job

After market analysis:

```text
Market Summary

↓

Recommendation Engine

↓

Prompt Builder

↓

AI Client

↓

Response Parser

↓

Validation

↓

Store Recommendation

↓

Broadcast
```

Only validated recommendations should be persisted.

---

# 14. Scheduler Configuration

Typical settings:

| Parameter | Purpose |
|-----------|---------|
| Interval | Execution frequency |
| max_instances | Prevent overlapping jobs |
| coalesce | Merge missed executions |
| misfire_grace_time | Allowed execution delay |
| timezone | Scheduler timezone |

Example:

```text
Every 1 minute

max_instances = 1

coalesce = True
```

Configuration should be loaded from application settings where possible.

---

# 15. Concurrency Management

To prevent duplicate processing:

- Limit concurrent executions
- Use max_instances
- Avoid overlapping market collection
- Prevent duplicate recommendations

Example:

```text
Execution of job skipped:
maximum number of running instances reached
```

This protects data consistency.

---

# 16. Error Handling

Possible failures:

- MT5 unavailable
- Database unavailable
- AI unavailable
- Network timeout
- Invalid market data

Recovery strategy:

```text
Catch Exception

↓

Log Error

↓

Continue Scheduler

↓

Retry Next Cycle
```

The scheduler should never terminate because of a single job failure.

---

# 17. Logging

Typical log messages:

```text
Scheduler Started

Collecting XAUUSD M1

500 Candles Retrieved

Market Analysis Completed

Recommendation Generated

Scheduler Stopped
```

Errors should include stack traces during development and structured summaries in production.

---

# 18. Monitoring

Operational metrics:

- Scheduler status
- Last execution time
- Next execution time
- Execution duration
- Failed jobs
- Successful jobs
- Average runtime

Future health endpoint:

```
GET /scheduler/status
```

Example response:

```json
{
  "status": "running",
  "jobs": 3,
  "last_execution": "2026-07-15T14:20:00Z",
  "next_execution": "2026-07-15T14:21:00Z"
}
```

---

# 19. Performance

Current optimizations:

- Incremental candle collection
- Shared database session
- Reusable MT5 connection
- Vectorized analysis

Future optimizations:

- Async job execution
- Parallel symbols
- Parallel timeframes
- Distributed scheduling
- Job prioritization

---

# 20. Scaling Strategy

Current architecture:

```text
FastAPI

↓

Local APScheduler

↓

Local Jobs
```

Future production architecture:

```text
Load Balancer

↓

Multiple FastAPI Instances

↓

Distributed Scheduler

↓

Redis

↓

Worker Nodes

↓

Database
```

Only one scheduler instance should own a specific recurring job to avoid duplicate execution.

---

# 21. Future Scheduled Jobs

Planned automation:

- Multi-symbol synchronization
- H1/H4/D1 candle collection
- News synchronization
- Economic calendar updates
- AI model health checks
- Database cleanup
- Backup creation
- Log rotation
- Notification delivery
- Strategy evaluation
- Backtesting automation
- Portfolio recalculation
- Trade management

---

# 22. Best Practices

- Keep jobs idempotent.
- Keep execution time shorter than the scheduling interval.
- Log every execution.
- Handle failures gracefully.
- Avoid long-running synchronous operations.
- Separate scheduling from business logic.
- Make schedules configurable.
- Monitor execution duration.

---

# 23. Related Documents

- 05_Backend_Architecture.md
- 07_MT5_Integration.md
- 11_Market_Analysis_Engine.md
- 12_Recommendation_Engine.md
- 13_REST_API.md
- 14_WebSocket_Architecture.md
- 19_Deployment_Guide.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Background Scheduler documentation |

---

**Document End**

© Athena AI Terminal Project
