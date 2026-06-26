"""
BBC Memory Interfaces - Phase 4
Exposes the storage contracts and default file-based persistence layers.
"""

from bbc_aos.memory.interfaces.state_storage_interface import StateStorageInterface
from bbc_aos.memory.interfaces.file_state_storage import FileStateStorage

__all__ = ["StateStorageInterface", "FileStateStorage"]
