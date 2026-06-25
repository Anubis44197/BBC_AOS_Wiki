class ObsidianException(Exception):
    """Base exception for all Obsidian subsystem operations."""
    ERROR_CODE = -34000
    ERROR_MESSAGE = "Obsidian integration error"

    def __init__(self, message: str = None) -> None:
        super().__init__(message or self.ERROR_MESSAGE)


class ObsidianFrozenRegistryException(ObsidianException):
    """Raised when trying to modify the registry after startup."""
    ERROR_CODE = -34001
    ERROR_MESSAGE = "Obsidian registry is frozen"


class ObsidianNoteLifecycleException(ObsidianException):
    """Raised when an invalid note state transition is attempted."""
    ERROR_CODE = -34002
    ERROR_MESSAGE = "Invalid note lifecycle transition"


class ObsidianSyncException(ObsidianException):
    """Raised when synchronization validation or verification fails."""
    ERROR_CODE = -34003
    ERROR_MESSAGE = "Obsidian synchronization failure"


class ObsidianSandboxViolationException(ObsidianException):
    """Raised when directory writes or unauthorized edits are detected."""
    ERROR_CODE = -34004
    ERROR_MESSAGE = "Obsidian sandbox boundary breach"
