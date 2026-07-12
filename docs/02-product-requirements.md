# Athena AI Terminal

## Product Requirements Document (PRD)

**Version:** 1.0

**Project Owner:** Akshay Patil

**Status:** Planning

---

# 1. Executive Summary

Athena AI Terminal is an AI-powered trading platform designed to help traders analyze financial markets using technical analysis, market structure, news analysis, and local AI models.

The initial version focuses on **XAUUSD (Gold)** while maintaining an architecture that can support additional markets in the future.

The system is designed to assist traders by providing transparent analysis and paper-trading capabilities before any live trading features are considered.

---

# 2. Problem Statement

Retail traders often use multiple disconnected tools:

* MetaTrader 5 for charts
* News websites for economic events
* TradingView for analysis
* Telegram for alerts
* Excel for trade journals

Switching between multiple applications slows decision-making and makes trade tracking difficult.

---

# 3. Solution

Athena AI Terminal combines these workflows into one platform.

It will:

* Collect live market data
* Calculate technical indicators
* Detect market structure
* Analyze financial news
* Generate AI-assisted trade analysis
* Record every trading decision
* Support paper trading
* Display everything in a single dashboard

---

# 4. Target Users

Primary Users:

* Beginner traders
* Intermediate traders
* Swing traders
* Intraday traders
* Personal trading projects

Future Users:

* Professional traders
* Trading teams
* Quantitative researchers

---

# 5. Goals

## Business Goals

* Build a professional portfolio project.
* Learn modern backend and frontend development.
* Learn AI integration.
* Create a maintainable software platform.

## Technical Goals

* Modular architecture
* Scalable codebase
* Local AI support
* Fast API responses
* Reliable market data collection

---

# 6. Version 1 Scope (MVP)

Version 1 will include:

### Backend

* FastAPI
* REST APIs
* Logging
* Configuration
* PostgreSQL

### Market Data

* MetaTrader 5 connection
* Live candles
* Live ticks
* Symbol management

### Analysis

* EMA
* RSI
* MACD
* ATR
* Bollinger Bands

### Market Structure

* Trend detection
* Support & Resistance
* Break of Structure (BOS)
* Change of Character (CHOCH)

### AI

* Local Ollama integration
* Market summary
* Trade explanation
* Confidence score

### Trading

* Paper trading only
* Trade journal
* Performance statistics

### Dashboard

* Live chart
* Indicator values
* AI analysis
* Trade history

### Notifications

* Telegram alerts

---

# 7. Out of Scope (Version 1)

The following features are intentionally excluded from the first release:

* Automatic live trading
* Cloud deployment
* Multi-user authentication
* Mobile application
* Multiple broker integrations
* Social trading
* Copy trading
* Portfolio optimization

These features may be added in future versions.

---

# 8. Functional Requirements

The system must:

* Connect to MetaTrader 5.
* Receive live market data.
* Store historical market data.
* Calculate technical indicators.
* Analyze market structure.
* Generate AI-assisted analysis.
* Execute paper trades.
* Record trade history.
* Display live information on the dashboard.
* Send Telegram notifications.

---

# 9. Non-Functional Requirements

* Modular architecture
* Easy to maintain
* Secure configuration
* Responsive user interface
* Structured logging
* Comprehensive error handling
* Extensible design

---

# 10. Success Criteria

Version 1 is successful when the platform can:

* Display live XAUUSD data.
* Calculate indicators correctly.
* Produce AI market summaries.
* Simulate trades through paper trading.
* Maintain a complete trade journal.
* Present all information in a responsive dashboard.

---

# 11. Future Roadmap

Future versions may include:

* Live trading
* Multiple symbols
* Multiple brokers
* Strategy builder
* AI strategy optimization
* Portfolio management
* Cloud deployment
* User accounts
* Mobile application

---

# 12. Definition of Done

Version 1 is complete when:

* All planned modules are implemented.
* Core features are tested.
* Documentation is complete.
* The application runs locally from a fresh clone using the setup guide.
