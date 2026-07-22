"""
Statistical historical insights — never AI-generated.
"""

from __future__ import annotations

from typing import Any

from app.models.learning import RecommendationOutcome
from app.models.recommendation import Recommendation


def _win_rate(outcomes: list[RecommendationOutcome]) -> float | None:
    if not outcomes:
        return None
    wins = sum(1 for o in outcomes if o.label == "WIN")
    return 100.0 * wins / len(outcomes)


def _validation(rec: Recommendation) -> dict[str, Any]:
    validation = rec.validation or {}
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()
    return validation if isinstance(validation, dict) else {}


def _checklist_passed(rec: Recommendation, name: str) -> bool:
    checklist = rec.institutional_checklist or []
    if not isinstance(checklist, list):
        return False
    needle = name.lower()
    for item in checklist:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        if isinstance(item, dict) and str(item.get("name", "")).lower() == needle:
            return bool(item.get("passed"))
    return False


class HistoricalInsightsService:
    """
    Build deterministic insight strings from labeled similar/cohort trades.
    """

    def build(
        self,
        rows: list[tuple[Recommendation, float, RecommendationOutcome | None]],
    ) -> list[str]:
        labeled = [(rec, outcome) for rec, _, outcome in rows if outcome is not None]
        if len(labeled) < 5:
            return [
                "Insufficient labeled similar trades for statistical insights",
            ]

        insights: list[str] = []
        all_outcomes = [o for _, o in labeled]
        baseline = _win_rate(all_outcomes)
        if baseline is None:
            return insights

        # BOS + HTF-ish: bos validated
        bos_outcomes = [
            o for rec, o in labeled if _validation(rec).get("bos")
        ]
        bos_rate = _win_rate(bos_outcomes)
        if bos_rate is not None and len(bos_outcomes) >= 5:
            insights.append(
                f"Trades with BOS confirmation win {bos_rate:.0f}% "
                f"(n={len(bos_outcomes)})",
            )

        # Trend validated as HTF/trend alignment proxy
        trend_outcomes = [
            o for rec, o in labeled if _validation(rec).get("trend")
        ]
        trend_rate = _win_rate(trend_outcomes)
        if trend_rate is not None and len(trend_outcomes) >= 5:
            insights.append(
                f"Trades with HTF/trend alignment win {trend_rate:.0f}%",
            )

        # Liquidity sweep
        with_liq = [
            o
            for rec, o in labeled
            if _validation(rec).get("liquidity")
            or _checklist_passed(rec, "Liquidity Sweep")
        ]
        without_liq = [
            o
            for rec, o in labeled
            if not (
                _validation(rec).get("liquidity")
                or _checklist_passed(rec, "Liquidity Sweep")
            )
        ]
        with_rate = _win_rate(with_liq)
        without_rate = _win_rate(without_liq)
        if (
            with_rate is not None
            and without_rate is not None
            and len(with_liq) >= 5
            and len(without_liq) >= 5
        ):
            delta = with_rate - without_rate
            direction = "improve" if delta >= 0 else "reduce"
            insights.append(
                f"Liquidity presence {direction}s win rate by {abs(delta):.0f}%",
            )

        # News filter failed => high impact / blocked
        news_ok = [o for rec, o in labeled if _validation(rec).get("news")]
        news_bad = [o for rec, o in labeled if not _validation(rec).get("news")]
        ok_rate = _win_rate(news_ok)
        bad_rate = _win_rate(news_bad)
        if (
            ok_rate is not None
            and bad_rate is not None
            and len(news_bad) >= 5
            and len(news_ok) >= 5
        ):
            delta = ok_rate - bad_rate
            if delta > 0:
                insights.append(
                    f"Trades during adverse/high-impact news perform "
                    f"{delta:.0f}% worse than filtered trades",
                )
            else:
                insights.append(
                    f"News filter cohort win rate {ok_rate:.0f}% vs "
                    f"{bad_rate:.0f}% without filter",
                )

        # RR above 2.5
        high_rr = [
            (rec, o) for rec, o in labeled if float(rec.risk_reward or 0) >= 2.5
        ]
        high_rr_outcomes = [o for _, o in high_rr]
        high_rr_rate = _win_rate(high_rr_outcomes)
        if high_rr_rate is not None and len(high_rr_outcomes) >= 5:
            # Profitability proxy: mean pnl
            mean_pnl = sum(float(o.pnl_proxy) for o in high_rr_outcomes) / len(
                high_rr_outcomes
            )
            base_pnl = sum(float(o.pnl_proxy) for o in all_outcomes) / len(all_outcomes)
            if mean_pnl > base_pnl:
                insights.append(
                    "RR above 2.5 historically increases profitability vs cohort",
                )
            else:
                insights.append(
                    f"RR ≥ 2.5 cohort win rate {high_rr_rate:.0f}% (n={len(high_rr_outcomes)})",
                )

        if not insights:
            insights.append(
                f"Cohort baseline win rate {baseline:.0f}% across {len(labeled)} similar trades",
            )

        return insights[:6]


historical_insights_service = HistoricalInsightsService()
