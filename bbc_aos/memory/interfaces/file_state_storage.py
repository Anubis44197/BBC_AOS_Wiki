"""
File-based State Storage Implementation - Phase 4
Implements local JSON file-based state serialization.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from bbc_aos.config import BBCConfig
from bbc_aos.memory.interfaces.state_storage_interface import StateStorageInterface

logger = logging.getLogger("bbc_aos.memory.interfaces.file_state_storage")


class FileStateStorage(StateStorageInterface):
    """
    Local JSON file implementation of StateStorageInterface.
    Persists session states under the .bbc/state/ directory.
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """
        Initializes FileStateStorage.

        Args:
            base_dir: Optional custom storage path. Defaults to bbc_dir/state.
        """
        if base_dir is None:
            bbc_dir = BBCConfig.get_bbc_dir()
            base_dir = os.path.join(bbc_dir, "state")
        
        self.base_dir = Path(base_dir)
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create state storage directory '{base_dir}': {e}")

    def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """
        Saves the session state dictionary to a local JSON file.

        Args:
            session_id: Unique identifier for the current session.
            state: The session state metrics dictionary.
        """
        file_path = self.base_dir / f"{session_id}_state.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"Session state saved to '{file_path}'")
        except Exception as e:
            logger.error(f"Failed to save state to '{file_path}': {e}")

    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads the session state dictionary from a local JSON file if it exists.

        Args:
            session_id: Unique identifier for the session to recover.

        Returns:
            The recovered state metrics dictionary, or None if not found/error.
        """
        file_path = self.base_dir / f"{session_id}_state.json"
        if not file_path.exists():
            logger.debug(f"No state file found at '{file_path}'")
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded session state from '{file_path}'")
            return data
        except Exception as e:
            logger.error(f"Failed to load state from '{file_path}': {e}")
            return None
