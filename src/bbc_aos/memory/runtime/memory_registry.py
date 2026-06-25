from typing import Dict, Type
from bbc_aos.memory.runtime.memory_exceptions import MemoryFrozenRegistryException

class MemoryRegistry:
    """
    Registry for authorized Memory layers and retrieval modules in bbc_aos.
    Ensures layer uniqueness and locks configuration post-startup.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MemoryRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._layers: Dict[str, Type] = {}
        self._frozen: bool = False
        self._initialized = True

    def register_layer(self, name: str, layer_cls: Type) -> None:
        """
        Registers a memory layer under a unique namespace key.
        
        Args:
            name: The namespace key of the layer (e.g. 'episodic').
            layer_cls: The class reference of the layer.
            
        Raises:
            MemoryFrozenRegistryException: If the registry is frozen.
            ValueError: If the layer namespace is already registered.
        """
        if self._frozen:
            raise MemoryFrozenRegistryException("Cannot register memory layer: registry is frozen")
        if name in self._layers:
            raise ValueError(f"Layer '{name}' is already registered")
        self._layers[name] = layer_cls

    def freeze(self) -> None:
        """Locks the registry against further registrations."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Returns True if the registry is frozen."""
        return self._frozen

    def get_layer(self, name: str) -> Type:
        """Retrieves a layer class reference by key name."""
        return self._layers[name]

    def reset(self) -> None:
        """Resets the registry mappings (useful for fresh test setups)."""
        self._layers.clear()
        self._frozen = False
