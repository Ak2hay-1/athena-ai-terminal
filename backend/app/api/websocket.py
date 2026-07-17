"""
Athena WebSocket API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.core.logger import logger
from app.websocket.connection_manager import connection_manager

router = APIRouter(tags=["WebSocket"])


async def handle_market_websocket(websocket: WebSocket) -> None:
    """Shared market stream handler used by app-level and router mounts."""

    await connection_manager.connect(websocket)

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

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        logger.info("WebSocket disconnected.")

    except Exception:
        logger.exception("WebSocket failed.")
        await connection_manager.disconnect(websocket)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_market_websocket(websocket)
