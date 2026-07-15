"""
Athena WebSocket Connection Manager.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logger import logger


class ConnectionManager:
    """
    Manages websocket clients.

    Supports:

    • Multiple clients
    • Symbol subscriptions
    • Broadcast
    • Disconnect cleanup
    """

    def __init__(self):

        self.connections: list[WebSocket] = []

        self.subscriptions: dict[
            str,
            set[WebSocket],
        ] = defaultdict(set)

        self._lock = asyncio.Lock()

    # -------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
    ):

        await websocket.accept()

        async with self._lock:

            self.connections.append(
                websocket,
            )

        logger.info(
            "WebSocket connected (%d clients)",
            len(self.connections),
        )

    # -------------------------------------------------

    async def disconnect(
        self,
        websocket: WebSocket,
    ):

        async with self._lock:

            if websocket in self.connections:

                self.connections.remove(
                    websocket,
                )

            for clients in self.subscriptions.values():

                clients.discard(
                    websocket,
                )

        logger.info(
            "WebSocket disconnected"
        )

    # -------------------------------------------------

    async def subscribe(

        self,

        websocket: WebSocket,

        symbol: str,

    ):

        async with self._lock:

            self.subscriptions[
                symbol.upper()
            ].add(websocket)

    # -------------------------------------------------

    async def unsubscribe(

        self,

        websocket: WebSocket,

        symbol: str,

    ):

        async with self._lock:

            self.subscriptions[
                symbol.upper()
            ].discard(websocket)

    # -------------------------------------------------

    async def send(

        self,

        websocket: WebSocket,

        payload: dict,

    ):

        try:

            await websocket.send_json(
                payload,
            )

        except Exception:

            await self.disconnect(
                websocket,
            )

    # -------------------------------------------------

    async def broadcast(

        self,

        payload: dict,

    ):

        for websocket in list(
            self.connections,
        ):

            await self.send(
                websocket,
                payload,
            )

    # -------------------------------------------------

    async def broadcast_symbol(

        self,

        symbol: str,

        payload: dict,

    ):

        clients = self.subscriptions.get(

            symbol.upper(),

            set(),

        )

        for websocket in list(clients):

            await self.send(
                websocket,
                payload,
            )


connection_manager = ConnectionManager()