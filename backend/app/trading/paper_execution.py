"""
Paper Trading Execution Provider (DB-backed).
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from app.ai.models import AIRecommendation
from app.core.logger import logger
from app.database.database import SessionLocal
from app.events.async_bridge import schedule_publish
from app.events.types import EventType
from app.models.journal_entry import JournalEntry
from app.models.paper_position import PaperPosition
from app.repositories.journal_repository import JournalRepository
from app.repositories.paper_position_repository import PaperPositionRepository


def _side_pnl(signal: str, entry: float, exit_price: float, volume: float) -> float:
    direction = -1.0 if "SELL" in str(signal).upper() else 1.0
    return round((exit_price - entry) * direction * volume, 2)


def _infer_exit_flags(
    signal: str,
    entry: float,
    exit_price: float,
    stop_loss: float,
    take_profit: float,
) -> tuple[bool, bool]:
    side = str(signal).upper()
    sl_hit = False
    tp_hit = False
    if stop_loss > 0:
        if "SELL" in side:
            sl_hit = exit_price >= stop_loss
        else:
            sl_hit = exit_price <= stop_loss
    if take_profit > 0:
        if "SELL" in side:
            tp_hit = exit_price <= take_profit
        else:
            tp_hit = exit_price >= take_profit
    return sl_hit, tp_hit


class PaperExecutionProvider:
    """
    PostgreSQL-backed paper trading backend.
    """

    def execute(
        self,
        recommendation: AIRecommendation,
        *,
        volume: float = 1.0,
        user_id: int,
    ) -> dict:
        signal = recommendation.signal
        if hasattr(signal, "value"):
            signal = signal.value

        db = SessionLocal()
        try:
            repo = PaperPositionRepository(db)
            ticket = repo.next_ticket()
            opened_at = datetime.now(timezone.utc)
            row = PaperPosition(
                user_id=user_id,
                ticket=ticket,
                symbol=str(recommendation.symbol).upper(),
                signal=str(signal).upper(),
                entry=float(recommendation.entry or 0),
                stop_loss=float(recommendation.stop_loss or 0),
                take_profit=float(recommendation.take_profit or 0),
                volume=float(volume or 1.0),
                status="OPEN",
                opened_at=opened_at,
                pnl=0.0,
            )
            repo.create(row)
            db.commit()
            db.refresh(row)
            trade = row.to_trade_dict()
            schedule_publish(
                EventType.TRADE_CREATED,
                {
                    "user_id": row.user_id,
                    "ticket": row.ticket,
                    "symbol": row.symbol,
                    "signal": row.signal,
                    "entry": float(row.entry),
                    "stop_loss": float(row.stop_loss),
                    "take_profit": float(row.take_profit),
                    "volume": float(row.volume),
                    "status": "OPEN",
                },
                source="paper_execution",
                correlation_id=str(row.ticket),
            )
            return trade
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def close(
        self,
        ticket: int,
        *,
        user_id: int | None = None,
        mark: float | None = None,
    ) -> bool:
        db = SessionLocal()
        try:
            repo = PaperPositionRepository(db)
            position = repo.get_open_by_ticket(ticket, user_id=user_id)
            if position is None:
                return False

            exit_price = float(mark) if mark and mark > 0 else float(position.entry)
            pnl = _side_pnl(
                position.signal,
                float(position.entry),
                exit_price,
                float(position.volume or 1.0),
            )
            sl_hit, tp_hit = _infer_exit_flags(
                position.signal,
                float(position.entry),
                exit_price,
                float(position.stop_loss or 0),
                float(position.take_profit or 0),
            )
            position.status = "CLOSED"
            position.closed_at = datetime.now(timezone.utc)
            position.pnl = pnl
            db.commit()
            db.refresh(position)

            if position.user_id:
                try:
                    outcome_label = (
                        "win" if pnl > 0 else ("loss" if pnl < 0 else "breakeven")
                    )
                    journal_repo = JournalRepository(db)
                    journal_repo.create(
                        JournalEntry(
                            user_id=position.user_id,
                            entry_type="auto_close",
                            title=f"{position.symbol} {position.signal} closed",
                            body=(
                                f"Ticket {position.ticket} · "
                                f"Entry {float(position.entry):.5f} · "
                                f"Exit {exit_price:.5f} · "
                                f"PnL {pnl:.2f} ({outcome_label})"
                            ),
                            symbol=position.symbol,
                            tags=["auto_close", outcome_label],
                            paper_position_id=position.id,
                            recommendation_id=position.recommendation_id,
                        )
                    )
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.exception(
                        "Failed to create auto_close journal for ticket=%s",
                        position.ticket,
                    )

            outcome = "win" if pnl > 0 else ("loss" if pnl < 0 else "breakeven")
            schedule_publish(
                EventType.TRADE_CLOSED,
                {
                    "user_id": position.user_id,
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "signal": position.signal,
                    "entry": float(position.entry),
                    "exit": exit_price,
                    "stop_loss": float(position.stop_loss or 0),
                    "take_profit": float(position.take_profit or 0),
                    "volume": float(position.volume or 1.0),
                    "pnl": pnl,
                    "outcome": outcome,
                    "sl_hit": sl_hit,
                    "tp_hit": tp_hit,
                    "status": "CLOSED",
                },
                source="paper_execution",
                correlation_id=str(position.ticket),
            )
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def positions(
        self,
        marks: dict[str, float] | None = None,
        *,
        user_id: int | None = None,
    ) -> list:
        db = SessionLocal()
        try:
            repo = PaperPositionRepository(db)
            open_positions = [
                row.to_trade_dict() for row in repo.list_open(user_id=user_id)
            ]
        finally:
            db.close()

        if not marks:
            return open_positions

        enriched: list[dict] = []
        for position in open_positions:
            row = dict(position)
            symbol = str(row.get("symbol", "")).upper()
            mark = marks.get(symbol)
            if mark is not None and mark > 0:
                entry = float(row.get("entry") or 0)
                volume = float(row.get("volume") or 1.0)
                side = str(row.get("signal", "")).upper()
                if entry > 0:
                    row["pnl"] = _side_pnl(side, entry, mark, volume)
                    row["mark"] = mark
            enriched.append(row)
        return enriched

    def count_open(self, user_id: int) -> int:
        db = SessionLocal()
        try:
            return PaperPositionRepository(db).count_open(user_id)
        finally:
            db.close()


paper_execution = PaperExecutionProvider()
