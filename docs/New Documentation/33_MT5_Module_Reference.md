# Athena AI Terminal
# MetaTrader 5 (MT5) Module Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | MT5 Module Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Trading Engineers, DevOps Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. MT5 Architecture
3. Connection Lifecycle
4. Module Overview
5. manager.py
6. interfaces.py
7. candle_collector.py
8. Market Data Workflow
9. Scheduler Integration
10. Error Handling
11. Logging
12. Performance Considerations
13. Future Trading Modules
14. Extension Guidelines
15. Related Documents

---

# 1. Introduction

Athena uses the official MetaTrader 5 Python package to communicate with a locally installed MetaTrader 5 terminal.

The MT5 subsystem is responsible for:

- Terminal initialization
- Authentication
- Connection management
- Symbol information
- Historical candle retrieval
- Future live price streaming
- Future order execution

The subsystem is designed so that the rest of Athena never directly communicates with MetaTrader5.

All broker interactions are encapsulated inside dedicated modules.

---

# 2. MT5 Architecture

```
Market Scheduler

↓

MarketService

↓

MT5 Manager

↓

MetaTrader5 Python API

↓

MetaTrader 5 Terminal

↓

Broker Server
```

Only the MT5 Manager should communicate with the MetaTrader5 package.

---

# 3. Connection Lifecycle

Application startup

```
FastAPI Startup

↓

Load Configuration

↓

Initialize MT5 Manager

↓

Initialize Terminal

↓

Login

↓

Validate Connection

↓

Ready
```

Shutdown

```
Stop Scheduler

↓

Close MT5 Session

↓

Shutdown Terminal Connection

↓

Application Exit
```

Reconnect

```
Failure

↓

Log Error

↓

Retry Initialization

↓

Reconnect

↓

Resume Collection
```

---

# 4. Module Overview

Current modules

```
mt5/

manager.py

interfaces.py

candle_collector.py
```

Future modules

```
order_manager.py

position_manager.py

account_manager.py

trade_executor.py

symbol_cache.py

market_stream.py
```

---

# 5. manager.py

## Purpose

Provides the primary abstraction around the MetaTrader5 Python package.

---

## Responsibilities

- Initialize terminal
- Authenticate
- Shutdown
- Retrieve symbols
- Retrieve candles
- Retrieve account information
- Handle MT5 errors
- Hide MetaTrader5 API complexity

---

## Dependencies

```
MetaTrader5

Configuration

Logger
```

---

## Public Methods

Typical methods

```python
initialize()

shutdown()

connected()

last_error()

account_info()

terminal_info()

symbols_get()

symbol_info()

copy_rates_from()

copy_rates_from_pos()

copy_rates_range()

copy_ticks_range()
```

---

## Responsibilities

The manager should never:

- Calculate indicators
- Save database records
- Generate recommendations
- Execute scheduler logic

Its only responsibility is broker communication.

---

## Typical Workflow

```
Service

↓

Manager

↓

MetaTrader5 API

↓

Broker

↓

Manager

↓

Service
```

---

## Connection Validation

Checks

- Terminal initialized
- Login successful
- Trading server reachable
- Symbol available

---

# 6. interfaces.py

## Purpose

Defines contracts for broker communication.

---

## Responsibilities

- Abstract broker implementation
- Enable future broker support
- Define required methods
- Provide consistent interfaces

---

## Example Interface

```python
initialize()

shutdown()

connected()

copy_rates_from()

copy_rates_range()

account_info()
```

---

## Benefits

Supports future integrations such as

- cTrader
- Interactive Brokers
- Binance
- OANDA
- FIX API

without changing business logic.

---

# 7. candle_collector.py

## Purpose

Synchronize historical market candles between MT5 and the database.

---

## Responsibilities

- Download candles
- Prevent duplicates
- Validate timestamps
- Batch insert candles
- Support multiple timeframes

---

## Dependencies

```
MT5 Manager

MarketRepository

Logger
```

---

## Public Methods

Typical methods

```python
collect_m1()

collect_m5()

collect_m15()

collect_h1()

collect()

_sync()

_validate()
```

---

## Workflow

```
Scheduler

↓

Collector

↓

MT5

↓

Downloaded Candles

↓

Filter Existing

↓

Bulk Insert

↓

Database
```

---

## Duplicate Prevention

Typical process

```
Download

↓

Extract timestamps

↓

Query existing timestamps

↓

Remove duplicates

↓

Insert remaining candles
```

---

## Validation

Each candle should satisfy

- High ≥ Open
- High ≥ Close
- Low ≤ Open
- Low ≤ Close
- Timestamp exists
- Volume ≥ 0

Invalid candles should be skipped and logged.

