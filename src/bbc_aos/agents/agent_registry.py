from typing import Dict, Type, Optional
from bbc_aos.agents.base_agent import BaseAgent

class AgentRegistry:
    """
    Singleton registry class that manages class mappings for all registered agents.
    """
    _instance: Optional['AgentRegistry'] = None
    
    def __new__(cls) -> 'AgentRegistry':
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def register(self, agent_cls: Type[BaseAgent]) -> None:
        """
        Registers an agent class using its static AGENT_ID.
        """
        agent_id = agent_cls.AGENT_ID
        if agent_id in self._registry:
            raise ValueError(f"Agent '{agent_id}' is already registered.")
        self._registry[agent_id] = agent_cls

    def get_agent_cls(self, agent_id: str) -> Type[BaseAgent]:
        """
        Retrieves the registered agent class.
        
        Raises:
            KeyError: If agent_id is not registered.
        """
        if agent_id not in self._registry:
            raise KeyError(f"Agent '{agent_id}' is not registered.")
        return self._registry[agent_id]

    def reset(self) -> None:
        """Resets the registry map (primarily for testing purposes)."""
        self._registry.clear()
