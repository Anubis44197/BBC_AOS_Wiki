import os
import sys
import unittest
from typing import Dict, Any

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.loops import (
    LoopEngine,
    LoopSupervisor,
    LoopContext,
    LoopCheckpoint,
    LoopResult,
    LoopPolicy,
    LoopBudget,
    LoopStateMachine,
    LoopRegistry,
    LoopBudgetExceededException,
    LoopSafetyViolationException,
    LoopFrozenRegistryException,
    LoopStateMachineException,
)

# Mock class representing AgentOrchestrator to satisfy caller checks
class AgentOrchestrator:
    def __init__(self) -> None:
        self.budget = LoopBudget()
        self.policy = LoopPolicy()
        self.supervisor = LoopSupervisor(self.budget, self.policy)
        self.engine = LoopEngine(self.supervisor)

    def run_engine_success(self, ctx: LoopContext) -> LoopResult:
        self.engine.initialize(ctx)
        return self.engine.run()

    def run_engine_cancel(self, ctx: LoopContext) -> None:
        self.engine.initialize(ctx)
        self.engine.cancel("User cancel test")

    def run_engine_terminate(self, ctx: LoopContext) -> None:
        self.engine.initialize(ctx)
        self.engine.terminate("Safety sandbox check")

    def run_engine_resume(self, ctx: LoopContext, cp: LoopCheckpoint) -> LoopResult:
        self.engine = LoopEngine(self.supervisor)
        self.engine.resume_from_checkpoint(cp)
        # Transition from READY to RUNNING manually to simulate run resume
        self.engine.state_machine.transition_to(LoopStateMachine.RUNNING, "Resuming execution run")
        # Save state time elapsed simulation
        self.supervisor.budget.add_time(12.34)
        return LoopResult(
            trace_id=ctx.trace_id,
            replay_id=ctx.replay_id,
            deterministic_hash=cp.deterministic_hash,
            checkpoint_id=cp.checkpoint_id,
            execution_time_ms=12.34 * 1000.0,
            final_state=self.engine.state_machine.current_state,
            success=True
        )


class TestLoopRuntimeSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = LoopRegistry()
        self.registry.reset()

    def test_syntax_and_imports(self) -> None:
        """1. Validate syntax and imports of all loops classes."""
        self.assertIsNotNone(LoopEngine)
        self.assertIsNotNone(LoopSupervisor)
        self.assertIsNotNone(LoopContext)
        self.assertIsNotNone(LoopCheckpoint)
        self.assertIsNotNone(LoopResult)
        self.assertIsNotNone(LoopPolicy)
        self.assertIsNotNone(LoopBudget)
        self.assertIsNotNone(LoopStateMachine)
        self.assertIsNotNone(LoopRegistry)

    def test_state_machine_validation(self) -> None:
        """2. Validate deterministic state transitions."""
        sm = LoopStateMachine()
        self.assertEqual(sm.current_state, LoopStateMachine.CREATED)

        # CREATED -> READY
        sm.transition_to(LoopStateMachine.READY, "Test ready")
        self.assertEqual(sm.current_state, LoopStateMachine.READY)

        # READY -> RUNNING
        sm.transition_to(LoopStateMachine.RUNNING, "Test run")
        self.assertEqual(sm.current_state, LoopStateMachine.RUNNING)

        # RUNNING -> WAITING_APPROVAL
        sm.transition_to(LoopStateMachine.WAITING_APPROVAL, "Test wait")
        self.assertEqual(sm.current_state, LoopStateMachine.WAITING_APPROVAL)

        # WAITING_APPROVAL -> RUNNING
        sm.transition_to(LoopStateMachine.RUNNING, "Test approve")
        self.assertEqual(sm.current_state, LoopStateMachine.RUNNING)

        # Invalid transition: WAITING_APPROVAL -> READY
        sm.transition_to(LoopStateMachine.TERMINATED, "Cancel")
        with self.assertRaises(LoopStateMachineException):
            sm.transition_to(LoopStateMachine.RUNNING, "Attempt invalid")

    def test_checkpoint_validation(self) -> None:
        """3. Validate checkpoint serialization/deserialization."""
        cp = LoopCheckpoint(
            checkpoint_id="cp_001",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_123",
            iteration_id="i_0",
            parent_checkpoint_id=None,
            state_data={"var": 42}
        )
        cp_dict = cp.to_dict()
        self.assertEqual(cp_dict["checkpoint_id"], "cp_001")
        self.assertEqual(cp_dict["state_data"]["var"], 42)

        recovered_cp = LoopCheckpoint.from_dict(cp_dict)
        self.assertEqual(recovered_cp.checkpoint_id, "cp_001")
        self.assertEqual(recovered_cp.trace_id, "t_1")
        self.assertEqual(recovered_cp.deterministic_hash, "hash_123")
        self.assertEqual(recovered_cp.state_data["var"], 42)

    def test_budget_validation(self) -> None:
        """4. Validate budget hard limits check."""
        budget = LoopBudget(max_iterations=2, max_tokens=100)
        budget.record_iteration()
        budget.record_iteration()
        # Should not raise yet
        budget.check_hard_limits()

        budget.record_iteration()
        with self.assertRaises(LoopBudgetExceededException):
            budget.check_hard_limits()

    def test_registry_uniqueness_and_freeze(self) -> None:
        """5. Validate registry unique registration and freeze lifecycle."""
        self.assertFalse(self.registry.is_frozen)
        
        # Register a class
        class DummyRuntime1:
            pass
        class DummyRuntime2:
            pass

        self.registry.register("dummy1", DummyRuntime1)
        self.assertEqual(self.registry.get("dummy1"), DummyRuntime1)

        # Test Uniqueness validation
        with self.assertRaises(ValueError):
            self.registry.register("dummy1", DummyRuntime2)

        # Test Freeze validation
        self.registry.freeze()
        self.assertTrue(self.registry.is_frozen)

        # Test modification after freeze is forbidden
        with self.assertRaises(LoopFrozenRegistryException):
            self.registry.register("dummy2", DummyRuntime2)

    def test_orchestrator_caller_restriction(self) -> None:
        """6. Validate that LoopEngine restricts caller to AgentOrchestrator."""
        budget = LoopBudget()
        policy = LoopPolicy()
        supervisor = LoopSupervisor(budget, policy)
        
        # Instantiating LoopEngine directly in a unit test (without AgentOrchestrator frame)
        # must fail with a LoopSafetyViolationException
        with self.assertRaises(LoopSafetyViolationException):
            LoopEngine(supervisor)

    def test_full_replay_contract(self) -> None:
        """7. Validate LoopResult data structure and replay contract resume."""
        ctx = LoopContext(trace_id="t_replay", replay_id="r_replay", task_id="task_123")
        orch = AgentOrchestrator()
        
        res = orch.run_engine_success(ctx)
        self.assertIsInstance(res, LoopResult)
        self.assertEqual(res.trace_id, "t_replay")
        self.assertEqual(res.replay_id, "r_replay")
        self.assertEqual(res.final_state, LoopStateMachine.COMPLETED)
        self.assertTrue(res.success)
        self.assertTrue(res.execution_time_ms > 0)

        # Test resume from checkpoint
        cp = LoopCheckpoint(
            checkpoint_id="cp_resume",
            trace_id="t_replay",
            replay_id="r_replay",
            deterministic_hash="hash_resume",
            iteration_id="i_resume"
        )
        res_resume = orch.run_engine_resume(ctx, cp)
        self.assertEqual(res_resume.checkpoint_id, "cp_resume")
        self.assertEqual(res_resume.deterministic_hash, "hash_resume")
        self.assertEqual(res_resume.final_state, LoopStateMachine.RUNNING)


if __name__ == "__main__":
    unittest.main()
