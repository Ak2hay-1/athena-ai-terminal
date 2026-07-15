# Athena AI Terminal
# Pattern Engine

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Pattern Engine |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Quantitative Analysts, Trading Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Objectives
3. Pattern Engine Architecture
4. Pattern Processing Pipeline
5. Folder Structure
6. Pattern Detection Lifecycle
7. Supported Patterns
8. Swing Detection
9. Break of Structure (BOS)
10. Change of Character (CHOCH)
11. Fair Value Gap (FVG)
12. Order Blocks
13. Liquidity Zones
14. Premium / Discount Zones
15. Trend Structure
16. Pattern Aggregation
17. Pattern Confidence
18. Multi-Timeframe Analysis
19. Integration with Indicator Engine
20. Integration with Market Analysis
21. Integration with AI
22. Error Handling
23. Logging
24. Performance
25. Future Enhancements
26. Best Practices
27. Related Documents

---

# 1. Introduction

The Pattern Engine identifies Smart Money Concepts (SMC) and advanced price-action structures from historical market data.

Unlike traditional indicator-based systems, the Pattern Engine attempts to identify institutional trading behaviour through structural analysis.

Pattern detection provides higher-level market context that complements technical indicators.

---

# 2. Objectives

The Pattern Engine is responsible for:

- Detecting market structure
- Identifying institutional footprints
- Finding liquidity areas
- Detecting imbalance
- Supporting AI recommendations
- Improving trade confluence

It does **not** generate trading signals directly.

---

# 3. Pattern Engine Architecture

```
Historical Candles

↓

Indicator Engine

↓

Swing Detection

↓

Pattern Detection

↓

Pattern Aggregation

↓

Market Analysis Engine

↓

AI Recommendation Engine
```

---

# 4. Pattern Processing Pipeline

```mermaid
flowchart TD

Candles

-->

Swing Detector

-->

BOS

-->

CHOCH

-->

FVG

-->

Liquidity

-->

Order Block

-->

Premium Discount

-->

Trend Structure

-->

Pattern Results
```

Each detector operates independently and contributes structured results.

---

# 5. Folder Structure

```
app/

└── patterns/

    ├── swing_detector.py
    ├── break_of_structure.py
    ├── bos.py
    ├── change_of_character.py
    ├── choch.py
    ├── fair_value_gap.py
    ├── fvg.py
    ├── liquidity.py
    ├── order_block.py
    ├── premium_discount.py
    ├── trend_structure.py
    ├── market_analyzer.py
    └── __init__.py
```

Each module has a single responsibility.

---

# 6. Pattern Detection Lifecycle

1. Load validated candles
2. Detect swing highs/lows
3. Determine trend structure
4. Detect structural breaks
5. Detect imbalance
6. Detect liquidity
7. Aggregate findings
8. Return structured pattern data

---

# 7. Supported Patterns

Current implementation:

| Pattern | Purpose |
|----------|---------|
| Swing High/Low | Market pivots |
| BOS | Trend continuation |
| CHOCH | Trend reversal |
| FVG | Market imbalance |
| Order Block | Institutional zones |
| Liquidity | Stop clusters |
| Premium / Discount | Value zones |
| Trend Structure | Overall direction |

---

# 8. Swing Detection

Primary file:

```
swing_detector.py
```

Purpose:

Detect significant highs and lows.

Outputs:

- Swing High
- Swing Low
- Pivot Index
- Pivot Price

Swing detection is the foundation for most other patterns.

---

# 9. Break of Structure (BOS)

Primary files:

```
bos.py

break_of_structure.py
```

Purpose:

Detect continuation of an existing trend.

Typical workflow:

```
Swing High

↓

Price closes above

↓

Bullish BOS
```

or

```
Swing Low

↓

Price closes below

↓

Bearish BOS
```

Outputs:

- Direction
- Price
- Candle Index
- Timestamp

---

# 10. Change of Character (CHOCH)

Primary files:

```
choch.py

change_of_character.py
```

Purpose:

Identify potential trend reversals.

Example:

```
Uptrend

↓

Lower Low

↓

CHOCH

↓

Possible Downtrend
```

Outputs:

- Direction
- Break Level
- Confirmation Candle

---

# 11. Fair Value Gap (FVG)

Primary files:

```
fair_value_gap.py

fvg.py
```

Purpose:

Identify market imbalance.

Bullish FVG

```
High(Candle 1)

<

Low(Candle 3)
```