---

# 8. Market Data Workflow

Current workflow

```
Scheduler Trigger

↓

MarketScheduler

↓

CandleCollector

↓

MT5 Manager

↓

copy_rates_from_pos()

↓

NumPy Array

↓

DataFrame

↓

Repository

↓

Database
```

Future real-time workflow

```
Market Tick

↓

MT5

↓

Streaming Layer

↓

WebSocket

↓

Frontend
```

---

# 9. Scheduler Integration

The scheduler periodically executes market synchronization jobs.

Current jobs

```
collect_xauusd_m1()
```

Future jobs

```
collect_xauusd_m5()

collect_xauusd_h1()

collect_forex()

collect_crypto()

collect_indices()
```

The scheduler should never access MetaTrader5 directly; it must always use the MT5 Manager or Candle Collector.

---

# 10. Error Handling

Common MT5 errors

| Error | Description |
|--------|-------------|
| Authorization Failed | Invalid login credentials |
| IPC Timeout | Terminal communication timeout |
| No Connection | Terminal unavailable |
| Invalid Symbol | Symbol not found |
| No History | Historical data unavailable |
| Terminal Closed | Terminal not running |

---

## Recovery Strategy

```
Error

↓

Log

↓

Retry

↓

Reconnect

↓

Continue Scheduler
```

Fatal errors should stop initialization; transient errors should trigger retries.

---

# 11. Logging

Every significant MT5 operation should be logged.

Examples

Startup

```
Connected to MetaTrader 5.
```

Collection

```
Downloaded 500 candles for XAUUSD M1.
```

Persistence

```
Inserted 498 new candles.
Skipped 2 duplicates.
```

Shutdown

```
Disconnected from MetaTrader 5.
```

Errors

```
Authorization failed.

IPC timeout.

Unable to retrieve candles.
```

Logs should include

- Symbol
- Timeframe
- Record count
- Execution time
- Error code (if available)

---

# 12. Performance Considerations

Current optimizations

- Batch candle retrieval
- Batch inserts
- Duplicate filtering
- Reused MT5 connection

Future optimizations

- Symbol cache
- Incremental synchronization
- Parallel symbol collection
- Async scheduling
- Memory-efficient streaming

Avoid repeatedly reconnecting to the terminal during normal operation.

---

# 13. Future Trading Modules

Planned additions

## order_manager.py

Responsibilities

- Place orders
- Modify orders
- Cancel orders

---

## position_manager.py

Responsibilities

- Retrieve open positions
- Close positions
- Position history

---

## account_manager.py

Responsibilities

- Balance
- Equity
- Margin
- Leverage
- Profit/Loss

---

## trade_executor.py

Responsibilities

- Execute AI recommendations
- Risk validation
- Position sizing
- Broker execution

These modules should reuse the existing MT5 Manager rather than communicate directly with MetaTrader5.

---

# 14. Extension Guidelines

When adding MT5 functionality

1. Extend the interface

↓

2. Implement in manager.py

↓

3. Add service integration

↓

4. Add scheduler support (if required)

↓

5. Add tests

↓

6. Update documentation

Future broker implementations should conform to the same interface to preserve portability.

---

# 15. Related Documents

Architecture

- 07_MT5_Integration.md
- 16_Background_Scheduler.md
- 18_Service_Layer.md

Implementation

- 27_Backend_Package_Reference.md
- 30_Service_Class_Reference.md
- 32_AI_Module_Reference.md

Operations

- 19_Deployment_Guide.md
- 20_Testing_Strategy.md
- 21_Logging_Observability.md

---

# MT5 Module Checklist

Before modifying the MT5 subsystem:

- [ ] Interface updated
- [ ] Manager implementation updated
- [ ] Error handling reviewed
- [ ] Logging verified
- [ ] Reconnection logic tested
- [ ] Scheduler integration verified
- [ ] Repository integration verified
- [ ] Unit tests updated
- [ ] Integration tests updated
- [ ] Documentation updated

---

# MT5 Module Dependency Matrix

| Module | Depends On | Returns |
|---------|------------|----------|
| manager.py | MetaTrader5, Configuration | Market Data, Account Info |
| interfaces.py | Python ABC / Protocols | Broker Contract |
| candle_collector.py | Manager, MarketRepository | Persisted Candles |

---

# Future Improvements

Future versions of this document should include:

- Complete MT5 API mapping
- Broker interface specification
- Sequence diagrams
- Connection state machine
- Retry timing diagrams
- Symbol synchronization strategy
- Multi-broker architecture
- Order execution workflow
- Position management workflow
- Performance benchmark results

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial MT5 Module Reference |

---

**Document End**

© Athena AI Terminal Project
