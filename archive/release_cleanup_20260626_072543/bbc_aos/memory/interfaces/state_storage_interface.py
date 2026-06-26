"""
State Storage Interface - Phase 4
Defines the contract for persisting and recovering session-level state metrics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class StateStorageInterface(ABC):
    """
    Contract for state persistence backends.
    Any memory backend (JSON, SQLite, Redis, Vector DB) must implement this interface.
    """

    @abstractmethod
    def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """
        Saves the state dictionary for a given session.

        Args:
            session_id: Unique identifier for the current session.
            state: The session state metrics dictionary.
        """
        pass

    @abstractmethod
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads the state dictionary for a given session.

        Args:
            session_id: Unique identifier for the session to recover.

        Returns:
            The recovered state metrics dictionary, or None if not found.
        """
        pass
