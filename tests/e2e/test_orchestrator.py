import os
import sys
import unittest
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.agents.agent_registry import AgentRegistry
from bbc_aos.agents.agent_orchestrator import AgentOrchestrator
from bbc_aos.agents.planner_agent import PlannerAgent
from bbc_aos.agents.context_agent import ContextAgent
from bbc_aos.agents.coder_agent import CoderAgent
from bbc_aos.agents.tester_agent import TesterAgent
from bbc_aos.agents.verification_agent import VerificationAgent

from bbc_aos.memory.runtime import MemoryManager
from bbc_aos.memory.working.state_manager import StateManager
from bbc_aos.integration import (
    IntegrationAuditLog,
)

# Core Graph Extraction classes to build symbol graph programmatically
from bbc_aos.knowledge.graph.symbol_extractor import SymbolExtractor
from bbc_aos.knowledge.graph.symbol_graph import SymbolGraph


class TestAgentOrchestratorPipeline(unittest.TestCase):

    def setUp(self) -> None:
        # Re-register agents in registry to clean up any testing side-effects
        self.registry = AgentRegistry()
        self.registry.reset()
        self.registry.register(PlannerAgent)
        self.registry.register(ContextAgent)
        self.registry.register(CoderAgent)
        self.registry.register(TesterAgent)
        self.registry.register(VerificationAgent)

        # Setup StateManager singleton clean state
        StateManager._reset_for_testing()
        self.state_manager = StateManager(heal_budget=100, session_heal_budget=100)

        # Setup MemoryManager mock semantic database
        self.memory_manager = MemoryManager()
        
        project_sub = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../archive/legacy_bbc"))
        if os.path.exists(os.path.join(project_sub, "Legacy_BBC")):
            project_sub = os.path.join(project_sub, "Legacy_BBC")
        elif not os.path.exists(project_sub):
            project_sub = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Legacy_BBC"))

        target_python_files = [
            os.path.join(project_sub, "bbc_core", "bbc_scalar.py"),
            os.path.join(project_sub, "bbc_core", "matrix_ops.py"),
        ]
        ext = SymbolExtractor()
        fs_list = [ext.extract_from_file(f) for f in target_python_files]
        fs_dicts = [fs.to_dict() for fs in fs_list if fs is not None]
        
        source_mapping = {}
        for f in target_python_files:
            with open(f, 'r', encoding='utf-8') as src_f:
                source_mapping[f] = src_f.read()
                
        graph = SymbolGraph()
        graph.build_from_symbols(fs_dicts, source_mapping)
        self.symbol_graph = graph.to_dict()
        
        # Register symbol_graph
        graph_record_params = {
            "memory_id": "symbol_graph",
            "trace_id": "tr_init",
            "replay_id": "rp_init",
            "deterministic_hash": "hash_graph",
            "originating_agent": "system",
            "layer": "semantic",
            "data": self.symbol_graph
        }
        self.memory_manager.create_record(graph_record_params, actor_role="human")
        
        # Register bbc_context.json
        context_path = os.path.join(project_sub, ".bbc", "bbc_context.json")
        with open(context_path, 'r', encoding='utf-8') as f:
            self.full_context = json.load(f)
            
        context_record_params = {
            "memory_id": "full_context",
            "trace_id": "tr_init",
            "replay_id": "rp_init",
            "deterministic_hash": "hash_context",
            "originating_agent": "system",
            "layer": "semantic",
            "data": self.full_context
        }
        self.memory_manager.create_record(context_record_params, actor_role="human")

        # Local audit log setup
        self.audit_log = IntegrationAuditLog()
        self.orchestrator = AgentOrchestrator(
            agent_registry=self.registry,
            memory_manager=self.memory_manager,
            audit_log=self.audit_log,
        )

    def tearDown(self) -> None:
        pass

    def _get_context_data(self) -> dict:
        return {
            "memory_manager": self.memory_manager,
            "integration_log": self.audit_log,
        }

    def test_stage_execution_sequence(self) -> None:
        """1. Validate execution completes successfully in sequence (Planner->Context->Coder->Tester->Verify)."""
        context_data = self._get_context_data()
        status = self.orchestrator.execute_goal(
            goal_id="goal_1",
            goal_description="Verify mathematical scalar logic on condition stable estimate",
            trace_id="tr_1",
            replay_id="rp_1",
            context_data=context_data,
        )
        self.assertEqual(status["status"], "COMPLETED")
        self.assertEqual(status["current_stage"], "verify")
        self.assertEqual(status["outputs"]["verify_result"]["verdict"], "APPROVED")

    def test_deterministic_replay(self) -> None:
        """2. Validate 100 runs on identical goal inputs produce identical hashes and logs."""
        context_data = self._get_context_data()
        
        first_status = self.orchestrator.execute_goal(
            goal_id="goal_det",
            goal_description="Sync note promotions to semantic memory",
            trace_id="tr_det",
            replay_id="rp_det",
            context_data=context_data,
        )
        first_hash = first_status["deterministic_hash"]

        for i in range(100):
            # Purge dynamic execution details to prevent key collisions
            key = ("tr_det", "rp_det")
            if key in self.orchestrator.active_executions:
                del self.orchestrator.active_executions[key]
                
            status = self.orchestrator.execute_goal(
                goal_id="goal_det",
                goal_description="Sync note promotions to semantic memory",
                trace_id="tr_det",
                replay_id="rp_det",
                context_data=context_data,
            )
            self.assertEqual(status["deterministic_hash"], first_hash)

    def test_checkpoint_generation(self) -> None:
        """3. Verify stage checkpoints are created at every stage boundary."""
        context_data = self._get_context_data()
        self.orchestrator.execute_goal(
            goal_id="goal_check",
            goal_description="Refactor scalar matrix computations",
            trace_id="tr_check",
            replay_id="rp_check",
            context_data=context_data,
        )
        
        key = ("tr_check", "rp_check")
        exec_info = self.orchestrator.active_executions[key]
        checkpoints = exec_info["checkpoints"]
        
        # 5 checkpoints expected (planner, context, coder, tester, verify)
        self.assertEqual(len(checkpoints), 5)
        self.assertIn("planner", checkpoints)
        self.assertIn("context", checkpoints)
        self.assertIn("coder", checkpoints)
        self.assertIn("tester", checkpoints)
        self.assertIn("verify", checkpoints)

    def test_rollback_correctness(self) -> None:
        """4. Verify execution rollback to previous stage and purge newer checkpoints."""
        context_data = self._get_context_data()
        
        # Run execution
        self.orchestrator.execute_goal(
            goal_id="goal_roll",
            goal_description="Analyse math scalar performance",
            trace_id="tr_roll",
            replay_id="rp_roll",
            context_data=context_data,
        )
        
        # Rollback execution to coder stage
        status = self.orchestrator.rollback_execution("tr_roll", "rp_roll", "coder")
        self.assertEqual(status["current_stage"], "coder")
        self.assertEqual(status["status"], "SUSPENDED")
        
        # Verify checkpoints after coder are purged
        checkpoints = status["checkpoints"]
        self.assertIn("coder", checkpoints)
        self.assertNotIn("tester", checkpoints)
        self.assertNotIn("verify", checkpoints)

    def test_resume_correctness(self) -> None:
        """5. Verify resume execution restarts successfully from checkpoints."""
        context_data = self._get_context_data()
        self.orchestrator.execute_goal(
            goal_id="goal_res",
            goal_description="Verify scalar metrics calculations",
            trace_id="tr_res",
            replay_id="rp_res",
            context_data=context_data,
        )
        
        # Rollback to coder
        self.orchestrator.rollback_execution("tr_res", "rp_res", "coder")
        
        # Resume execution
        status = self.orchestrator.resume_execution("tr_res", "rp_res", context_data)
        self.assertEqual(status["status"], "COMPLETED")
        self.assertEqual(status["current_stage"], "verify")

    def test_rejection_termination(self) -> None:
        """6. Verify that VerificationAgent rejection terminates pipeline execution immediately."""
        context_data = self._get_context_data()

        # Mock CoderAgent that creates an out-of-bounds file edit to force verification rejection
        class HackedCoderAgent(CoderAgent):
            def execute(self, params):
                res = super().execute(params)
                res["modified_files"] = ["bbc_aos/core/unauthorized_file.py"]
                return res

        self.registry._registry["coder_agent"] = HackedCoderAgent

        status = self.orchestrator.execute_goal(
            goal_id="goal_rej",
            goal_description="Perform audit on solver",
            trace_id="tr_rej",
            replay_id="rp_rej",
            context_data=context_data,
        )
        self.assertEqual(status["status"], "SUSPENDED")
        self.assertEqual(status["current_stage"], "verify")
        self.assertEqual(status["outputs"]["verify_result"]["verdict"], "REJECTED")

    def test_retry_limits_transient(self) -> None:
        """7. Validate retry limits catch transient exceptions and fail after 3 retries."""
        context_data = self._get_context_data()

        # Mock CoderAgent that fails twice then succeeds
        class TransientFailingCoderAgent(CoderAgent):
            attempts = 0
            def execute(self, params):
                if TransientFailingCoderAgent.attempts < 2:
                    TransientFailingCoderAgent.attempts += 1
                    raise RuntimeError("Transient DB lock failure")
                return super().execute(params)

        self.registry._registry["coder_agent"] = TransientFailingCoderAgent

        status = self.orchestrator.execute_goal(
            goal_id="goal_transient",
            goal_description="Optimize matrix performance states",
            trace_id="tr_transient",
            replay_id="rp_transient",
            context_data=context_data,
        )
        self.assertEqual(status["status"], "COMPLETED")
        key = ("tr_transient", "rp_transient")
        self.assertEqual(self.orchestrator.active_executions[key]["retry_counts"]["coder"], 2)

        # Mock CoderAgent that fails forever
        class FatalFailingCoderAgent(CoderAgent):
            def execute(self, params):
                raise ValueError("Fatal syntax compile error")

        self.registry._registry["coder_agent"] = FatalFailingCoderAgent

        with self.assertRaises(ValueError):
            self.orchestrator.execute_goal(
                goal_id="goal_fatal",
                goal_description="Optimize matrix performance states",
                trace_id="tr_fatal",
                replay_id="rp_fatal",
                context_data=context_data,
            )

        key_fatal = ("tr_fatal", "rp_fatal")
        self.assertEqual(self.orchestrator.active_executions[key_fatal]["status"], "FAILED")

    def test_audit_generation(self) -> None:
        """8. Verify dispatches generate IntegrationAuditLog events."""
        context_data = self._get_context_data()
        
        self.orchestrator.execute_goal(
            goal_id="goal_audit",
            goal_description="Fix bug in scalar calculations",
            trace_id="tr_audit",
            replay_id="rp_audit",
            context_data=context_data,
        )

        events = self.audit_log.get_events()
        verify_events = [e for e in events if e.event_type == "contract_verified"]
        self.assertEqual(len(verify_events), 1)
        self.assertEqual(verify_events[0].trace_id, "tr_audit")
        self.assertEqual(verify_events[0].replay_id, "rp_audit")

    def test_state_updates(self) -> None:
        """9. Verify that orchestrator execution updates StateManager metrics."""
        context_data = self._get_context_data()

        stats_before = self.state_manager.get_stats()
        files_before = stats_before.get("files_processed", 0)
        recipes_before = stats_before.get("recipes_created", 0)

        self.orchestrator.execute_goal(
            goal_id="goal_state",
            goal_description="Fix bug in scalar calculations",
            trace_id="tr_state",
            replay_id="rp_state",
            context_data=context_data,
        )

        stats_after = self.state_manager.get_stats()
        self.assertGreater(stats_after.get("files_processed", 0), files_before)
        self.assertGreater(stats_after.get("recipes_created", 0), recipes_before)
        self.assertGreater(stats_after.get("data_processed", 0), stats_before.get("data_processed", 0))


if __name__ == "__main__":
    unittest.main()
