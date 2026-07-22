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

        self.user_connections: dict[int, set[WebSocket]] = defaultdict(set)

        self._socket_users: dict[int, int] = {}

        self._lock = asyncio.Lock()

    # -------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
        *,
        user_id: int | None = None,
    ):

        await websocket.accept()

        async with self._lock:

            self.connections.append(
                websocket,
            )
            if user_id is not None:
                self.user_connections[user_id].add(websocket)
                self._socket_users[id(websocket)] = user_id

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

            user_id = self._socket_users.pop(id(websocket), None)
            if user_id is not None:
                sockets = self.user_connections.get(user_id)
                if sockets is not None:
                    sockets.discard(websocket)
                    if not sockets:
                        self.user_connections.pop(user_id, None)

        logger.info(
            "WebSocket disconnected"
        )

    async def send_to_user(
        self,
        user_id: int,
        payload: dict,
    ) -> int:
        """Send payload to all sockets for a user. Returns recipient count."""
        async with self._lock:
            clients = list(self.user_connections.get(user_id, set()))
        sent = 0
        for websocket in clients:
            await self.send(websocket, payload)
            sent += 1
        return sent

    # -------------------------------------------------

    async def subscribe(
        self,
        websocket: WebSocket,
        symbol: str,
        timeframe: str | None = None,
    ):

        channel = (
            f"{symbol.upper()}:{timeframe.upper()}"
            if timeframe
            else symbol.upper()
        )

        async with self._lock:

            self.subscriptions[channel].add(websocket)

    async def unsubscribe(
        self,
        websocket: WebSocket,
        symbol: str,
        timeframe: str | None = None,
    ):

        channel = (
            f"{symbol.upper()}:{timeframe.upper()}"
            if timeframe
            else symbol.upper()
        )

        async with self._lock:

            self.subscriptions[channel].discard(websocket)

    async def broadcast_channel(
        self,
        channel: str,
        payload: dict,
    ):

        clients = self.subscriptions.get(
            channel.upper(),
            set(),
        )

        for websocket in list(clients):

            await self.send(
                websocket,
                payload,
            )

        if clients:
            return

        symbol = channel.split(":")[0]

        await self.broadcast_symbol(
            symbol,
            payload,
        )

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

    async def broadcast_for_symbol(
        self,
        symbol: str,
        payload: dict,
    ) -> None:
        """
        Send to every subscriber of SYMBOL or SYMBOL:TIMEFRAME.
        """
        symbol = symbol.upper()
        prefix = f"{symbol}:"

        async with self._lock:
            clients: set[WebSocket] = set()
            for channel, sockets in self.subscriptions.items():
                if channel == symbol or channel.startswith(prefix):
                    clients |= sockets

        for websocket in list(clients):
            await self.send(websocket, payload)


connection_manager = ConnectionManager()