# Athena AI Terminal
# Recommendation Engine

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Recommendation Engine |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, AI Engineers, Trading Engineers, Architects, AI Assistants |

---

# Table of Contents

1. Introduction
2. Objectives
3. Design Philosophy
4. Recommendation Architecture
5. Recommendation Lifecycle
6. Engine Workflow
7. Inputs
8. Decision Pipeline
9. Signal Generation
10. Entry Price Calculation
11. Stop Loss Calculation
12. Take Profit Calculation
13. Risk/Reward Validation
14. Confidence Scoring
15. AI Integration
16. Recommendation Validation
17. Persistence
18. Duplicate Prevention
19. Recommendation States
20. Scheduler Integration
21. REST API Integration
22. WebSocket Integration
23. Error Handling
24. Logging
25. Performance
26. Future Enhancements
27. Best Practices
28. Related Documents

---

# 1. Introduction

The Recommendation Engine is Athena's final decision-making layer.

Every market analysis eventually reaches this engine.

The Recommendation Engine evaluates:

- Market Trend
- Technical Indicators
- Smart Money Concepts
- Risk
- Volatility
- AI Interpretation

before generating a recommendation.

---

# 2. Objectives

The Recommendation Engine must:

- Produce consistent recommendations
- Reject poor-quality setups
- Validate AI responses
- Calculate risk parameters
- Store recommendations
- Stream live recommendations
- Support future automated execution

---

# 3. Design Philosophy

The engine follows these principles.

• Deterministic preprocessing

• AI-assisted reasoning

• Explainable output

• Strict validation

• Risk-first approach

• Provider independence

---

# 4. Recommendation Architecture

```text
Market Data

↓

Indicator Engine

↓

Pattern Engine

↓

Market Analysis

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

Repository

↓

Database

↓

REST API

↓

Frontend
```

---

# 5. Recommendation Lifecycle

```mermaid
flowchart TD

Candles

-->

Indicators

-->

Patterns

-->

Market Summary

-->

AI Recommendation

-->

Validation

-->

Risk Validation

-->

Save Database

-->

Broadcast
```

---

# 6. Engine Workflow

1. Receive Market Summary
2. Validate data
3. Build AI prompt
4. Request AI recommendation
5. Parse AI response
6. Validate fields
7. Calculate risk
8. Verify risk/reward
9. Persist recommendation
10. Broadcast recommendation

---

# 7. Inputs

The engine consumes structured data only.

Market inputs include:

- Symbol
- Timeframe
- Trend
- Momentum
- Volatility
- EMA
- RSI
- MACD
- ATR
- BOS
- CHOCH
- FVG
- Liquidity
- Order Blocks
- Premium / Discount
- Support
- Resistance

No raw OHLC data is required once the Market Summary has been generated.

---

# 8. Decision Pipeline

```mermaid
flowchart TD

Market Summary

-->

Prompt Builder

-->

AI Client

-->

Response Parser

-->

Recommendation Validation

-->

Risk Validation

-->

Repository

-->

Frontend
```

---

# 9. Signal Generation

Supported recommendation signals:

| Signal | Meaning |
|----------|---------|
| BUY | Long opportunity |
| SELL | Short opportunity |
| HOLD | No trade recommended |

The engine should never return undefined signals.

---

# 10. Entry Price Calculation

Entry may be:

Current market price

or

AI suggested price

Future enhancements:

- Pullback entries
- Limit entries
- Stop entries

---

# 11. Stop Loss Calculation

Stop Loss should consider:

- ATR
- Swing High
- Swing Low
- Order Block
- Liquidity

Priority:

```
Market Structure

↓

ATR

↓

Fallback Distance
```

Future:

Dynamic ATR multipliers.

---

# 12. Take Profit Calculation

Take Profit should consider:

- Risk/Reward
- Liquidity
- Support
- Resistance
- Previous Highs
- Previous Lows

Possible strategies:

Fixed RR

Dynamic RR

Structure Based

---

# 13. Risk/Reward Validation

Example validation:

