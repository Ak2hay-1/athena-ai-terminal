"""
Base tool interface for agents.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Tools are the only way agents interact with external capabilities.
    """

    id: str
    name: str
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Run the tool and return a structured result."""

    def health(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": "ready",
        }
