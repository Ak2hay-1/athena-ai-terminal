# Trade Probability Engine

Deterministic success estimation for Athena recommendations. **No LLMs** are used.

## Pipeline

After institutional enrichments (confidence breakdown, checklist, heatmap, entry zone):

1. **Historical Similarity** — score labeled peers (same symbol / timeframe / signal)
2. **Trade Probability** — empirical win rate (+ optional logistic blend)
3. **Trade Quality** — composite 0–100 grade
4. **Historical Insights** — statistical template strings
5. Persist on `recommendations` and expose via API / detail UI

## Probability formula

Primary:

```
historical_win_rate_smoothed = (wins + 1) / (n + 2)   # Laplace
```

When `similar_trades >= PROBABILITY_BLEND_MIN` and a trained `SignalModel` v2 file exists:

```
probability = 0.7 * similar_win_rate + 0.3 * lr_predict_proba
```

Otherwise probability = smoothed similar win rate only.

If `similar_trades < PROBABILITY_LOW_SAMPLE` → `confidence_category = LOW_SAMPLE`
(still returns the empirical rate; does not invent certainty).

## Logistic Regression (SignalModel v2)

Training features (`FEATURE_ORDER`) are taken from the parent recommendation **before** outcome labels:

- confluence
- rsi
- macd_bullish
- news_score
- multi_tf_bullish

Labels come from `recommendation_outcomes`. Stale v1 models (label-leaked features) are ignored at predict time when feature size mismatches.

## Similarity weights (defaults)

| Factor    | Weight |
|-----------|--------|
| Trend     | 25%    |
| Structure | 20%    |
| Liquidity | 15%    |
| Momentum  | 15%    |
| News      | 10%    |
| ATR       | 10%    |
| Risk      | 5%     |

Candidates are filtered in SQL (`symbol`, `timeframe`, `signal`) with limit `PROBABILITY_CANDIDATE_LIMIT`, then scored in-process. Top 20 returned.

## APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/recommendations/{id}` | By id |
| GET | `/api/v1/recommendations/{id}/similar` | Similar historical |
| GET | `/api/v1/recommendations/{id}/comparison/{other_id}` | Side-by-side compare |

Existing `latest` / `history` responses include probability fields when present.

## Settings

See `backend/.env.example`:

- `PROBABILITY_LOW_SAMPLE`
- `PROBABILITY_BLEND_MIN`
- `PROBABILITY_CANDIDATE_LIMIT`
- `PROBABILITY_SIMILAR_TOP_N`
- `SIMILARITY_WEIGHT_*`

## Migration

```bash
cd backend
alembic upgrade head
```

Revision: `a3b4c5d6e7f8_add_trade_probability_fields`.
