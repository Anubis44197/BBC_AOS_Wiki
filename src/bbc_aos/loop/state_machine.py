"""BBC-AOS daemon loop state machine."""

from enum import Enum
from typing import Dict, Set


class LoopState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    FAILED_FINAL = "FAILED_FINAL"


class LoopStateMachine:
    """Strict transition table for daemon loop execution."""

    TRANSITIONS: Dict[LoopState, Set[LoopState]] = {
        LoopState.IDLE: {LoopState.RUNNING},
        LoopState.RUNNING: {LoopState.VERIFYING, LoopState.FAILED},
        LoopState.VERIFYING: {LoopState.COMMITTED, LoopState.REJECTED, LoopState.FAILED},
        LoopState.COMMITTED: {LoopState.IDLE},
        LoopState.REJECTED: {LoopState.IDLE},
        LoopState.FAILED: {LoopState.RECOVERING, LoopState.FAILED_FINAL},
        LoopState.RECOVERING: {LoopState.IDLE, LoopState.FAILED_FINAL},
        LoopState.FAILED_FINAL: set(),
    }

    def __init__(self) -> None:
        self.state = LoopState.IDLE

    def transition(self, target: LoopState) -> LoopState:
        if target not in self.TRANSITIONS[self.state]:
            raise ValueError(f"Invalid loop transition: {self.state.value} -> {target.value}")
        self.state = target
        return self.state

    def reset(self) -> LoopState:
        self.state = LoopState.IDLE
        return self.state
