"""
Format structured notifications for text channels.
"""

from __future__ import annotations

from app.notifications.message import NotificationMessage


def format_text(message: NotificationMessage) -> str:
    lines = [
        f"{message.symbol or 'MARKET'} — {message.message_type}",
    ]
    if message.side:
        lines.append(f"Side: {message.side}")
    if message.confidence is not None:
        lines.append(f"Confidence: {message.confidence:.0f}%")
    lines.append(f"Summary: {message.summary}")
    if message.reasoning:
        lines.append("Why:")
        for reason in message.reasoning[:6]:
            lines.append(f"  • {reason}")
    if message.risk:
        lines.append(f"Risk: {message.risk}")
    if message.stop_loss is not None:
        lines.append(f"SL: {message.stop_loss}")
    if message.take_profit is not None:
        lines.append(f"TP: {message.take_profit}")
    if message.evidence:
        lines.append("Evidence:")
        for item in message.evidence[:6]:
            lines.append(f"  • {item}")
    if message.action:
        lines.append(f"Action: {message.action}")
    lines.append(f"Priority: {message.priority}")
    return "\n".join(lines)


def format_subject(message: NotificationMessage) -> str:
    symbol = message.symbol or "Athena"
    return f"[Athena] {symbol} {message.message_type} ({message.priority})"
