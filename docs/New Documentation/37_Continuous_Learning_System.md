# Continuous Learning System

Athena learns from labeled recommendation outcomes with **deterministic**, explainable, versioned updates. No LLMs. Historical recommendation rows are never rewritten.

## Pipeline

```text
Recommendation FINAL (RiskEngine signal/levels)
        ↓
RegimeClassifier + audit versions + pattern/confluence snapshots
        ↓
OutcomeTracker (TP_HIT / SL_HIT / MANUAL_EXIT / TIMEOUT)
        ↓
Analytics aggregators (feature / symbol / TF / strategy / regime / calibration)
        ↓
AdaptiveWeightService (clamped confidence weights)
        ↓
ConfidenceEngine (future recommendations only)
```

## Non-decision boundary

| Owned by RiskEngine (unchanged rules) | Owned by Continuous Learning |
|---------------------------------------|------------------------------|
| Signal BUY/SELL/NO_TRADE | Outcome labels & exit result |
| Entry / SL / TP / RR gates | Feature / symbol / TF analytics |
| Structure validation | Versioned confidence **weights** |
| | Calibration dashboard |

Adaptive weights feed **ConfidenceEngine** for *future* scores only. They do not invent levels.

## Outcome rules

For each unlabeled BUY/SELL recommendation, scan subsequent candles (horizon = `LEARNING_OUTCOME_HORIZON_CANDLES`):

1. **SL_HIT** if stop is touched first (same-bar SL preferred over TP)
2. **TP_HIT** if take-profit is touched
3. **TIMEOUT** if neither within horizon (label WIN/LOSS/NEUTRAL from close vs entry)
4. **MANUAL_EXIT** if a closed `paper_positions` row links via `recommendation_id`

Stored fields include entry, sl, tp, rr, profit, duration_minutes, regime, confidence_at_entry, plus legacy `label` for SignalModel.

## Weight update formula

```text
lift = feature_win_rate − global_win_rate
delta = clamp(lift * LEARNING_WEIGHT_STEP * 10, ±MAX_STEP, +MAX_STEP)
weight' = clamp(weight + delta, MIN, MAX)
renormalize so Σ weights = 100
```

Requires `LEARNING_WEIGHT_MIN_SAMPLES`. Each update writes `weight_history` + `learning_versions` and deactivates the previous active row.

## Schedule (`NewsScheduler`)

| Job | Setting |
|-----|---------|
| Outcome labeling | `LEARNING_LABEL_INTERVAL_SECONDS` |
| Analytics refresh | `LEARNING_ANALYTICS_INTERVAL_SECONDS` |
| Weight update | `LEARNING_WEIGHT_UPDATE_INTERVAL_HOURS` |
| SignalModel retrain | `LEARNING_RETRAIN_INTERVAL_HOURS` |

Gated by `LEARNING_ENABLED`.

## APIs

| Method | Path |
|--------|------|
| GET | `/api/v1/learning/dashboard` |
| GET | `/api/v1/learning/features` |
| GET | `/api/v1/learning/symbols` |
| GET | `/api/v1/learning/timeframes` |
| GET | `/api/v1/learning/regimes` |
| GET | `/api/v1/learning/calibration` |
| GET | `/api/v1/learning/weights` |
| GET | `/api/v1/learning/history` |
| GET | `/api/v1/learning/stats` |
| POST | `/api/v1/learning/label` |
| POST | `/api/v1/learning/refresh-analytics` |
| POST | `/api/v1/learning/update-weights` |
| POST | `/api/v1/learning/retrain` |

## Frontend

`/learning` — dashboard with win rate, profit factor, calibration, feature/symbol/TF/regime analytics, and weight evolution.

## Migration

`b4c5d6e7f8a9_continuous_learning_system.py` — outcome enrichment, stats tables, weight history, recommendation audit columns, `paper_positions.recommendation_id`.

## Code map

| Concern | Path |
|---------|------|
| OutcomeTracker | `backend/app/services/learning/outcome_tracker.py` |
| RegimeClassifier | `backend/app/learning/regime_classifier.py` |
| Adaptive weights | `backend/app/services/learning/adaptive_weight_service.py` |
| Analytics services | `backend/app/services/learning/*_analytics_service.py` |
| Orchestration | `backend/app/services/learning_service.py` |
| API | `backend/app/api/v1/learning.py` |
| Confidence injection | `backend/app/risk/confidence_engine.py`, `risk_engine.build_plan` |
