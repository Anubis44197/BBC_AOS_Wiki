from typing import Dict, Any, Type
from bbc_aos.loops.loop_exceptions import LoopFrozenRegistryException

class LoopRegistry:
    """
    Registry for allowed Loop Engine execution runtimes.
    Ensures uniqueness of registered runtimes and freezes post-startup.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LoopRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._runtimes: Dict[str, Type] = {}
        self._frozen: bool = False
        self._initialized = True

    def register(self, name: str, runtime_cls: Type) -> None:
        """
        Registers a loop runtime under a unique name.
        
        Args:
            name: Unique name of the runtime.
            runtime_cls: Class reference for the runtime.
            
        Raises:
            LoopFrozenRegistryException: If the registry is already frozen.
            ValueError: If the name is already registered.
        """
        if self._frozen:
            raise LoopFrozenRegistryException("Cannot register runtime: registry is frozen")
        if name in self._runtimes:
            raise ValueError(f"Runtime '{name}' is already registered")
        self._runtimes[name] = runtime_cls

    def freeze(self) -> None:
        """Freezes the registry to prevent further registrations."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Returns True if the registry is frozen."""
        return self._frozen

    def get(self, name: str) -> Type:
        """
        Retrieves a registered loop runtime class by name.
        
        Args:
            name: Registered name of the runtime.
            
        Returns:
            Type: The runtime class reference.
            
        Raises:
            KeyError: If the runtime name is not found.
        """
        return self._runtimes[name]

    def reset(self) -> None:
        """Resets the registry (useful for clean testing environments)."""
        self._runtimes.clear()
        self._frozen = False
