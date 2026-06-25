"""
BBC State Manager - Phase 4
Maintains session-level metadata, heal budgets, token tracking metrics,
degenerate event statistics, and interfaces with structured telemetry logging.
Persists session states via pluggable StateStorageInterface implementations.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import centralized configuration layer
from bbc_aos.config import BBCConfig

# Import storage interfaces
from bbc_aos.memory.interfaces import StateStorageInterface, FileStateStorage

# Set up logging namespace
logger = logging.getLogger("bbc_aos.memory.working.state_manager")


class TelemetryLogger:
    """
    Lightweight telemetry logger that records structured event JSON lines
    to .bbc/logs/telemetry.jsonl.
    """
    
    def __init__(self, log_path: Optional[str] = None) -> None:
        """
        Initializes TelemetryLogger.

        Args:
            log_path: Explicit file path for event logging. Defaults to bbc_dir/logs/telemetry.jsonl.
        """
        if log_path is None:
            bbc_dir = BBCConfig.get_bbc_dir()
            log_path = os.path.join(bbc_dir, "logs", "telemetry.jsonl")
        try:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create telemetry parent directory for '{log_path}': {e}")
        self.log_path: str = log_path
        self.session_id: Optional[str] = None
        self._event_count: int = 0

    def set_session(self, session_id: str) -> None:
        """Sets the active session identifier."""
        self.session_id = session_id

    def log_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Logs a structured telemetry event to disk.

        Args:
            event_type: Event type keyword.
            data: Arbitrary metadata key-values.
        """
        event = {
            "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event_type,
            "data": data or {},
        }
        if self.session_id:
            event["session"] = self.session_id

        self._event_count += 1
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Telemetry write failed: {e}")


# Initialize global telemetry logger instance
_tele = TelemetryLogger()


