"""
Record notification interactions and soft preference updates.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.memory.service import MemoryService
from app.models.notification import NotificationDelivery
from app.repositories.notification_repository import NotificationRepository
from app.repositories.preferences_repository import PreferencesRepository

logger = get_logger("athena.personalization.tracker")


def record_interaction(
    db: Session,
    *,
    user_id: int,
    delivery: NotificationDelivery,
    action: str,
) -> None:
    repo = NotificationRepository(db)
    repo.add_interaction(
        delivery_id=delivery.id,
        user_id=user_id,
        action=action,
    )
    _update_soft_weights(db, user_id=user_id, delivery=delivery, action=action)
    try:
        MemoryService().store(
            agent_id="personalization",
            memory_type="user_feedback",
            payload={
                "user_id": user_id,
                "delivery_id": delivery.id,
                "action": action,
                "message_type": delivery.message_type,
                "symbol": (delivery.payload or {}).get("symbol"),
            },
            symbol=(delivery.payload or {}).get("symbol"),
            correlation_id=str(delivery.id),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("personalization memory store skipped: %s", exc)


def _update_soft_weights(
    db: Session,
    *,
    user_id: int,
    delivery: NotificationDelivery,
    action: str,
) -> None:
    prefs_repo = PreferencesRepository(db)
    prefs = prefs_repo.get_or_create(user_id)
    weights: dict[str, Any] = dict(prefs.soft_weights or {})
    type_weights = dict(weights.get("message_types") or {})
    symbol_weights = dict(weights.get("symbols") or {})

    delta = {"opened": 0.05, "clicked": 0.12, "dismissed": -0.15}.get(action, 0.0)
    message_type = delivery.message_type
    symbol = str((delivery.payload or {}).get("symbol") or "").upper()

    type_weights[message_type] = round(
        float(type_weights.get(message_type, 0.0)) + delta,
        4,
    )
    if symbol:
        symbol_weights[symbol] = round(
            float(symbol_weights.get(symbol, 0.0)) + delta,
            4,
        )

    weights["message_types"] = type_weights
    weights["symbols"] = symbol_weights
    prefs.soft_weights = weights
    db.commit()
