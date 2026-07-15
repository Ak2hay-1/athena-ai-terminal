"""
Athena WebSocket API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.core.logger import logger
from app.websocket.connection_manager import (
    connection_manager,
)

router = APIRouter(
    tags=["WebSocket"],
)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await connection_manager.connect(
        websocket,
    )

    try:

        while True:

            message = await websocket.receive_json()

            action = message.get(
                "action",
                "",
            ).upper()

            # ---------------------------------
            # Subscribe
            # ---------------------------------

            if action == "SUBSCRIBE":

                symbol = message.get(
                    "symbol",
                    "",
                )

                if symbol:

                    await connection_manager.subscribe(

                        websocket,

                        symbol,

                    )

                    await websocket.send_json(

                        {

                            "type": "subscribed",

                            "symbol": symbol,

                        }

                    )

            # ---------------------------------
            # Unsubscribe
            # ---------------------------------

            elif action == "UNSUBSCRIBE":

                symbol = message.get(
                    "symbol",
                    "",
                )

                if symbol:

                    await connection_manager.unsubscribe(

                        websocket,

                        symbol,

                    )

            # ---------------------------------
            # Heartbeat
            # ---------------------------------

            elif action == "PING":

                await websocket.send_json(

                    {

                        "type": "PONG",

                    }

                )

    except WebSocketDisconnect:

        await connection_manager.disconnect(
            websocket,
        )

        logger.info(
            "WebSocket disconnected."
        )

    except Exception:

        logger.exception(
            "WebSocket failed."
        )

        await connection_manager.disconnect(
            websocket,
        )