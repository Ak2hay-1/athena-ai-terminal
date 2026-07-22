"""
Agent manager — lifecycle, dispatch, configuration, metrics.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.bus import AsyncEventBus
from app.events.bus import event_bus
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.memory.service import MemoryService
from app.scheduler.jobs import register_default_agent_jobs
from app.scheduler.scheduler import AgentScheduler
from app.tools.manager import ToolManager
from app.tools.stubs import create_default_tools

logger = get_logger("athena.agents.manager")


class AgentManager:
    """
    Starts/stops agents, loads config, routes events, isolates errors.

    Uses the shared process-wide ``event_bus`` by default so publishers
    (e.g. market_data_engine via ``schedule_publish``) and agent
    subscribers share one bus.
    """

    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        bus: AsyncEventBus | None = None,
        tool_manager: ToolManager | None = None,
        scheduler: AgentScheduler | None = None,
        memory_service: MemoryService | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.bus = bus if bus is not None else event_bus
        self.tool_manager = tool_manager or ToolManager()
        self.scheduler = scheduler or AgentScheduler()
        self.memory_service = memory_service or MemoryService()
        self.publisher = EventPublisher(self.bus)
        self._started = False
        self._handler_bindings: list[tuple[str, Any]] = []

    @property
    def started(self) -> bool:
        return self._started

    async def start(self) -> None:
        if self._started:
            logger.info("agent_manager action=start status=already_started")
            return

        if not settings.AGENTS_ENABLED:
            logger.info(
                "agent_manager action=start status=skipped reason=AGENTS_ENABLED=false"
            )
            return

        # Tools
        for tool in create_default_tools(memory_service=self.memory_service):
            self.tool_manager.register(tool)

        # Discover and register agents
        self.registry.clear()
        self.registry.instantiate_discovered("app.agents")

        disabled = {item.strip() for item in settings.AGENTS_DISABLED if item.strip()}
        for agent in self.registry.list():
            if agent.id in disabled:
                agent.enabled = False
                logger.info(
                    "agent_manager action=config agent=%s enabled=false",
                    agent.id,
                )
            agent.bind_tools(self.tool_manager)
            agent.bind_publisher(self.publisher)

        # Initialize enabled agents and subscribe
        for agent in self.registry.list(enabled_only=True):
            try:
                await agent.initialize()
                self._subscribe_agent(agent)
            except Exception:
                logger.exception(
                    "agent_manager action=initialize agent=%s status=error",
                    agent.id,
                )

        # Scheduler heartbeats
        register_default_agent_jobs(self.scheduler, self.publisher)
        self.scheduler.start()

        self._started = True
        logger.info(
            "agent_manager action=start status=ok agents=%s",
            len(self.registry.list(enabled_only=True)),
        )

    async def shutdown(self) -> None:
        if not self._started and not settings.AGENTS_ENABLED:
            return

        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            logger.exception("agent_manager action=scheduler_shutdown status=error")

        for event_type, handler in list(self._handler_bindings):
            self.bus.unsubscribe(event_type, handler)
        self._handler_bindings.clear()

        for agent in reversed(self.registry.list()):
            try:
                await agent.shutdown()
            except Exception:
                logger.exception(
                    "agent_manager action=shutdown agent=%s status=error",
                    agent.id,
                )

        self._started = False
        logger.info("agent_manager action=shutdown status=ok")

    def _subscribe_agent(self, agent: BaseAgent) -> None:
        async def _handler(event: Event) -> None:
            await self._dispatch_to_agent(agent, event)

        for event_type in agent.subscribed_events:
            key = str(event_type)
            self.bus.subscribe(key, _handler)
            self._handler_bindings.append((key, _handler))

    async def _dispatch_to_agent(self, agent: BaseAgent, event: Event) -> None:
        if not agent.enabled:
            return
        try:
            await agent.process_event(event)
        except Exception:
            # Error already logged in process_event; isolate from other agents
            logger.error(
                "agent_manager action=dispatch agent=%s event_id=%s status=isolated_error",
                agent.id,
                event.id,
            )

    async def publish(self, event: Event) -> list[Any]:
        return await self.bus.publish(event)

    async def broadcast(self, event: Event) -> list[Any]:
        return await self.bus.broadcast(event)

    async def publish_type(
        self,
        event_type: EventType | str,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        return await self.publisher.publish(
            event_type,
            source=source,
            payload=payload,
            correlation_id=correlation_id,
            metadata=metadata,
        )

    def health(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "agents_enabled_flag": settings.AGENTS_ENABLED,
            "agents": [agent.health() for agent in self.registry.list()],
            "tools": self.tool_manager.health(),
            "scheduler": self.scheduler.status(),
            "bus": self.bus.metrics(),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "agents": [agent.metrics() for agent in self.registry.list()],
            "bus": self.bus.metrics(),
            "queue_length": self.bus.queue_depth,
        }


agent_manager = AgentManager()
