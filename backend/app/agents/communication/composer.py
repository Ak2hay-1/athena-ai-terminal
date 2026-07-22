"""
Compose structured NotificationMessage from event payloads.
"""

from __future__ import annotations

from typing import Any

from app.agents.communication.priority import message_type_for
from app.agents.communication.priority import resolve_priority
from app.notifications.message import NotificationMessage


def compose_from_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    user_id: int,
) -> NotificationMessage:
    msg_type = message_type_for(event_type, payload)
    priority = resolve_priority(event_type, payload)
    symbol = str(payload.get("symbol") or "").upper() or None
    side = str(payload.get("signal") or payload.get("bias") or payload.get("side") or "")
    side = side.upper() or None

    confidence = payload.get("confluence") or payload.get("confidence") or payload.get(
        "score"
    )
    try:
        confidence_f = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence_f = None

    reasoning = _as_str_list(
        payload.get("reasoning")
        or payload.get("reasons")
        or payload.get("recommendations")
        or []
    )
    evidence = _as_str_list(payload.get("evidence") or payload.get("citations") or [])
    if not evidence and payload.get("scores"):
        scores = payload["scores"]
        if isinstance(scores, dict):
            evidence = [f"{k}={v}" for k, v in scores.items()]

    summary = str(payload.get("summary") or "").strip()
    if not summary:
        summary = _default_summary(msg_type, symbol, side, confidence_f, payload)

    risk = payload.get("risk") or payload.get("risk_level")
    if risk is None and payload.get("health_score") is not None:
        health = float(payload["health_score"])
        risk = "High" if health < 45 else ("Medium" if health < 70 else "Low")
    risk = str(risk) if risk is not None else None

    sl = _float_or_none(payload.get("stop_loss") or payload.get("sl"))
    tp = _float_or_none(payload.get("take_profit") or payload.get("tp"))
    action = str(payload.get("action") or "").strip() or _default_action(msg_type, payload)

    return NotificationMessage(
        user_id=user_id,
        message_type=msg_type,
        priority=priority,
        summary=summary,
        confidence=confidence_f,
        reasoning=reasoning,
        risk=risk,
        stop_loss=sl,
        take_profit=tp,
        evidence=evidence,
        action=action,
        symbol=symbol,
        side=side,
        dedupe_key=(
            f"{msg_type}:{symbol or '-'}:{payload.get('ticket') or payload.get('timeframe') or '-'}"
        ),
        extra={"source_event": event_type, "raw_keys": list(payload.keys())[:20]},
    )


def _default_summary(
    msg_type: str,
    symbol: str | None,
    side: str | None,
    confidence: float | None,
    payload: dict[str, Any],
) -> str:
    sym = symbol or "Market"
    if msg_type == "Trade Signal":
        conf = f" ({confidence:.0f}%)" if confidence is not None else ""
        return f"{sym} {side or 'SETUP'}{conf} — validation {payload.get('status')}"
    if msg_type == "Trade Closed":
        return f"{sym} closed PnL={payload.get('pnl')} outcome={payload.get('outcome')}"
    if msg_type == "Portfolio Update":
        return (
            f"Portfolio health {payload.get('health_score')} "
            f"win_rate={((payload.get('metrics') or {}).get('win_rate'))}"
        )
    if msg_type == "Breaking News":
        items = payload.get("items") or []
        return f"News update ({len(items)} items)"
    if msg_type == "Market Alert":
        return f"{sym} watchlist opportunity confluence={payload.get('confluence')}"
    return f"{msg_type} for {sym}"


def _default_action(msg_type: str, payload: dict[str, Any]) -> str:
    if msg_type == "Trade Signal":
        status = str(payload.get("status") or "").upper()
        if status == "APPROVED":
            return "Watch for confirmation candle."
        if status == "WAIT":
            return "Wait for confluence confirmation."
        return "Do not enter; review rejection reasons."
    if msg_type in {"SL Hit", "Risk Warning"}:
        return "Reduce risk and review open exposure."
    if msg_type == "Portfolio Update":
        tips = payload.get("recommendations") or []
        if tips and isinstance(tips[0], dict):
            return str(tips[0].get("detail") or tips[0].get("title") or "Review portfolio.")
        return "Review portfolio health and risk."
    if msg_type == "Market Alert":
        return "Review setup on preferred timeframe."
    return "Review details in Athena."


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                out.append(str(item.get("title") or item.get("detail") or item))
            else:
                out.append(str(item))
        return [x for x in out if x.strip()]
    return [str(value)]


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
