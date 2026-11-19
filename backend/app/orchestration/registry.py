"""Agent Registry for OpenReview AI.

Enables extensible agent registration so new review agents (specialist or arbiter)
can be registered dynamically without modifying the LangGraph topology.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type


@dataclass
class AgentMetadata:
    """Metadata describing an agent's capabilities and role in the review engine."""

    name: str
    role: str
    category: str  # bug, security, performance, architecture, test, critique, verification, context
    description: str
    is_specialist: bool = True  # True if runs during the parallel specialist pass
    priority: int = 100  # Lower number = higher execution priority
    model_name: Optional[str] = None
    timeout_seconds: float = 45.0
    tags: List[str] = field(default_factory=list)


class AgentRegistry:
    """Thread-safe registry for AI review agents."""

    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, agent: Any, metadata: AgentMetadata):
        """Registers a new agent instance or class along with its metadata."""
        key = metadata.name.lower().strip()
        self._agents[key] = agent
        self._metadata[key] = metadata

    def get(self, name: str) -> Optional[Any]:
        """Retrieves an agent by name."""
        return self._agents.get(name.lower().strip())

    def get_metadata(self, name: str) -> Optional[AgentMetadata]:
        """Retrieves metadata for an agent by name."""
        return self._metadata.get(name.lower().strip())

    def list_specialists(self) -> List[Tuple[Any, AgentMetadata]]:
        """Returns all agents flagged as specialists for the parallel review pass."""
        specialists = [
            (self._agents[key], meta)
            for key, meta in self._metadata.items()
            if meta.is_specialist
        ]
        specialists.sort(key=lambda pair: pair[1].priority)
        return specialists

    def list_all(self) -> List[AgentMetadata]:
        """Returns metadata for all registered agents."""
        items = list(self._metadata.values())
        items.sort(key=lambda m: m.priority)
        return items

    def unregister(self, name: str) -> bool:
        """Removes an agent from the registry."""
        key = name.lower().strip()
        if key in self._agents:
            del self._agents[key]
            del self._metadata[key]
            return True
        return False


# Global singleton instance
_registry_instance: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Returns the global agent registry singleton."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance
