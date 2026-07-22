"""
Athena Recommendation Engine.

Risk engine owns signal, confidence, and all trade levels.
The LLM only explains the frozen plan.
Qualification rejects weak markets before RiskEngine.
Institutional and probability enrichments are deterministic.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pandas as pd

from app.ai.models import AIRecommendation
from app.ai.schemas.context import MarketContext
from app.ai.services.ai_service import ai_service
from app.analysis.market_analyzer import market_analyzer
from app.analysis.multi_timeframe_analyzer import multi_timeframe_analyzer
from app.core.enums import RecommendationSignal
from app.core.logger import logger
from app.core.settings import settings
from app.learning.regime_classifier import classify_regime
from app.models.learning import ConfluenceSnapshot
from app.models.learning import PatternOccurrence
from app.qualification.correlation_filter import conflicts_with_open
from app.qualification.portfolio_awareness import evaluate_portfolio_fit
from app.qualification.qualification_engine import qualification_engine
from app.qualification.recommendation_ranker import apply_global_limits_to_recommendation
from app.qualification.rejection_reasons import build_rejection_checklist
from app.qualification.rejection_reasons import format_rejection_summary
from app.qualification.rejection_reasons import merge_validation_into_gates
from app.qualification.setup_lifecycle import next_state_on_create
from app.qualification.setup_lifecycle import next_state_on_update
from app.qualification.setup_lifecycle import should_create_new
from app.qualification.setup_quality import scanner_group_for_score
from app.qualification.setup_quality import setup_quality_service
from app.repositories.learning_repository import LearningRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.risk.confidence_engine import ConfidenceEngine
from app.risk.models import TradePlan
from app.risk.models import ValidationFlags
from app.risk.risk_engine import risk_engine
from app.services.confidence_breakdown_service import ConfidenceBreakdownService
from app.services.confidence_breakdown_service import confidence_breakdown_service
from app.services.entry_zone_service import entry_zone_service
from app.services.historical_insights_service import historical_insights_service
from app.services.historical_similarity_service import HistoricalSimilarityService
from app.services.institutional_checklist_service import institutional_checklist_service
from app.services.learning.adaptive_weight_service import AdaptiveWeightService
from app.services.market_heatmap_service import market_heatmap_service
from app.services.trade_probability_service import TradeProbabilityService
from app.services.trade_quality_service import trade_quality_service


class RecommendationEngine:
    """
    AI Recommendation Engine.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
        symbol: str,
        timeframe: str,
        repository: RecommendationRepository | None = None,
        *,
        news_context: dict | None = None,
        higher_timeframes: dict[str, pd.DataFrame] | None = None,
        weights: dict[str, float] | None = None,
        persist: bool = True,
        explain_with_ai: bool = True,
        spread: float | None = None,
        open_trades: list[dict] | None = None,
    ) -> AIRecommendation:

        try:

            if dataframe.empty:

                return AIRecommendation(
                    signal=RecommendationSignal.NO_TRADE,
                    confidence=0,
                    reason=[
                        "No candle data available.",
                    ],
                    symbol=symbol,
                    timeframe=timeframe,
                    scanner_group="no_trade",
                    lifecycle_state="INVALIDATED",
                    rejection_checklist=build_rejection_checklist(
                        extra=[
                            {
                                "name": "Data Availability",
                                "passed": False,
                                "detail": "Empty candle frame",
                            }
                        ]
                    ),
                )

            multi_tf = None
            multi_tf_trend = None

            if higher_timeframes:

                multi_tf = multi_timeframe_analyzer.analyze(
                    higher_timeframes,
                )
                multi_tf_trend = multi_tf.get("overall_trend")

            analysis = market_analyzer.analyze(
                dataframe,
                news_context=news_context,
                multi_timeframe=multi_tf,
                weights=weights,
            )

            # --------------------------------------------------
            # Phase 1 — Qualification (before RiskEngine)
            # --------------------------------------------------
            qual = None
            mtf_aligned = True
            if settings.QUALIFICATION_ENABLED:
                qual = qualification_engine.evaluate(
                    dataframe,
                    symbol=symbol,
                    timeframe=timeframe,
                    analysis=analysis,
                    higher_timeframes=higher_timeframes,
                    multi_tf_summary=multi_tf,
                    news_context=news_context,
                    spread=spread,
                )
                mtf_aligned = all(
                    g.passed
                    for g in qual.gates
                    if "Alignment" in g.name or g.name == "Execution Trend"
                ) if qual.gates else True

                if not qual.qualified:
                    checklist = build_rejection_checklist(qual.gates)
                    return self._finalize_no_trade(
                        symbol=symbol,
                        timeframe=timeframe,
                        analysis=analysis,
                        reasons=qual.reasons or format_rejection_summary(checklist),
                        checklist=checklist,
                        regime=qual.regime,
                        qualification_score=qual.quality_score,
                        trend_strength=qual.trend_strength,
                        repository=repository,
                        persist=persist,
                    )

            confidence_weights = None
            weight_version = "baseline"
            if repository is not None and settings.LEARNING_ENABLED:
                try:
                    weight_service = AdaptiveWeightService(repository.db)
                    confidence_weights = weight_service.get_active_weights()
                    weight_version = weight_service.get_active_version()
                except Exception as exc:
                    logger.warning("Active confidence weights unavailable: %s", exc)

            bundle = risk_engine.build_plan(
                dataframe,
                symbol=symbol,
                timeframe=timeframe,
                higher_timeframes=higher_timeframes,
                news_context=news_context,
                multi_tf_trend=multi_tf_trend,
                confidence_weights=confidence_weights,
                market_regime=qual.regime if qual else None,
                mtf_aligned=mtf_aligned if settings.QUAL_MTF_REQUIRE_STRICT else None,
                trend_strength=qual.trend_strength if qual else None,
                spread=spread,
            )
            plan = bundle.plan
            context = bundle.context

            recommendation = self._from_plan(
                plan,
                analysis=analysis,
                symbol=symbol,
                timeframe=timeframe,
            )

            # Prefer qualification regime; fall back to learning classifier
            if qual is not None:
                regime = qual.regime
                recommendation.qualification_score = qual.quality_score
                recommendation.trend_strength = qual.trend_strength
            else:
                regime = classify_regime(
                    analysis=analysis,
                    trend=str(plan.trend or ""),
                    news_blocked=bool((news_context or {}).get("blocked")),
                    news_score=(news_context or {}).get("score"),
                    bos_active=bool(getattr(context, "bos_active", False)),
                    choch_active=bool(getattr(context, "choch_active", False)),
                )
            recommendation.market_regime = regime
            recommendation.engine_version = settings.ENGINE_VERSION
            recommendation.learning_version = settings.LEARNING_SYSTEM_VERSION
            recommendation.weight_version = weight_version
            recommendation.indicator_version = settings.INDICATOR_VERSION
            recommendation.strategy_version = settings.STRATEGY_VERSION

            # Deterministic institutional enrichments (no AI).
            breakdown_service = (
                ConfidenceBreakdownService(ConfidenceEngine(confidence_weights))
                if confidence_weights
                else confidence_breakdown_service
            )
            recommendation.confidence_breakdown = breakdown_service.build(
                context,
                plan,
            )
            recommendation.institutional_checklist = institutional_checklist_service.build(
                context,
                plan,
            )
            recommendation.market_heatmap = market_heatmap_service.build(
                context,
                plan,
                analysis=analysis,
            )
            recommendation.entry_zone = entry_zone_service.build(
                context,
                plan,
            )

            # --------------------------------------------------
            # Phase 4 — Setup Quality (separate from confidence)
            # --------------------------------------------------
            vol_ratio = 1.0
            if context.avg_volume > 0:
                vol_ratio = context.volume / context.avg_volume
            structure_score = 0.0
            if context.bos_active:
                structure_score += 40.0
            if context.choch_active:
                structure_score += 25.0
            structure_score += min(35.0, float(recommendation.confluence or 0) * 0.35)

            validation_dump = (
                plan.validation.model_dump()
                if hasattr(plan.validation, "model_dump")
                else dict(plan.validation or {})
            )
            quality = setup_quality_service.score(
                trend_strength=float(recommendation.trend_strength or 0.0),
                structure_score=structure_score,
                volume_ratio=vol_ratio,
                risk_reward=float(plan.risk_reward or 0.0),
                atr_ok=bool(context.atr_ok and not context.tight_range),
                session=qual.session if qual else None,
                bos_active=bool(context.bos_active),
                choch_active=bool(context.choch_active),
                confluence=float(recommendation.confluence or 0),
                validation_flags=validation_dump,
                gates=qual.gates if qual else None,
            )
            recommendation.setup_quality = quality.score
            recommendation.setup_quality_grade = quality.grade
            recommendation.setup_quality_components = quality.components
            # Keep trade_quality in sync for scanner/legacy consumers
            recommendation.trade_quality = quality.score
            recommendation.quality_grade = quality.grade

            # Quality floor → demote / reject (never soft-lower confidence)
            signal_value = (
                recommendation.signal.value
                if hasattr(recommendation.signal, "value")
                else str(recommendation.signal)
            )
            if signal_value in {"BUY", "SELL"}:
                if quality.score < 60:
                    recommendation.signal = RecommendationSignal.NO_TRADE
                    recommendation.reason = [
                        *recommendation.reason,
                        f"Setup quality {quality.score} below 60 — NO_TRADE.",
                    ]
                    signal_value = "NO_TRADE"
                elif quality.score < int(settings.MIN_SETUP_QUALITY) or int(
                    recommendation.confidence
                ) < int(settings.MIN_CONFIDENCE):
                    recommendation.signal = RecommendationSignal.HOLD
                    recommendation.reason = [
                        *recommendation.reason,
                        (
                            f"Setup quality {quality.score} / confidence "
                            f"{recommendation.confidence} → Watchlist."
                        ),
                    ]
                    signal_value = "HOLD"

            # Portfolio awareness
            if (
                settings.PORTFOLIO_AWARENESS_ENABLED
                and signal_value in {"BUY", "SELL"}
            ):
                peers = open_trades
                if peers is None and repository is not None:
                    peers = self._recent_actionable_peers(repository, exclude_symbol=symbol)
                allowed, portfolio_reasons = evaluate_portfolio_fit(
                    symbol=symbol,
                    signal=signal_value,
                    open_trades=peers,
                )
                if not allowed:
                    recommendation.signal = RecommendationSignal.HOLD
                    recommendation.reason = [
                        *recommendation.reason,
                        *portfolio_reasons,
                    ]
                    signal_value = "HOLD"
                    recommendation.correlated = any(
                        "Correlat" in r for r in portfolio_reasons
                    )
                    recommendation.correlation_note = "; ".join(portfolio_reasons)

            # Correlation vs open book
            if signal_value in {"BUY", "SELL"} and open_trades:
                conflict, note = conflicts_with_open(
                    symbol=symbol,
                    signal=signal_value,
                    open_trades=open_trades,
                )
                if conflict and not settings.ALLOW_CORRELATED_TRADES:
                    recommendation.signal = RecommendationSignal.HOLD
                    recommendation.correlated = True
                    recommendation.correlation_note = note or "Correlated Opportunity"
                    recommendation.reason = [
                        *recommendation.reason,
                        recommendation.correlation_note,
                    ]
                    signal_value = "HOLD"

            # Global actionable limits vs recent peers
            if signal_value in {"BUY", "SELL"} and repository is not None:
                peer_count = self._count_recent_actionable(repository, exclude_symbol=symbol)
                new_signal, group = apply_global_limits_to_recommendation(
                    signal=signal_value,
                    setup_quality=quality.score,
                    confidence=int(recommendation.confidence),
                    peer_actionable_count=peer_count,
                )
                if new_signal != signal_value:
                    recommendation.signal = RecommendationSignal(new_signal)
                    recommendation.reason = [
                        *recommendation.reason,
                        f"Demoted to {new_signal} — actionable limit / quality gate.",
                    ]
                    signal_value = new_signal
                recommendation.scanner_group = group
            else:
                recommendation.scanner_group = scanner_group_for_score(
                    quality.score,
                    signal_value,
                )

            # Structured rejection checklist for NO_TRADE / HOLD explainability
            if signal_value in {"NO_TRADE", "HOLD"}:
                gates = list(qual.gates) if qual else []
                gates.extend(
                    merge_validation_into_gates(
                        validation_dump,
                        reasons=list(plan.reasons),
                    )
                )
                checklist = build_rejection_checklist(gates)
                recommendation.rejection_checklist = checklist
                if signal_value == "NO_TRADE" and not recommendation.reason:
                    recommendation.reason = format_rejection_summary(checklist)

            # Deterministic probability enrichments (requires DB history).
            if repository is not None:
                self._attach_probability_fields(
                    recommendation,
                    analysis=analysis,
                    repository=repository,
                )

            trade_plan_payload = plan.model_dump()

            try:
                context_payload = MarketContext.from_analysis(
                    analysis,
                    symbol=symbol,
                    timeframe=timeframe,
                    trade_plan=trade_plan_payload,
                )
                from concurrent.futures import ThreadPoolExecutor
                from concurrent.futures import TimeoutError as FuturesTimeout
                _is_no_trade = (
                    recommendation.signal == RecommendationSignal.NO_TRADE
                    or str(recommendation.signal) == "NO_TRADE"
                    or getattr(recommendation.signal, "value", "") == "NO_TRADE"
                )
                # Skip LLM for scheduler/NO_TRADE — local fallback was ~140s/symbol and starved HTTP.
                if not explain_with_ai or _is_no_trade:
                    explanation = None
                else:
                    with ThreadPoolExecutor(max_workers=1) as _pool:
                        _fut = _pool.submit(
                            ai_service.generate_trade_explanation,
                            context_payload,
                        )
                        try:
                            explanation = _fut.result(timeout=float(settings.AI_TIMEOUT))
                        except FuturesTimeout:
                            logger.warning(
                                "AI explanation timed out after %ss for %s %s",
                                settings.AI_TIMEOUT,
                                symbol,
                                timeframe,
                            )
                            explanation = None
                if explanation is not None and explanation.reasons:
                    recommendation.reason = [
                        *recommendation.reason,
                        *explanation.reasons,
                    ]
            except Exception as exc:
                logger.warning("AI explanation skipped: %s", exc)
                if not recommendation.reason:
                    recommendation.reason = [
                        plan.sl_reason or "Risk engine plan generated.",
                        plan.tp_reason or "",
                    ]

            if repository is not None and persist:
                self._persist_with_lifecycle(
                    repository=repository,
                    recommendation=recommendation,
                    analysis={
                        **analysis,
                        "trade_plan": trade_plan_payload,
                        "market_regime": regime,
                        "setup_quality": recommendation.setup_quality,
                        "rejection_checklist": recommendation.rejection_checklist,
                    },
                    atr=float(context.atr or 0.0),
                )

            return recommendation

        except Exception as exc:

            logger.exception(exc)

            return AIRecommendation(
                signal=RecommendationSignal.NO_TRADE,
                confidence=0,
                reason=[
                    str(exc),
                ],
                symbol=symbol,
                timeframe=timeframe,
                scanner_group="no_trade",
            )

    def _finalize_no_trade(
        self,
        *,
        symbol: str,
        timeframe: str,
        analysis: dict,
        reasons: list[str],
        checklist: list[dict],
        regime: str,
        qualification_score: int,
        trend_strength: float,
        repository: RecommendationRepository | None,
        persist: bool,
    ) -> AIRecommendation:
        recommendation = AIRecommendation(
            signal=RecommendationSignal.NO_TRADE,
            confidence=0,
            reason=list(reasons),
            symbol=symbol,
            timeframe=timeframe,
            trend=(analysis.get("trend") or {}).get("direction"),
            confluence=(analysis.get("confluence") or {}).get("score"),
            market_regime=regime,
            qualification_score=qualification_score,
            setup_quality=qualification_score,
            setup_quality_grade="No Trade",
            trade_quality=qualification_score,
            quality_grade="No Trade",
            scanner_group="no_trade",
            lifecycle_state="INVALIDATED",
            rejection_checklist=checklist,
            trend_strength=trend_strength,
            engine_version=settings.ENGINE_VERSION,
            learning_version=settings.LEARNING_SYSTEM_VERSION,
            indicator_version=settings.INDICATOR_VERSION,
            strategy_version=settings.STRATEGY_VERSION,
        )
        if repository is not None and persist:
            self._persist_with_lifecycle(
                repository=repository,
                recommendation=recommendation,
                analysis={
                    **analysis,
                    "market_regime": regime,
                    "rejection_checklist": checklist,
                    "qualified": False,
                },
                atr=None,
            )
        return recommendation

    def _persist_with_lifecycle(
        self,
        *,
        repository: RecommendationRepository,
        recommendation: AIRecommendation,
        analysis: dict,
        atr: float | None,
    ) -> None:
        """Create or update recommendation according to setup lifecycle rules."""
        existing = None
        existing_dict = None
        if settings.SETUP_LIFECYCLE_ENABLED:
            existing = repository.get_active_setup(
                recommendation.symbol or "",
                recommendation.timeframe or "",
            )
            if existing is not None:
                existing_dict = {
                    "id": existing.id,
                    "signal": getattr(existing.signal, "value", existing.signal),
                    "entry_price": float(existing.entry_price or 0),
                    "stop_loss": float(existing.stop_loss or 0),
                    "take_profit": float(existing.take_profit or 0),
                    "lifecycle_state": getattr(existing, "lifecycle_state", None)
                    or "ACTIVE",
                    "created_at": existing.created_at,
                    "updated_at": getattr(existing, "updated_at", None),
                }

        signal_value = (
            recommendation.signal.value
            if hasattr(recommendation.signal, "value")
            else str(recommendation.signal)
        )
        create_new, action = should_create_new(
            existing=existing_dict,
            new_signal=signal_value,
            new_entry=float(recommendation.entry or 0),
            new_sl=float(recommendation.stop_loss or 0),
            new_tp=float(recommendation.take_profit or 0),
            atr=atr,
            now=datetime.now(timezone.utc),
        )

        if action == "invalidate" and existing is not None:
            repository.update_recommendation(
                existing.id,
                lifecycle_state="INVALIDATED",
                signal=RecommendationSignal.NO_TRADE,
                reasoning=recommendation.reason,
                rejection_checklist=recommendation.rejection_checklist,
                setup_quality=recommendation.setup_quality,
                setup_quality_grade=recommendation.setup_quality_grade,
                scanner_group=recommendation.scanner_group or "no_trade",
                analysis=analysis,
            )
            return

        if action == "update" and existing is not None and not create_new:
            recommendation.lifecycle_state = next_state_on_update(
                signal_value,
                existing_dict.get("lifecycle_state") if existing_dict else None,
            )
            recommendation.parent_recommendation_id = existing.id
            fields = self._recommendation_update_fields(recommendation, analysis)
            repository.update_recommendation(existing.id, **fields)
            return

        if action == "expire" and existing is not None:
            repository.update_recommendation(
                existing.id,
                lifecycle_state="EXPIRED",
            )

        recommendation.lifecycle_state = next_state_on_create(signal_value)
        row = repository.create_recommendation(
            recommendation=recommendation,
            analysis=analysis,
        )
        self._persist_learning_snapshots(
            repository=repository,
            recommendation_id=row.id,
            symbol=recommendation.symbol or "",
            timeframe=recommendation.timeframe or "",
            analysis=analysis,
            recommendation=recommendation,
        )

    @staticmethod
    def _recommendation_update_fields(
        recommendation: AIRecommendation,
        analysis: dict,
    ) -> dict:
        validation = getattr(recommendation, "validation", None)
        if hasattr(validation, "model_dump"):
            validation = validation.model_dump()
        return {
            "signal": recommendation.signal,
            "confidence": int(recommendation.confidence),
            "entry_price": recommendation.entry,
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
            "risk_reward": recommendation.risk_reward,
            "entry_type": recommendation.entry_type,
            "risk_pips": recommendation.risk_pips,
            "reward_pips": recommendation.reward_pips,
            "sl_reason": recommendation.sl_reason,
            "tp_reason": recommendation.tp_reason,
            "validation": validation or {},
            "reasoning": recommendation.reason,
            "analysis": analysis,
            "confluence": int(recommendation.confluence or 0),
            "market_regime": recommendation.market_regime,
            "setup_quality": recommendation.setup_quality,
            "setup_quality_grade": recommendation.setup_quality_grade,
            "setup_quality_components": recommendation.setup_quality_components,
            "trade_quality": recommendation.trade_quality,
            "quality_grade": recommendation.quality_grade,
            "scanner_group": recommendation.scanner_group,
            "lifecycle_state": recommendation.lifecycle_state,
            "rejection_checklist": recommendation.rejection_checklist,
            "qualification_score": recommendation.qualification_score,
            "trend_strength": recommendation.trend_strength,
            "correlated": recommendation.correlated,
            "correlation_note": recommendation.correlation_note,
            "confidence_breakdown": (
                recommendation.confidence_breakdown.model_dump()
                if recommendation.confidence_breakdown
                and hasattr(recommendation.confidence_breakdown, "model_dump")
                else recommendation.confidence_breakdown or {}
            ),
            "institutional_checklist": [
                i.model_dump() if hasattr(i, "model_dump") else i
                for i in (recommendation.institutional_checklist or [])
            ],
            "market_heatmap": (
                recommendation.market_heatmap.model_dump()
                if recommendation.market_heatmap
                and hasattr(recommendation.market_heatmap, "model_dump")
                else recommendation.market_heatmap or {}
            ),
            "entry_zone": (
                recommendation.entry_zone.model_dump()
                if recommendation.entry_zone
                and hasattr(recommendation.entry_zone, "model_dump")
                else recommendation.entry_zone or {}
            ),
        }

    def _count_recent_actionable(
        self,
        repository: RecommendationRepository,
        *,
        exclude_symbol: str,
    ) -> int:
        try:
            return repository.count_active_actionable(exclude_symbol=exclude_symbol)
        except Exception as exc:
            logger.warning("Actionable peer count failed: %s", exc)
            return 0

    def _recent_actionable_peers(
        self,
        repository: RecommendationRepository,
        *,
        exclude_symbol: str,
    ) -> list[dict]:
        try:
            rows = repository.list_active_actionable(exclude_symbol=exclude_symbol)
            return [
                {
                    "symbol": r.symbol,
                    "signal": getattr(r.signal, "value", r.signal),
                    "risk_percent": float(settings.MAX_RISK_PERCENT),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Peer open-trade lookup failed: %s", exc)
            return []

    def _attach_probability_fields(
        self,
        recommendation: AIRecommendation,
        *,
        analysis: dict,
        repository: RecommendationRepository,
    ) -> None:
        """Attach similarity / probability / quality / insights (no AI)."""
        try:
            if not settings.LEARNING_ENABLED:
                return

            similarity = HistoricalSimilarityService(repository.db)
            probability_service = TradeProbabilityService(repository.db)

            similar_rows = similarity.find_similar(
                recommendation,
                analysis=analysis,
                labeled_only=True,
            )
            prob = probability_service.estimate(
                recommendation,
                analysis=analysis,
                similar_rows=similar_rows,
            )
            # Preserve setup_quality as authoritative; still compute legacy grade blend
            quality = trade_quality_service.score(
                recommendation,
                prob,
                analysis=analysis,
            )
            insights = historical_insights_service.build(similar_rows)

            recommendation.trade_probability = prob.probability
            recommendation.similar_trade_count = prob.similar_trades
            recommendation.historical_win_rate = prob.historical_win_rate
            recommendation.expected_rr = float(prob.expected_rr)
            recommendation.expected_hold_time = prob.expected_hold_time
            # Do not overwrite institutional setup_quality; keep historical grade hint
            if not recommendation.setup_quality:
                recommendation.trade_quality = quality.trade_quality
                recommendation.quality_grade = quality.grade
            recommendation.historical_insights = insights
            recommendation.probability_detail = prob
        except Exception as exc:
            logger.warning("Probability enrichment skipped: %s", exc)

    def _persist_learning_snapshots(
        self,
        *,
        repository: RecommendationRepository,
        recommendation_id: int,
        symbol: str,
        timeframe: str,
        analysis: dict,
        recommendation: AIRecommendation,
    ) -> None:
        """Write pattern occurrences + confluence snapshot (append-only)."""
        try:
            learning = LearningRepository(repository.db)
            confluence = analysis.get("confluence") or {}
            factors = confluence.get("factors") or confluence
            if isinstance(factors, dict):
                learning.save_snapshot(
                    ConfluenceSnapshot(
                        recommendation_id=recommendation_id,
                        symbol=symbol,
                        timeframe=timeframe,
                        factors=factors,
                        total_score=int(
                            confluence.get("score")
                            or recommendation.confluence
                            or 0
                        ),
                    )
                )

            checklist = recommendation.institutional_checklist or []
            for item in checklist:
                name = getattr(item, "name", None) or (
                    item.get("name") if isinstance(item, dict) else None
                )
                passed = getattr(item, "passed", None)
                if isinstance(item, dict):
                    passed = item.get("passed")
                if not name or not passed:
                    continue
                learning.save_pattern(
                    PatternOccurrence(
                        symbol=symbol,
                        timeframe=timeframe,
                        pattern_type=str(name),
                        context={
                            "recommendation_id": recommendation_id,
                            "signal": str(recommendation.signal),
                        },
                        outcome=None,
                    )
                )
            repository.db.commit()
        except Exception as exc:
            logger.warning("Learning snapshot persist skipped: %s", exc)

    def _from_plan(
        self,
        plan: TradePlan,
        *,
        analysis: dict,
        symbol: str,
        timeframe: str,
    ) -> AIRecommendation:
        signal = plan.signal
        try:
            signal_enum = RecommendationSignal(signal)
        except ValueError:
            signal_enum = RecommendationSignal.NO_TRADE

        reasons = list(plan.reasons)
        for extra in (plan.sl_reason, plan.tp_reason, plan.entry_reason):
            if extra and extra not in reasons:
                reasons.append(extra)

        validation = plan.validation
        if not isinstance(validation, ValidationFlags):
            validation = ValidationFlags.model_validate(validation or {})

        return AIRecommendation(
            signal=signal_enum,
            confidence=int(plan.confidence),
            entry=float(plan.entry),
            entry_type=plan.entry_type.value if hasattr(plan.entry_type, "value") else str(plan.entry_type),
            stop_loss=float(plan.stop_loss),
            take_profit=float(plan.take_profit),
            risk_reward=float(plan.risk_reward),
            risk_pips=float(plan.risk_pips),
            reward_pips=float(plan.reward_pips),
            sl_reason=plan.sl_reason,
            tp_reason=plan.tp_reason,
            entry_reason=plan.entry_reason,
            validation=validation,
            reason=reasons,
            trend=plan.trend or analysis.get("trend", {}).get("direction"),
            confluence=analysis.get("confluence", {}).get("score"),
            symbol=symbol,
            timeframe=timeframe,
        )


recommendation_engine = RecommendationEngine()