Bearish FVG

```
Low(Candle 1)

>

High(Candle 3)
```

Outputs:

- Gap Start
- Gap End
- Direction
- Status (Open/Filled)

---

# 12. Order Blocks

Primary file:

```
order_block.py
```

Purpose:

Detect institutional accumulation/distribution zones.

Attributes:

- Bullish/Bearish
- High
- Low
- Strength
- Status

Future enhancements:

- Mitigated
- Invalidated
- Tested count

---

# 13. Liquidity Zones

Primary file:

```
liquidity.py
```

Purpose:

Locate clustered stop-loss areas.

Examples:

- Equal highs
- Equal lows
- Liquidity sweeps

Outputs:

- Zone
- Direction
- Strength

---

# 14. Premium / Discount Zones

Primary file:

```
premium_discount.py
```

Purpose:

Divide the trading range into value areas.

```
Range High

↓

Midpoint

↓

Premium

↓

Discount
```

Outputs:

- Range High
- Range Low
- Midpoint
- Current Zone

---

# 15. Trend Structure

Primary file:

```
trend_structure.py
```

Purpose:

Determine overall market direction.

Possible states:

- Bullish
- Bearish
- Range

Trend is consumed by both the Analysis Engine and AI Engine.

---

# 16. Pattern Aggregation

Pattern outputs are combined into a single structured object.

Example:

```json
{
  "trend": "Bullish",
  "bos": true,
  "choch": false,
  "order_block": true,
  "fvg": true,
  "liquidity": "Above Price"
}
```

This summary becomes the input for the Market Analysis Engine.

---

# 17. Pattern Confidence

Future versions may assign confidence scores based on:

- Pattern age
- Number of confirmations
- Timeframe
- Volume
- Trend alignment
- Indicator confluence

Confidence can help rank trade setups.

---

# 18. Multi-Timeframe Analysis

Pattern detection is performed independently for each timeframe.

Supported:

- M1
- M5
- M15
- M30
- H1
- H4
- D1

Future versions will aggregate higher-timeframe and lower-timeframe signals into a unified market view.

---

# 19. Integration with Indicator Engine

The Pattern Engine consumes indicator outputs where relevant.

Examples:

- EMA trend filter
- ATR volatility filter
- Volume confirmation

Indicators and patterns complement each other but remain separate modules.

---

# 20. Integration with Market Analysis

Pattern results are passed to the Market Analysis Engine, which combines them with:

- Indicators
- Trend
- Volatility
- Risk metrics

The result is a structured market summary.

---

# 21. Integration with AI

The AI receives a concise representation of detected patterns rather than raw candle data.

Example prompt section:

```
Trend: Bullish

BOS: Bullish

CHOCH: None

Order Block: Bullish

Liquidity: Above Price

FVG: Open Bullish Gap
```

This reduces prompt size and improves consistency.

---

# 22. Error Handling

Potential issues:

- Empty dataset
- Insufficient candles
- Missing swing points
- Invalid OHLC values
- Conflicting pattern results

Pattern detectors should validate inputs and fail gracefully.

---

# 23. Logging

Pattern logs include:

- Detector start
- Detector completion
- Number of patterns found
- Execution time
- Validation failures

Example:

```text
Swing Detector: 24 pivots found.

BOS Detector: 3 bullish, 1 bearish.

FVG Detector: 5 active gaps.
```

---

# 24. Performance

Current optimizations:

- Vectorized calculations
- Shared DataFrame
- Reusable swing points

Future optimizations:

- Incremental updates
- Pattern caching
- Parallel detection
- Multi-core execution

---

# 25. Future Enhancements

Planned features:

- Breaker Blocks
- Mitigation Blocks
- Inducement
- SMT Divergence
- Volume Profile
- Market Maker Buy/Sell Models
- Liquidity Heatmaps
- Pattern confidence scoring
- User-configurable detectors

---

# 26. Best Practices

- Keep one detector per file.
- Do not duplicate calculations.
- Keep detectors deterministic.
- Document assumptions.
- Validate all inputs.
- Return structured outputs.
- Write unit tests for each detector.

---

# 27. Related Documents

- 05_Backend_Architecture.md
- 08_AI_Architecture.md
- 09_Indicator_Engine.md
- 11_Market_Analysis_Engine.md
- 12_Recommendation_Engine.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Pattern Engine documentation |

---

**Document End**

© Athena AI Terminal Project
