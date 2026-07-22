"""
Recommendation Repository.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection
from app.models.recommendation import Recommendation
from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """
    Repository for Recommendation model.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(
            db=db,
            model=Recommendation,
        )

    _NON_ACTIONABLE = frozenset(
        {
            RecommendationSignal.HOLD,
            RecommendationSignal.NO_TRADE,
        }
    )

    # Prefer mid/higher TFs when scores tie (less noise than M1).
    _TF_RANK = {
        "D1": 70,
        "H4": 60,
        "H1": 50,
        "M30": 40,
        "M15": 30,
        "M5": 20,
        "M1": 10,
    }

    def get_latest(
        self,
        symbol: str,
        timeframe: str | None = None,
    ) -> Recommendation | None:
        """
        Get latest recommendation.

        When ``timeframe`` is omitted, returns the best overall setup for the
        symbol across all timeframes (actionable preferred).
        """

        if not timeframe:
            return self.get_best_for_symbol(symbol)

        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol.upper().strip(),
                Recommendation.timeframe == timeframe.upper().strip(),
            )
            .order_by(
                desc(Recommendation.created_at)
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_active_setup(
        self,
        symbol: str,
        timeframe: str,
    ) -> Recommendation | None:
        """Latest non-terminal setup for symbol/timeframe (lifecycle aware)."""
        terminal = ("EXPIRED", "INVALIDATED", "TP", "SL", "EXECUTED")
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol.upper().strip(),
                Recommendation.timeframe == timeframe.upper().strip(),
            )
            .order_by(desc(Recommendation.updated_at), desc(Recommendation.created_at))
            .limit(1)
        )
        row = self.db.scalar(stmt)
        if row is None:
            return None
        state = getattr(row, "lifecycle_state", None) or "ACTIVE"
        if state in terminal:
            return None
        # Treat recent BUY/SELL/HOLD as active even if lifecycle column missing/default
        signal = getattr(row.signal, "value", row.signal)
        if str(signal).upper() == "NO_TRADE" and state in terminal:
            return None
        if str(signal).upper() == "NO_TRADE":
            return None
        return row

    def list_active_actionable(
        self,
        *,
        exclude_symbol: str | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        """Active BUY/SELL recommendations across the book (one per symbol)."""
        from sqlalchemy import func

        subq = (
            select(
                Recommendation.symbol.label("symbol"),
                func.max(Recommendation.created_at).label("max_created"),
            )
            .where(
                Recommendation.signal.in_(
                    [RecommendationSignal.BUY, RecommendationSignal.SELL]
                )
            )
            .group_by(Recommendation.symbol)
            .subquery()
        )
        stmt = (
            select(Recommendation)
            .join(
                subq,
                (Recommendation.symbol == subq.c.symbol)
                & (Recommendation.created_at == subq.c.max_created),
            )
            .where(
                Recommendation.signal.in_(
                    [RecommendationSignal.BUY, RecommendationSignal.SELL]
                )
            )
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
        )
        rows = list(self.db.scalars(stmt).all())
        if exclude_symbol:
            ex = exclude_symbol.upper().strip()
            rows = [r for r in rows if (r.symbol or "").upper() != ex]
        # Filter terminal lifecycle
        terminal = {"EXPIRED", "INVALIDATED", "TP", "SL", "EXECUTED"}
        return [
            r
            for r in rows
            if (getattr(r, "lifecycle_state", None) or "ACTIVE") not in terminal
        ]

    def count_active_actionable(
        self,
        *,
        exclude_symbol: str | None = None,
    ) -> int:
        return len(self.list_active_actionable(exclude_symbol=exclude_symbol))

    @classmethod
    def _is_actionable(cls, signal: RecommendationSignal | str | None) -> bool:
        if signal is None:
            return False
        try:
            value = signal if isinstance(signal, RecommendationSignal) else RecommendationSignal(str(signal).upper())
        except ValueError:
            return False
        return value not in cls._NON_ACTIONABLE

    @classmethod
    def _scenario_sort_key(cls, row: Recommendation) -> tuple:
        """Higher tuple wins: actionable → confidence → confluence → quality → TF → recency."""
        created = row.created_at.timestamp() if row.created_at else 0.0
        tf = (row.timeframe or "").upper()
        return (
            1 if cls._is_actionable(row.signal) else 0,
            int(row.confidence or 0),
            int(row.confluence or 0),
            int(getattr(row, "trade_quality", 0) or 0),
            cls._TF_RANK.get(tf, 0),
            created,
        )

    def get_latest_per_timeframe(
        self,
        symbol: str,
    ) -> dict[str, Recommendation]:
        """Latest recommendation for each timeframe on a symbol."""
        from sqlalchemy import func

        sym = symbol.upper().strip()
        if not sym:
            return {}

        subq = (
            select(
                Recommendation.timeframe.label("timeframe"),
                func.max(Recommendation.created_at).label("max_created"),
            )
            .where(Recommendation.symbol == sym)
            .group_by(Recommendation.timeframe)
            .subquery()
        )
        stmt = select(Recommendation).join(
            subq,
            (Recommendation.timeframe == subq.c.timeframe)
            & (Recommendation.created_at == subq.c.max_created)
            & (Recommendation.symbol == sym),
        )
        rows = list(self.db.scalars(stmt).all())
        return {(row.timeframe or "").upper(): row for row in rows if row.timeframe}

    def get_best_for_symbol(
        self,
        symbol: str,
    ) -> Recommendation | None:
        """
        Best overall setup for a symbol across timeframes.

        Prefers actionable BUY/SELL over HOLD/NO_TRADE, then confidence /
        confluence / quality, with a mild higher-TF preference on ties.
        """
        by_tf = self.get_latest_per_timeframe(symbol)
        if not by_tf:
            return None
        return max(by_tf.values(), key=self._scenario_sort_key)

    def get_latest_for_symbols(
        self,
        symbols: list[str],
        timeframe: str | None = None,
    ) -> dict[str, Recommendation]:
        """
        Latest recommendation per symbol.

        When ``timeframe`` is set, scopes to that TF. When omitted, returns
        the best overall setup per symbol across all timeframes.
        """
        if not symbols:
            return {}

        normalized = [s.upper().strip() for s in symbols if s and s.strip()]
        if not normalized:
            return {}

        from sqlalchemy import func

        if timeframe:
            tf = timeframe.upper().strip()
            subq = (
                select(
                    Recommendation.symbol.label("symbol"),
                    func.max(Recommendation.created_at).label("max_created"),
                )
                .where(
                    Recommendation.symbol.in_(normalized),
                    Recommendation.timeframe == tf,
                )
                .group_by(Recommendation.symbol)
                .subquery()
            )
            stmt = select(Recommendation).join(
                subq,
                (Recommendation.symbol == subq.c.symbol)
                & (Recommendation.created_at == subq.c.max_created)
                & (Recommendation.timeframe == tf),
            )
            rows = list(self.db.scalars(stmt).all())
            return {row.symbol.upper(): row for row in rows}

        # Latest row per (symbol, timeframe), then pick best per symbol.
        subq = (
            select(
                Recommendation.symbol.label("symbol"),
                Recommendation.timeframe.label("timeframe"),
                func.max(Recommendation.created_at).label("max_created"),
            )
            .where(Recommendation.symbol.in_(normalized))
            .group_by(Recommendation.symbol, Recommendation.timeframe)
            .subquery()
        )
        stmt = select(Recommendation).join(
            subq,
            (Recommendation.symbol == subq.c.symbol)
            & (Recommendation.timeframe == subq.c.timeframe)
            & (Recommendation.created_at == subq.c.max_created),
        )
        rows = list(self.db.scalars(stmt).all())
        best: dict[str, Recommendation] = {}
        for row in rows:
            key = row.symbol.upper()
            current = best.get(key)
            if current is None or self._scenario_sort_key(row) > self._scenario_sort_key(current):
                best[key] = row
        return best

    def get_latest_signal(
        self,
        symbol: str,
        timeframe: str,
    ) -> Recommendation | None:
        """
        Return the latest actionable recommendation.
        """

        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol,
                Recommendation.timeframe == timeframe,
                Recommendation.signal.notin_(
                    [
                        RecommendationSignal.HOLD,
                        RecommendationSignal.NO_TRADE,
                    ]
                ),
            )
            .order_by(
                desc(Recommendation.created_at)
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_history(
        self,
        symbol: str | None,
        timeframe: str | None = None,
        limit: int = 100,
    ) -> list[Recommendation]:
        """
        Recommendation history.

        ``symbol`` and/or ``timeframe`` may be omitted to widen the query
        (e.g. all TFs for one symbol = overall scenario history).
        """

        stmt = select(Recommendation)
        if timeframe:
            stmt = stmt.where(Recommendation.timeframe == timeframe.upper().strip())
        if symbol:
            stmt = stmt.where(Recommendation.symbol == symbol.upper().strip())
        stmt = stmt.order_by(desc(Recommendation.created_at)).limit(limit)

        return list(self.db.scalars(stmt).all())

    def read(self, recommendation_id: int) -> Recommendation | None:
        """Read a recommendation by primary key."""
        return self.get_by_id(recommendation_id)

    def get_by_ids(self, ids: list[int]) -> list[Recommendation]:
        """Load recommendations by primary keys."""
        if not ids:
            return []
        stmt = select(Recommendation).where(Recommendation.id.in_(ids))
        return list(self.db.scalars(stmt).all())

    def get_candidates_for_similarity(
        self,
        symbol: str,
        timeframe: str,
        signal: str | None = None,
        exclude_id: int | None = None,
        limit: int = 500,
    ) -> list[Recommendation]:
        """
        Candidate pool for similarity scoring (indexed filter).
        """
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.symbol == symbol.upper(),
                Recommendation.timeframe == timeframe.upper(),
            )
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
        )
        if signal:
            try:
                signal_enum = RecommendationSignal(signal.upper())
                stmt = stmt.where(Recommendation.signal == signal_enum)
            except ValueError:
                pass
        if exclude_id is not None:
            stmt = stmt.where(Recommendation.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def save(
        self,
        recommendation,
        analysis: dict,
    ) -> Recommendation:
        """Persist a new recommendation (alias for create_recommendation)."""
        return self.create_recommendation(recommendation, analysis)

    def update_recommendation(
        self,
        recommendation_id: int,
        **fields: Any,
    ) -> Recommendation | None:
        """Update fields on an existing recommendation."""
        row = self.get_by_id(recommendation_id)
        if row is None:
            return None
        return self.update(row, **fields)

    @staticmethod
    def _serialize_model(value: Any, *, default: Any) -> Any:
        if value is None:
            return default
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if isinstance(value, list):
            return [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in value
            ]
        if isinstance(value, dict):
            return value
        return default

    def create_recommendation(
        self,
        recommendation,
        analysis: dict,
    ) -> Recommendation:
        """
        Create and persist a Recommendation model from
        an AI recommendation object.
        """

        trend = recommendation.trend
        if isinstance(trend, str):
            try:
                trend = TrendDirection(trend.upper())
            except ValueError:
                trend = TrendDirection.SIDEWAYS

        validation = getattr(recommendation, "validation", None)
        if hasattr(validation, "model_dump"):
            validation = validation.model_dump()
        elif not isinstance(validation, dict):
            validation = {}

        db_recommendation = Recommendation(
            symbol=recommendation.symbol,
            timeframe=recommendation.timeframe,
            signal=recommendation.signal,
            confidence=int(recommendation.confidence),
            trend=trend,
            confluence=int(recommendation.confluence or 0),
            entry_price=recommendation.entry,
            stop_loss=recommendation.stop_loss,
            take_profit=recommendation.take_profit,
            risk_reward=recommendation.risk_reward,
            entry_type=getattr(recommendation, "entry_type", None) or "NONE",
            risk_pips=getattr(recommendation, "risk_pips", 0) or 0,
            reward_pips=getattr(recommendation, "reward_pips", 0) or 0,
            sl_reason=getattr(recommendation, "sl_reason", None) or "",
            tp_reason=getattr(recommendation, "tp_reason", None) or "",
            validation=validation,
            confidence_breakdown=self._serialize_model(
                getattr(recommendation, "confidence_breakdown", None),
                default={},
            ),
            institutional_checklist=self._serialize_model(
                getattr(recommendation, "institutional_checklist", None),
                default=[],
            ),
            market_heatmap=self._serialize_model(
                getattr(recommendation, "market_heatmap", None),
                default={},
            ),
            entry_zone=self._serialize_model(
                getattr(recommendation, "entry_zone", None),
                default={},
            ),
            trade_probability=int(getattr(recommendation, "trade_probability", 0) or 0),
            similar_trade_count=int(
                getattr(recommendation, "similar_trade_count", 0) or 0
            ),
            historical_win_rate=int(
                getattr(recommendation, "historical_win_rate", 0) or 0
            ),
            expected_rr=getattr(recommendation, "expected_rr", 0) or 0,
            expected_hold_time=getattr(recommendation, "expected_hold_time", None) or "",
            trade_quality=int(getattr(recommendation, "trade_quality", 0) or 0),
            quality_grade=getattr(recommendation, "quality_grade", None) or "",
            historical_insights=self._serialize_model(
                getattr(recommendation, "historical_insights", None),
                default=[],
            ),
            probability_detail=self._serialize_model(
                getattr(recommendation, "probability_detail", None),
                default={},
            ),
            analysis=analysis,
            reasoning=recommendation.reason,
            engine_version=getattr(recommendation, "engine_version", None)
            or "1.0.0",
            learning_version=getattr(recommendation, "learning_version", None)
            or "1.0.0",
            weight_version=getattr(recommendation, "weight_version", None)
            or "baseline",
            indicator_version=getattr(recommendation, "indicator_version", None)
            or "1.0.0",
            strategy_version=getattr(recommendation, "strategy_version", None)
            or "1.0.0",
            market_regime=getattr(recommendation, "market_regime", None),
            setup_quality=int(getattr(recommendation, "setup_quality", 0) or 0),
            setup_quality_grade=getattr(recommendation, "setup_quality_grade", None) or "",
            setup_quality_components=self._serialize_model(
                getattr(recommendation, "setup_quality_components", None),
                default={},
            ),
            scanner_group=getattr(recommendation, "scanner_group", None) or "no_trade",
            lifecycle_state=getattr(recommendation, "lifecycle_state", None) or "NEW",
            rejection_checklist=self._serialize_model(
                getattr(recommendation, "rejection_checklist", None),
                default=[],
            ),
            qualification_score=int(
                getattr(recommendation, "qualification_score", 0) or 0
            ),
            trend_strength=float(getattr(recommendation, "trend_strength", 0) or 0),
            correlated=bool(getattr(recommendation, "correlated", False)),
            correlation_note=getattr(recommendation, "correlation_note", None) or "",
            parent_recommendation_id=getattr(
                recommendation, "parent_recommendation_id", None
            ),
        )

        self.create(
            db_recommendation,
        )

        try:
            self.flush()
        except Exception:
            raise

        return db_recommendation

    def delete_before(
        self,
        before: datetime,
    ) -> int:
        """
        Delete recommendations older than a timestamp.
        """

        stmt = (
            delete(Recommendation)
            .where(
                Recommendation.created_at < before
            )
        )

        result = self.db.execute(stmt)

        return result.rowcount or 0
