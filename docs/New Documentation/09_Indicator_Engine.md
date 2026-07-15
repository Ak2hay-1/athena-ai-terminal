# Athena AI Terminal
# Indicator Engine

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | Indicator Engine |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Quantitative Developers, Trading Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Indicator Engine Goals
3. Architecture
4. Indicator Workflow
5. Folder Structure
6. Supported Indicators
7. Indicator Pipeline
8. Indicator Lifecycle
9. Indicator Base Design
10. Indicator Calculations
11. Indicator Dependencies
12. Indicator Output Schema
13. Multi-Timeframe Support
14. Performance Optimizations
15. Error Handling
16. Logging
17. Extending the Indicator Engine
18. Future Enhancements
19. Best Practices
20. Related Documents

---

# 1. Introduction

The Indicator Engine is responsible for calculating all technical indicators used by Athena.

Indicators transform raw market data into structured numerical signals that are later consumed by:

- Pattern Engine
- Market Analysis Engine
- AI Recommendation Engine
- Risk Engine
- Backtesting Engine

The Indicator Engine does **not** generate trading signals directly.

Its sole purpose is to calculate reliable market metrics.

---

# 2. Indicator Engine Goals

The Indicator Engine is designed with the following objectives:

- Accuracy
- Deterministic calculations
- High performance
- Independent modules
- Reusable outputs
- Multi-timeframe support
- Easy extensibility

---

# 3. Architecture

```text
Market Candles

↓

Validation

↓

Indicator Engine

↓

Individual Indicators

↓

Indicator Results

↓

Market Analysis Engine
```

Each indicator operates independently.

---

# 4. Indicator Workflow

```mermaid
flowchart TD

Candles

-->

EMA

-->

RSI

-->

MACD

-->

ATR

-->

Volume

-->

Indicator Results

-->

Analysis Engine
```

---

# 5. Folder Structure

```
app/

└── indicators/

    ├── ema.py
    ├── rsi.py
    ├── macd.py
    ├── atr.py
    ├── volume.py
    ├── moving_average.py
    ├── __init__.py
```

Each file implements a single indicator.

---

# 6. Supported Indicators

Current implementation:

| Indicator | Purpose |
|------------|---------|
| EMA | Trend detection |
| RSI | Momentum |
| MACD | Momentum & trend |
| ATR | Volatility |
| Volume | Market participation |

Future indicators:

- Bollinger Bands
- VWAP
- ADX
- Stochastic RSI
- SuperTrend
- Ichimoku Cloud
- OBV
- CCI
- Donchian Channels
- Keltner Channels

---

# 7. Indicator Pipeline

```text
Database Candles

↓

Load DataFrame

↓

Validate

↓

Calculate EMA

↓

Calculate RSI

↓

Calculate MACD

↓

Calculate ATR

↓

Calculate Volume

↓

Return Enriched DataFrame
```

The pipeline should preserve the original candle data while appending indicator columns.

---

# 8. Indicator Lifecycle

1. Load candles
2. Validate data
3. Ensure sufficient history
4. Execute indicator calculation
5. Append result columns
6. Return enriched dataset
7. Pass to Pattern Engine

---

# 9. Indicator Base Design

Each indicator should follow the same interface.

Example:

```python
class Indicator:
    def calculate(self, dataframe):
        ...
```

Responsibilities:

- Accept a DataFrame
- Perform calculation
- Return updated DataFrame
- Avoid side effects

---

# 10. Indicator Calculations

## EMA (Exponential Moving Average)

Purpose:

Measure market trend.

Typical periods:

- EMA 20
- EMA 50
- EMA 200

Output:

```text
ema_20

ema_50

ema_200
```

---

## RSI (Relative Strength Index)

Purpose:

Measure momentum.

Range:

0 – 100

Typical interpretation:

- Above 70 → Overbought
- Below 30 → Oversold

Output:

```text
rsi
```

---

## MACD

Components:

- MACD Line
- Signal Line
- Histogram

Output:

```text
macd

macd_signal

macd_histogram
```

---

## ATR (Average True Range)

Purpose:

Market volatility.

Uses:

- Stop loss calculation
- Volatility analysis
- Risk management

Output:

```text
atr
```

---

## Volume

Metrics:

- Tick Volume
- Real Volume
- Relative Volume (future)

Output:

```text
volume
```

---

# 11. Indicator Dependencies

Indicators should not depend on one another unless mathematically required.

Dependency graph:

```text
Candles

↓

EMA

↓

RSI

↓

MACD

↓

ATR

↓

Volume
```

Each indicator should remain independently testable.

---

# 12. Indicator Output Schema

The enriched DataFrame should include:

```text
timestamp

open

high

low

close

volume

ema_20

ema_50

ema_200

rsi

macd

macd_signal

macd_histogram

atr
```

No original candle data should be removed.

---

# 13. Multi-Timeframe Support

The Indicator Engine supports all configured timeframes.

Examples:

- M1
- M5
- M15
- M30
- H1
- H4
- D1

Indicator calculations are independent for each timeframe.

---

# 14. Performance Optimizations

Current strategies:

- Vectorized Pandas operations
- Batch calculations
- Minimal DataFrame copying

Future optimizations:

- NumPy acceleration
- Numba JIT compilation
- Parallel execution
- Incremental updates
- Cached calculations

---

# 15. Error Handling

Possible issues:

- Empty dataset
- Insufficient candles
- Missing OHLC columns
- NaN values
- Invalid data types

Each indicator should:

- Validate inputs
- Raise meaningful exceptions
- Log failures
- Avoid corrupting the DataFrame

---

# 16. Logging

Indicator logs include:

- Indicator start
- Indicator completion
- Execution time
- Data size
- Errors

Example:

```text
Calculating EMA(20)...

EMA calculation completed in 4 ms.
```

---

# 17. Extending the Indicator Engine

To add a new indicator:

1. Create a new file in `app/indicators/`
2. Implement the standard interface
3. Add unit tests
4. Register the indicator in the pipeline
5. Update documentation
6. Verify AI prompt integration

---

# 18. Future Enhancements

Planned features:

- Indicator caching
- Dynamic indicator configuration
- User-defined indicators
- GPU acceleration
- Plugin architecture
- Indicator versioning
- Real-time incremental calculations

---

# 19. Best Practices

- Keep one indicator per file.
- Avoid modifying original candle values.
- Use vectorized calculations.
- Validate all inputs.
- Return deterministic results.
- Document formulas and assumptions.
- Add tests for every indicator.

---

# 20. Related Documents

- 05_Backend_Architecture.md
- 07_MT5_Integration.md
- 08_AI_Architecture.md
- 10_Pattern_Engine.md
- 11_Market_Analysis_Engine.md
- 12_Recommendation_Engine.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial Indicator Engine documentation |

---

**Document End**

© Athena AI Terminal Project
