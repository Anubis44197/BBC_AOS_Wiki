import logging
from typing import Set, Dict
from bbc_aos.loops.loop_exceptions import LoopStateMachineException

logger = logging.getLogger("bbc_aos.loops.loop_state_machine")

class LoopStateMachine:
    """
    State machine governing the lifecycle transitions of a Loop execution.
    Transitions are deterministic, validated against an allowlist, and fully logged.
    """
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

    # Define valid transitions: source -> set of targets
    TRANSITIONS: Dict[str, Set[str]] = {
        CREATED: {READY, FAILED},
        READY: {RUNNING, FAILED},
        RUNNING: {WAITING_APPROVAL, RETRYING, COMPLETED, FAILED, TERMINATED},
        WAITING_APPROVAL: {RUNNING, TERMINATED},
        RETRYING: {RUNNING, FAILED},
        COMPLETED: set(),
        FAILED: set(),
        TERMINATED: set(),
    }

    def __init__(self) -> None:
        self._current_state: str = self.CREATED
        self._history = [(self._current_state, "Initialization")]

    @property
    def current_state(self) -> str:
        """Returns the current loop state."""
        return self._current_state

    @property
    def history(self):
        """Returns the transition history list."""
        return self._history

    def transition_to(self, target_state: str, reason: str = "") -> None:
        """
        Transitions the state machine to target_state if valid.
        
        Args:
            target_state: The state to transition to.
            reason: Contextual explanation for the state change.
            
        Raises:
            LoopStateMachineException: If transition is invalid.
        """
        if target_state not in self.TRANSITIONS.get(self._current_state, set()):
            error_msg = f"Invalid state transition: {self._current_state} -> {target_state}"
            logger.error(f"[STATE MACHINE ERROR] {error_msg}")
            raise LoopStateMachineException(error_msg)

        old_state = self._current_state
        self._current_state = target_state
        self._history.append((target_state, reason))
        
        logger.info(
            f"[STATE TRANSITION] {old_state} -> {target_state} | Reason: {reason or 'none'}"
        )
