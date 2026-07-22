"""
Athena WebSocket API.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from jose import JWTError
from sqlalchemy.orm import Session

from app.ai.schemas.context import ChatMessage
from app.ai.services.ai_service import ai_service
from app.auth.security import security
from app.core.logger import logger
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import SessionLocal
from app.services.auth_service import AuthService
from app.services.market_service import MarketService
from app.websocket.connection_manager import connection_manager

router = APIRouter(tags=["WebSocket"])


def _extract_ws_token(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if token:
        return token
    auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _authenticate_ws_user(token: str) -> int | None:
    """Return authenticated user_id or None."""
    db: Session | None = None
    try:
        if security.get_token_type(token) != "access":
            return None
        user_id = int(security.get_subject(token))
        db = SessionLocal()
        user = AuthService(db).get_user(user_id)
        if user and user.is_active:
            return int(user.id)
        return None
    except (JWTError, ValueError, TypeError, Exception):
        return None
    finally:
        if db is not None:
            db.close()


def _build_market_context(symbol: str | None, timeframe: str | None):
    if not symbol or not timeframe:
        return None
    db = SessionLocal()
    try:
        symbol = validate_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        return MarketService(db).build_ai_market_context(symbol, timeframe)
    except Exception:
        logger.exception("Failed to build AI market context for WS stream.")
        return None
    finally:
        db.close()


async def _stream_ai_chunks(
    websocket: WebSocket,
    *,
    request_id: str,
    iterator,
) -> None:
    """Drain a sync token iterator and emit ai_chunk / ai_done / ai_error."""

    full_parts: list[str] = []

    def _next_chunk(it):
        try:
            return next(it), False
        except StopIteration:
            return None, True

    try:
        while True:
            chunk, done = await asyncio.to_thread(_next_chunk, iterator)
            if done:
                break
            if not chunk:
                continue
            full_parts.append(chunk)
            await websocket.send_json(
                {
                    "type": "ai_chunk",
                    "request_id": request_id,
                    "delta": chunk,
                }
            )
        await websocket.send_json(
            {
                "type": "ai_done",
                "request_id": request_id,
                "full": "".join(full_parts),
            }
        )
    except Exception as exc:
        logger.exception("AI websocket stream failed.")
        await websocket.send_json(
            {
                "type": "ai_error",
                "request_id": request_id,
                "message": str(exc),
            }
        )


async def _handle_ai_chat(websocket: WebSocket, message: dict[str, Any]) -> None:
    request_id = str(message.get("request_id") or "chat")
    raw_messages = message.get("messages") or []
    if not isinstance(raw_messages, list) or not raw_messages:
        await websocket.send_json(
            {
                "type": "ai_error",
                "request_id": request_id,
                "message": "messages required",
            }
        )
        return

    chat_messages: list[ChatMessage] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "user")
        content = str(item.get("content") or "").strip()
        if content:
            chat_messages.append(ChatMessage(role=role, content=content))

    if not chat_messages:
        await websocket.send_json(
            {
                "type": "ai_error",
                "request_id": request_id,
                "message": "No valid chat messages.",
            }
        )
        return

    context = await asyncio.to_thread(
        _build_market_context,
        message.get("symbol"),
        message.get("timeframe"),
    )
    iterator = ai_service.chat_stream(chat_messages, context=context)
    await _stream_ai_chunks(websocket, request_id=request_id, iterator=iterator)


async def _handle_ai_explain(websocket: WebSocket, message: dict[str, Any]) -> None:
    request_id = str(message.get("request_id") or "explain")
    symbol = message.get("symbol")
    timeframe = message.get("timeframe")
    if not symbol or not timeframe:
        await websocket.send_json(
            {
                "type": "ai_error",
                "request_id": request_id,
                "message": "symbol and timeframe required",
            }
        )
        return

    context = await asyncio.to_thread(_build_market_context, symbol, timeframe)
    if context is None:
        await websocket.send_json(
            {
                "type": "ai_error",
                "request_id": request_id,
                "message": "Not enough market data for explanation.",
            }
        )
        return

    iterator = ai_service.explain_trade_stream(context)
    await _stream_ai_chunks(websocket, request_id=request_id, iterator=iterator)


async def handle_market_websocket(websocket: WebSocket) -> None:
    """Shared market stream handler used by app-level and router mounts."""

    token = _extract_ws_token(websocket)
    user_id = _authenticate_ws_user(token) if token else None
    if not token or user_id is None:
        await websocket.close(code=4401)
        return

    await connection_manager.connect(websocket, user_id=user_id)

    try:
        while True:
            message = await websocket.receive_json()
            action = str(message.get("action", "")).upper()
            symbol = message.get("symbol", "")
            timeframe = message.get("timeframe")

            if action == "SUBSCRIBE" and symbol:
                await connection_manager.subscribe(
                    websocket,
                    symbol,
                    timeframe,
                )
                await websocket.send_json(
                    {
                        "type": "subscribed",
                        "symbol": str(symbol).upper(),
                        "timeframe": (
                            str(timeframe).upper() if timeframe else None
                        ),
                        "channel": (
                            f"{str(symbol).upper()}:{str(timeframe).upper()}"
                            if timeframe
                            else str(symbol).upper()
                        ),
                    }
                )

            elif action == "UNSUBSCRIBE" and symbol:
                await connection_manager.unsubscribe(
                    websocket,
                    symbol,
                    timeframe,
                )

            elif action == "PING":
                await websocket.send_json({"type": "PONG"})

            elif action == "AI_CHAT":
                await _handle_ai_chat(websocket, message)

            elif action == "AI_EXPLAIN":
                await _handle_ai_explain(websocket, message)

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        logger.info("WebSocket disconnected.")

    except Exception:
        logger.exception("WebSocket failed.")
        await connection_manager.disconnect(websocket)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_market_websocket(websocket)
