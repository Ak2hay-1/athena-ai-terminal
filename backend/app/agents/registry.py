"""
Agent registry with automatic discovery.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

from app.agents.base import BaseAgent
from app.core.logger import get_logger

logger = get_logger("athena.agents.registry")


class AgentRegistry:
    """
    Register, discover, enable, and disable agents.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.id] = agent
        logger.info(
            "registry action=register agent=%s enabled=%s priority=%s",
            agent.id,
            agent.enabled,
            agent.priority,
        )

    def unregister(self, agent_id: str) -> None:
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("registry action=unregister agent=%s", agent_id)

    def find(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list(self, *, enabled_only: bool = False) -> list[BaseAgent]:
        agents = list(self._agents.values())
        if enabled_only:
            agents = [agent for agent in agents if agent.enabled]
        return sorted(agents, key=lambda agent: agent.priority)

    def enable(self, agent_id: str) -> bool:
        agent = self.find(agent_id)
        if agent is None:
            return False
        agent.enabled = True
        logger.info("registry action=enable agent=%s", agent_id)
        return True

    def disable(self, agent_id: str) -> bool:
        agent = self.find(agent_id)
        if agent is None:
            return False
        agent.enabled = False
        logger.info("registry action=disable agent=%s", agent_id)
        return True

    def clear(self) -> None:
        self._agents.clear()

    def discover(
        self,
        package_name: str = "app.agents",
    ) -> list[type[BaseAgent]]:
        """
        Import subpackages and return concrete BaseAgent subclasses.
        """
        package = importlib.import_module(package_name)
        discovered: dict[str, type[BaseAgent]] = {}

        for module_info in pkgutil.walk_packages(
            package.__path__,
            prefix=f"{package_name}.",
        ):
            name = module_info.name
            # Skip framework modules themselves
            if name in {
                f"{package_name}.base",
                f"{package_name}.registry",
                f"{package_name}.manager",
                f"{package_name}._stub",
            }:
                continue
            if name.rsplit(".", 1)[-1].startswith("_"):
                continue
            try:
                module = importlib.import_module(name)
            except Exception:
                logger.exception(
                    "registry action=discover status=import_error module=%s",
                    name,
                )
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, BaseAgent):
                    continue
                if obj is BaseAgent:
                    continue
                if inspect.isabstract(obj):
                    continue
                if not getattr(obj, "id", None):
                    continue
                discovered[obj.id] = obj

        classes = list(discovered.values())
        logger.info(
            "registry action=discover package=%s count=%s",
            package_name,
            len(classes),
        )
        return classes

    def instantiate_discovered(
        self,
        package_name: str = "app.agents",
    ) -> list[BaseAgent]:
        instances: list[BaseAgent] = []
        for agent_cls in self.discover(package_name):
            instance = agent_cls()
            self.register(instance)
            instances.append(instance)
        return instances

    def health(self) -> dict[str, Any]:
        return {
            "agent_count": len(self._agents),
            "agents": [agent.health() for agent in self.list()],
        }


agent_registry = AgentRegistry()
