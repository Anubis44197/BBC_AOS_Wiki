from typing import Dict, Set
from bbc_aos.memory.runtime.memory_exceptions import MemoryVisibilityException

class MemoryVisibilityPolicy:
    """
    Defines read/write permission scopes for memory records.
    Restricts access across three actor roles: agents, loops, and humans.
    """
    def __init__(self) -> None:
        # Define allowed reads per layer
        self.read_scopes: Dict[str, Set[str]] = {
            "working": {"agent", "loop", "human"},
            "episodic": {"agent", "loop"},
            "semantic": {"agent", "loop", "human"},
            "human_knowledge": {"agent", "human"},
            "experience": {"agent"},
        }
        
        # Define allowed writes per layer
        self.write_scopes: Dict[str, Set[str]] = {
            "working": {"loop"},
            "episodic": {"loop"},
            "semantic": {"human"},  # Modified via manual approval only
            "human_knowledge": {"human"},  # System cannot write directly
            "experience": {"loop"},
        }

    def check_read_permission(self, actor_role: str, layer: str) -> None:
        """
        Validates read access for actor_role on target layer.
        
        Raises:
            MemoryVisibilityException: If read is forbidden.
        """
        allowed = self.read_scopes.get(layer, set())
        if actor_role not in allowed:
            raise MemoryVisibilityException(
                f"Read forbidden: Actor '{actor_role}' has no visibility on memory layer '{layer}'"
            )

    def check_write_permission(self, actor_role: str, layer: str) -> None:
        """
        Validates write access for actor_role on target layer.
        
        Raises:
            MemoryVisibilityException: If write is forbidden.
        """
        allowed = self.write_scopes.get(layer, set())
        if actor_role not in allowed:
            raise MemoryVisibilityException(
                f"Write forbidden: Actor '{actor_role}' has no edit visibility on memory layer '{layer}'"
            )
