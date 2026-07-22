"""
Setup lifecycle — update existing setups instead of duplicating recommendations.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from app.core.settings import settings
from app.qualification.models import SetupLifecycleState


ACTIVE_STATES = {
    SetupLifecycleState.NEW.value,
    SetupLifecycleState.ACTIVE.value,
    SetupLifecycleState.WAITING_ENTRY.value,
}

TERMINAL_STATES = {
    SetupLifecycleState.EXPIRED.value,
    SetupLifecycleState.INVALIDATED.value,
    SetupLifecycleState.TP.value,
    SetupLifecycleState.SL.value,
    SetupLifecycleState.EXECUTED.value,
}


def levels_similar(
    *,
    entry_a: float,
    sl_a: float,
    tp_a: float,
    entry_b: float,
    sl_b: float,
    tp_b: float,
    atr: float | None = None,
) -> bool:
    """True when levels have not materially changed."""
    tol = float(settings.SETUP_LEVEL_CHANGE_ATR_FRACTION)
    if atr and atr > 0:
        threshold = atr * tol
    else:
        # Fallback: 0.05% of entry
        threshold = abs(entry_a) * 0.0005 if entry_a else 0.0
        threshold = max(threshold, 1e-8)

    return (
        abs(entry_a - entry_b) <= threshold
        and abs(sl_a - sl_b) <= threshold
        and abs(tp_a - tp_b) <= threshold
    )


def should_create_new(
    *,
    existing: dict[str, Any] | None,
    new_signal: str,
    new_entry: float,
    new_sl: float,
    new_tp: float,
    atr: float | None = None,
    structure_changed: bool = False,
    trend_reversed: bool = False,
    entry_invalidated: bool = False,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """
    Decide whether to insert a new recommendation row.

    Returns (create_new, lifecycle_action) where lifecycle_action is
    'create' | 'update' | 'invalidate' | 'expire'.
    """
    if existing is None:
        return True, "create"

    state = str(existing.get("lifecycle_state") or SetupLifecycleState.ACTIVE.value)
    if state in TERMINAL_STATES:
        return True, "create"

    old_signal = str(existing.get("signal") or "").upper()
    new_sig = new_signal.upper()

    if new_sig == "NO_TRADE" or entry_invalidated or trend_reversed:
        return False, "invalidate"

    if structure_changed:
        return True, "create"

    # Expiry
    created = existing.get("created_at") or existing.get("updated_at")
    if isinstance(created, datetime):
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = (now or datetime.now(timezone.utc)) - created
        max_age = timedelta(minutes=int(settings.SETUP_MAX_AGE_MINUTES))
        if age > max_age:
            return True, "expire"

    if old_signal != new_sig and new_sig in {"BUY", "SELL"} and old_signal in {"BUY", "SELL"}:
        return True, "create"

    if levels_similar(
        entry_a=float(existing.get("entry_price") or existing.get("entry") or 0),
        sl_a=float(existing.get("stop_loss") or 0),
        tp_a=float(existing.get("take_profit") or 0),
        entry_b=new_entry,
        sl_b=new_sl,
        tp_b=new_tp,
        atr=atr,
    ):
        return False, "update"

    # Material level change ⇒ new setup
    return True, "create"


def next_state_on_create(signal: str) -> str:
    sig = signal.upper()
    if sig in {"BUY", "SELL"}:
        return SetupLifecycleState.NEW.value
    if sig == "HOLD":
        return SetupLifecycleState.WAITING_ENTRY.value
    return SetupLifecycleState.INVALIDATED.value


def next_state_on_update(signal: str, current: str | None = None) -> str:
    sig = signal.upper()
    if sig == "NO_TRADE":
        return SetupLifecycleState.INVALIDATED.value
    if current == SetupLifecycleState.NEW.value:
        return SetupLifecycleState.ACTIVE.value
    if sig in {"BUY", "SELL"}:
        return SetupLifecycleState.ACTIVE.value
    if sig == "HOLD":
        return SetupLifecycleState.WAITING_ENTRY.value
    return current or SetupLifecycleState.ACTIVE.value