class StateManager:
    """
    StateManager governs central session statistics, token savings,
    and budgets. Implements a thread-safe singleton design.
    """
    _instance: Optional['StateManager'] = None

    def __new__(cls, heal_budget: int = 100, session_heal_budget: int = 100, 
                db_path: Optional[str] = None, project_path: Optional[str] = None,
                storage: Optional[StateStorageInterface] = None) -> 'StateManager':
        """
        Retrieves or instantiates the StateManager singleton instance.

        Args:
            heal_budget: Global heal limit budget.
            session_heal_budget: Session-specific budget limit.
            db_path: Unused legacy parameter.
            project_path: Optional codebase workspace root path.
            storage: Custom persistence backend implementing StateStorageInterface.
        """
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.storage = storage or FileStateStorage()
            cls._instance.heal_budget = heal_budget
            cls._instance.session_heal_budget = session_heal_budget
            cls._instance.degenerate_count = 0
            cls._instance.tokens_used = 0
            cls._instance.token_savings = 0
            cls._instance.files_processed = 0
            cls._instance.recipes_created = 0
            cls._instance.data_processed = 0
            cls._instance.project_path = project_path
            cls._instance.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            logger.info(f"--- NEW SESSION STARTED (ID: {cls._instance.session_id}) ---")
            logger.info("--- ENGINE: BBC Master v8.6 (7-State + Telemetry) ---")
            
            _tele.set_session(cls._instance.session_id)
            _tele.log_event("SESSION_START", {
                "session_id": cls._instance.session_id,
                "heal_budget": heal_budget,
                "session_heal_budget": session_heal_budget,
                "project_path": project_path or ""
            })
            if project_path:
                logger.info(f"--- PROJECT: {project_path} ---")
            
            cls._instance._save_state()
        return cls._instance

    def _save_state(self) -> None:
        """Helper to invoke save_state on the storage backend contract."""
        if hasattr(self, 'storage') and self.storage:
            try:
                self.storage.save_state(self.session_id, self.get_stats())
            except Exception as e:
                logger.error(f"Error persisting session state: {e}")

    def request_heal(self, origin_info: str = "unknown") -> bool:
        """
        Requests permission to perform a scalar/equation healing operation.

        Args:
            origin_info: Context string describing the request source.

        Returns:
            True if within budget, False if budget is exhausted.
        """
        if self.heal_budget > 0:
            self.heal_budget -= 1
            logger.info(f"[HEAL APPROVED] Source: {origin_info} | Remaining: {self.heal_budget}")
            _tele.log_event("HEAL_APPROVED", {"source": origin_info, "remaining": self.heal_budget})
            self._save_state()
            return True
        else:
            logger.warning(f"[HEAL DENIED] Budget exhausted! Source: {origin_info}")
            _tele.log_event("HEAL_DENIED", {"source": origin_info})
            self._save_state()
            return False

    def consume_heal_budget(self) -> int:
        """
        Consumes one heal from the session budget.

        Returns:
            1 if successfully consumed, -2 if budget is exhausted.
        """
        if self.session_heal_budget > 0:
            self.session_heal_budget -= 1
            logger.info(f"[HEAL CONSUMED] Remaining session budget: {self.session_heal_budget}")
            _tele.log_event("HEAL_CONSUMED", {"remaining": self.session_heal_budget})
            self._save_state()
            return 1
        else:
            logger.warning("[HEAL DENIED] Session heal budget exhausted!")
            _tele.log_event("HEAL_DENIED", {"type": "session_budget"})
            self._save_state()
            return -2

    def record_degenerate(self, origin_info: str = "unknown") -> None:
        """
        Records a DEGENERATE (critical system drift or exception) event.

        Args:
            origin_info: Identification of source triggering degeneration.
        """
        self.degenerate_count += 1
        logger.critical(f"[DEGENERATE] CRITICAL! Source: {origin_info} | Total: {self.degenerate_count}")
        _tele.log_event("DEGENERATE", {"source": origin_info, "total": self.degenerate_count})
        self._save_state()

    def update_tokens(self, used: int = 0, saved: int = 0, files: int = 0) -> None:
        """Updates cumulative token consumption metrics."""
        self.tokens_used += used
        self.token_savings += saved
        self.files_processed += files
        self._save_state()

    def increment_files_analyzed(self) -> None:
        """Increments total files analyzed metric."""
        self.files_processed += 1
        self._save_state()

    def increment_recipes_created(self) -> None:
        """Increments total recipes created metric."""
        if not hasattr(self, 'recipes_created'):
            self.recipes_created = 0
        self.recipes_created += 1
        self._save_state()

    def add_data_processed(self, bytes_count: int) -> None:
        """Adds to total bytes processed metric."""
        if not hasattr(self, 'data_processed'):
            self.data_processed = 0
        self.data_processed += bytes_count
        self._save_state()

    def add_token_savings(self, tokens: float) -> None:
        """Adds to total estimated tokens saved metric."""
        self.token_savings += int(tokens)
        self._save_state()

    @property
    def stats(self) -> Dict[str, Any]:
        """Property shortcut mapping to get_stats()."""
        return self.get_stats()

    def reset_session(self) -> None:
        """Resets statistics and initializes a new session ID."""
        self.degenerate_count = 0
        self.tokens_used = 0
        self.token_savings = 0
        self.files_processed = 0
        self.recipes_created = 0
        self.data_processed = 0
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"--- SESSION RESET (ID: {self.session_id}) ---")
        _tele.set_session(self.session_id)
        _tele.log_event("SESSION_RESET", {"session_id": self.session_id})
        self._save_state()

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Resets the singleton reference (testing hook)."""
        cls._instance = None

    def get_stats(self) -> Dict[str, Any]:
        """Compiles a dictionary of current session parameters."""
        return {
            "session_id": self.session_id,
            "tokens_used": self.tokens_used,
            "token_savings": self.token_savings,
            "files_processed": self.files_processed,
            "recipes_created": getattr(self, 'recipes_created', 0),
            "data_processed": getattr(self, 'data_processed', 0),
            "heal_budget": self.heal_budget,
            "session_heal_budget": self.session_heal_budget,
            "degenerate_count": self.degenerate_count,
            "degenerate_seen_total": self.degenerate_count
        }

    def close(self) -> None:
        """Traces the termination event of the current session."""
        logger.info(f"--- SESSION ENDED (ID: {self.session_id}) ---")
        _tele.log_event("SESSION_END", self.get_stats())
        self._save_state()
