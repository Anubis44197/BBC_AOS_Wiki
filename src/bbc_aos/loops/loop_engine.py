import inspect
import time
import logging
from typing import Any, Dict, Optional, Callable
from bbc_aos.loops.loop_exceptions import LoopSafetyViolationException, LoopException, LoopStateMachineException
from bbc_aos.loops.loop_context import LoopContext
from bbc_aos.loops.loop_checkpoint import LoopCheckpoint
from bbc_aos.loops.loop_result import LoopResult
from bbc_aos.loops.loop_state_machine import LoopStateMachine
from bbc_aos.loops.loop_supervisor import LoopSupervisor
from bbc_aos.loops.loop_policy import LoopPolicy
from bbc_aos.loops.loop_budget import LoopBudget

logger = logging.getLogger("bbc_aos.loops.loop_engine")

class LoopEngine:
    """
    The only authorized executable loop runtime in bbc_aos.
    Can only be invoked by AgentOrchestrator. Implements strict state machine,
    checkpoints, budget audits, and observability hook contracts.
    """
    MAX_LOOP_DEPTH = 1
    MAX_ITERATIONS = 5

    def __init__(self, supervisor: LoopSupervisor) -> None:
        self._verify_orchestrator_caller()
        self.supervisor: LoopSupervisor = supervisor
        self.state_machine: LoopStateMachine = LoopStateMachine()
        self.context: Optional[LoopContext] = None
        self.active_checkpoint: Optional[LoopCheckpoint] = None
        
        # Hooks registry
        self.hooks: Dict[str, Callable[..., None]] = {
            "before_iteration": lambda context, idx: None,
            "after_iteration": lambda context, idx, cp: None,
            "on_failure": lambda context, err: None,
            "on_timeout": lambda context: None,
            "on_approval_required": lambda context, cp: None,
            "on_checkpoint_created": lambda cp: None,
            "on_resume": lambda cp: None,
        }

    def _verify_orchestrator_caller(self) -> None:
        """Inspects stack frames to ensure instantiation and run caller is AgentOrchestrator."""
        stack = inspect.stack()
        caller_valid = False
        for frame in stack:
            self_obj = frame.frame.f_locals.get("self")
            if self_obj and self_obj.__class__.__name__ == "AgentOrchestrator":
                caller_valid = True
                break
        if not caller_valid:
            error_msg = "Invocation forbidden: LoopEngine may only be invoked by AgentOrchestrator"
            logger.critical(f"[SANDBOX BREACH] {error_msg}")
            raise LoopSafetyViolationException(error_msg)

    def initialize(self, context: LoopContext) -> None:
        """Initializes the Loop Engine with an immutable context."""
        self._verify_orchestrator_caller()
        self.context = context
        self.state_machine.transition_to(LoopStateMachine.READY, "Engine initialized with context")

    def run(self) -> LoopResult:
        """
        Executes the loop iteration sequence.
        Note: This is a skeleton method containing no real LLM calls or code generation logic.
        """
        self._verify_orchestrator_caller()
        if self.state_machine.current_state != LoopStateMachine.READY:
            raise LoopStateMachineException("Engine not in READY state")

        start_time = time.perf_counter()
        self.state_machine.transition_to(LoopStateMachine.RUNNING, "Starting loop execution")
        
        try:
            # Main simulation loop
            while self.supervisor.budget.current_iterations < self.MAX_ITERATIONS:
                # 1. Budget validation before step
                self.supervisor.validate_budgets()
                
                idx = self.supervisor.budget.current_iterations
                
                # 2. Before hook
                self.hooks["before_iteration"](self.context, idx)
                
                # Increment counter
                self.supervisor.budget.record_iteration()
                
                # Simulate step timing/tokens
                self.supervisor.budget.add_time(0.01)
                self.supervisor.budget.consume_tokens(50)
                
                # 3. Create iteration checkpoint
                checkpoint_id = f"cp_iter_{idx}"
                iteration_id = f"iter_{idx}"
                deterministic_hash = f"hash_val_{idx}"
                
                cp = LoopCheckpoint(
                    checkpoint_id=checkpoint_id,
                    trace_id=self.context.trace_id,
                    replay_id=self.context.replay_id,
                    deterministic_hash=deterministic_hash,
                    iteration_id=iteration_id,
                    parent_checkpoint_id=self.active_checkpoint.checkpoint_id if self.active_checkpoint else None
                )
                self.active_checkpoint = cp
                self.hooks["on_checkpoint_created"](cp)
                
                # 4. After hook
                self.hooks["after_iteration"](self.context, idx, cp)
                
                # Simulated completion condition check
                if idx >= 1: # Stop after 2 simulated iterations for skeleton test
                    break

            self.state_machine.transition_to(LoopStateMachine.COMPLETED, "Completed successfully")
            
        except Exception as e:
            self.hooks["on_failure"](self.context, e)
            self.state_machine.transition_to(LoopStateMachine.FAILED, f"Failed with exception: {e}")
            raise e

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        return LoopResult(
            trace_id=self.context.trace_id,
            replay_id=self.context.replay_id,
            deterministic_hash=self.active_checkpoint.deterministic_hash if self.active_checkpoint else "none",
            checkpoint_id=self.active_checkpoint.checkpoint_id if self.active_checkpoint else None,
            execution_time_ms=exec_time_ms,
            final_state=self.state_machine.current_state,
            success=True
        )

    def resume_from_checkpoint(self, checkpoint: LoopCheckpoint) -> None:
        """Resumes loop state execution from a checkpoint."""
        self._verify_orchestrator_caller()
        self.active_checkpoint = checkpoint
        self.hooks["on_resume"](checkpoint)
        self.state_machine.transition_to(LoopStateMachine.READY, f"Resumed from checkpoint: {checkpoint.checkpoint_id}")

    def cancel(self, reason: str = "User request") -> None:
        """Safely cancels loop execution."""
        self._verify_orchestrator_caller()
        self.state_machine.transition_to(LoopStateMachine.TERMINATED, f"Cancelled: {reason}")

    def terminate(self, reason: str = "Safety violation") -> None:
        """Forcefully terminates execution on safety/budget breach."""
        self._verify_orchestrator_caller()
        self.state_machine.transition_to(LoopStateMachine.TERMINATED, f"Terminated: {reason}")

    def rollback(self, target_checkpoint: LoopCheckpoint) -> None:
        """Rolls back files and variables to a past checkpoint."""
        self._verify_orchestrator_caller()
        self.active_checkpoint = target_checkpoint
        logger.info(f"[ROLLBACK] State reverted to checkpoint: {target_checkpoint.checkpoint_id}")
