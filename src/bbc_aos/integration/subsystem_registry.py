from typing import Dict, Any
from bbc_aos.integration.integration_exceptions import IntegrationFrozenRegistryException

class SubsystemRegistry:
    """
    Registry for allowed BBC-AOS subsystems.
    Enforces uniqueness of registered subsystems and freezes modifications post-startup.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SubsystemRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._subsystems: Dict[str, Any] = {}
        self._frozen: bool = False
        self._initialized = True

    def register_subsystem(self, name: str, subsystem_instance: Any) -> None:
        """
        Registers a subsystem gateway or manager instance under a unique name key.
        
        Args:
            name: Subsystem identifier key (e.g. 'memory', 'knowledge').
            subsystem_instance: The runtime instance of the subsystem.
            
        Raises:
            IntegrationFrozenRegistryException: If the registry is frozen.
            ValueError: If the subsystem key is already registered.
        """
        if self._frozen:
            raise IntegrationFrozenRegistryException("Cannot register subsystem: registry is frozen")
        if name in self._subsystems:
            raise ValueError(f"Subsystem '{name}' is already registered")
        self._subsystems[name] = subsystem_instance

    def freeze(self) -> None:
        """Locks the registry against further registrations."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Returns True if the registry is frozen."""
        return self._frozen

    def get_subsystem(self, name: str) -> Any:
        """Retrieves a registered subsystem instance by name key."""
        return self._subsystems[name]

    def reset(self) -> None:
        """Resets the registry (useful for fresh test environments)."""
        self._subsystems.clear()
        self._frozen = False
