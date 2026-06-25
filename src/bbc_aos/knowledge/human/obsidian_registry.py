from typing import Dict, Any, Type
from bbc_aos.knowledge.human.obsidian_exceptions import ObsidianFrozenRegistryException

class ObsidianRegistry:
    """
    Registry for allowed Obsidian vault scopes and directories in bbc_aos.
    Ensures namespace uniqueness and freezes configurations post-startup.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ObsidianRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._vaults: Dict[str, str] = {}
        self._frozen: bool = False
        self._initialized = True

    def register_vault(self, name: str, directory_path: str) -> None:
        """
        Registers a vault scope key with its local directory path.
        
        Args:
            name: Unique name of the vault scope.
            directory_path: Directory path of the vault.
            
        Raises:
            ObsidianFrozenRegistryException: If the registry is frozen.
            ValueError: If the vault name is already registered.
        """
        if self._frozen:
            raise ObsidianFrozenRegistryException("Cannot register vault: registry is frozen")
        if name in self._vaults:
            raise ValueError(f"Vault scope '{name}' is already registered")
        self._vaults[name] = directory_path

    def freeze(self) -> None:
        """locks the registry against further registrations."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Returns True if the registry is frozen."""
        return self._frozen

    def get_vault_path(self, name: str) -> str:
        """Retrieves a registered vault directory path by key name."""
        return self._vaults[name]

    def reset(self) -> None:
        """Resets the registry (useful for fresh test environments)."""
        self._vaults.clear()
        self._frozen = False