```
Risk

=

Entry

-

Stop Loss

Reward

=

Take Profit

-

Entry

Risk Reward

=

Reward / Risk
```

Minimum configurable ratio:

```
2.0
```

Recommendations below the configured threshold should be rejected or downgraded.

---

# 14. Confidence Scoring

Confidence combines:

- AI confidence
- Indicator alignment
- Pattern confluence
- Trend quality
- Volatility

Example:

| Confidence | Interpretation |
|------------|----------------|
| 0–40 | Weak |
| 41–60 | Moderate |
| 61–80 | Strong |
| 81–100 | Exceptional |

Future versions may compute confidence independently of the AI.

---

# 15. AI Integration

The Recommendation Engine communicates with the AI subsystem through:

```
Prompt Builder

↓

AI Client

↓

Response Parser
```

The engine never communicates directly with the LLM.

---

# 16. Recommendation Validation

Validation rules include:

- Signal must be BUY, SELL or HOLD
- Confidence must be within range
- Stop Loss must be logical
- Take Profit must be logical
- Risk/Reward must meet configuration
- Required fields must exist

Invalid recommendations should never be stored.

---

# 17. Persistence

Recommendations are stored in PostgreSQL.

Typical fields include:

- Symbol
- Timeframe
- Signal
- Confidence
- Entry
- Stop Loss
- Take Profit
- Risk Reward
- Trend
- Confluence
- Reasoning
- Created At

---

# 18. Duplicate Prevention

The engine should avoid creating duplicate recommendations.

Possible duplicate criteria:

- Same symbol
- Same timeframe
- Same signal
- Same candle
- Same entry

Future improvements:

Recommendation hashing.

---

# 19. Recommendation States

Possible lifecycle states:

```
Generated

↓

Validated

↓

Stored

↓

Broadcast

↓

Archived
```

Future states:

- Executed
- Expired
- Cancelled
- Closed

---

# 20. Scheduler Integration

Current workflow:

```
Every Minute

↓

Collect Candles

↓

Market Analysis

↓

Recommendation Engine

↓

Database
```

Future:

Multi-symbol scheduling.

---

# 21. REST API Integration

Recommendations are available through REST endpoints.

Typical operations:

- Latest recommendation
- Recommendation history
- Symbol filter
- Timeframe filter

---

# 22. WebSocket Integration

New recommendations are broadcast to connected clients.

Typical payload:

```json
{
  "symbol": "XAUUSD",
  "timeframe": "M1",
  "signal": "BUY",
  "confidence": 82
}
```

---

# 23. Error Handling

Possible failures:

- AI unavailable
- Invalid JSON
- Missing fields
- Invalid signal
- Invalid prices
- Database failure

Recovery strategy:

- Log error
- Generate fallback recommendation
- Prevent application crash

---

# 24. Logging

Typical log events:

```
Recommendation Started

Prompt Generated

AI Response Received

Validation Passed

Recommendation Stored

Broadcast Completed
```

Log additional metrics:

- Execution time
- Model used
- Confidence
- Risk/Reward

---

# 25. Performance

Current optimizations:

- Compact prompts
- Structured responses
- Minimal database writes
- Shared market summaries

Future improvements:

- Response caching
- Batch processing
- Incremental analysis

---

# 26. Future Enhancements

Planned features:

- Portfolio-aware recommendations
- Position sizing
- Trade management
- Auto execution
- Multi-agent AI review
- Recommendation versioning
- Recommendation ranking
- Trade outcome feedback
- Reinforcement learning

---

# 27. Best Practices

- Validate every recommendation.
- Never trust raw AI output.
- Keep business rules deterministic.
- Separate AI logic from risk logic.
- Store reasoning for auditability.
- Prevent duplicate recommendations.
- Make thresholds configurable.

---

# 28. Related Documents

- 08_AI_Architecture.md
- 09_Indicator_Engine.md
- 10_Pattern_Engine.md
- 11_Market_Analysis_Engine.md
- 13_REST_API.md
- 14_WebSocket_Architecture.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Recommendation Engine documentation |

---

**Document End**

© Athena AI Terminal Project
