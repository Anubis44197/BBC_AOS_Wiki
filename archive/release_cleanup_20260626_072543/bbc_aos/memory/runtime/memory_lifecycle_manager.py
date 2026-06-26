import logging
from typing import Dict, Set
from bbc_aos.memory.runtime.memory_exceptions import MemoryLifecycleException

logger = logging.getLogger("bbc_aos.memory.runtime.memory_lifecycle_manager")

class MemoryLifecycleManager:
    """
    Manages deterministic states of a memory record.
    Supported states: CREATED, INDEXED, ACTIVE, ARCHIVED, FROZEN, DEPRECATED.
    """
    CREATED = "CREATED"
    INDEXED = "INDEXED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    FROZEN = "FROZEN"
    DEPRECATED = "DEPRECATED"

    # Define valid transitions
    TRANSITIONS: Dict[str, Set[str]] = {
        CREATED: {INDEXED, DEPRECATED},
        INDEXED: {ACTIVE, DEPRECATED},
        ACTIVE: {ARCHIVED, FROZEN, DEPRECATED},
        ARCHIVED: {DEPRECATED},
        FROZEN: {DEPRECATED},
        DEPRECATED: set()
    }

    def __init__(self) -> None:
        self._record_states: Dict[str, str] = {}

    def get_state(self, memory_id: str) -> str:
        """Retrieves active lifecycle state of a record."""
        return self._record_states.get(memory_id, self.CREATED)

    def transition_to(self, memory_id: str, target_state: str, reason: str = "") -> None:
        """
        Transitions record state to target_state.
        
        Args:
            memory_id: Target record ID.
            target_state: Target state name.
            reason: Explanation of the transition.
            
        Raises:
            MemoryLifecycleException: If the transition is illegal.
        """
        current_state = self._record_states.get(memory_id, self.CREATED)
        
        if target_state not in self.TRANSITIONS.get(current_state, set()):
            error_msg = f"Invalid memory lifecycle transition: {current_state} -> {target_state} (Record: {memory_id})"
            logger.error(f"[LIFECYCLE ERROR] {error_msg}")
            raise MemoryLifecycleException(error_msg)

        self._record_states[memory_id] = target_state
        logger.info(f"[LIFECYCLE TRANSITION] {current_state} -> {target_state} for record '{memory_id}' | Reason: {reason or 'none'}")
