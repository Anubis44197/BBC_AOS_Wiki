import os
import sys
import unittest

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.agents.planner_agent import PlannerAgent
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)

class TestPlannerAgentProduction(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = PlannerAgent()
        self.agent.initialize()
        
        # Integration broker mock setup for audit/validation gateway checks
        self.registry = SubsystemRegistry()
        self.registry.reset()
        
        class MockSubsystem:
            def get_health_status(self):
                return {"subsystem": "agent", "status": "OK", "is_frozen": True}
                
        self.registry.register_subsystem("agent", MockSubsystem())
        self.registry.freeze()
        self.audit_log = IntegrationAuditLog()
        self.orchestrator = IntegrationOrchestrator(self.registry, self.audit_log)

    def tearDown(self) -> None:
        self.agent.finalize()

    def test_syntax_and_validation(self) -> None:
        """1. Validate syntax, inputs, and outputs of the PlannerAgent."""
        # Valid input parameters
        params = {
            "context": {
                "goal": "Migrate bbc_scalar math operations",
                "goal_id": "goal_migrate_scalar"
            },
            "metadata": {
                "trace_id": "tr_1",
                "replay_id": "rp_1"
            }
        }
        
        self.assertTrue(self.agent.validate_input(params))
        
        # Invalid input parameters (missing goal_id)
        invalid_params = {
            "context": {
                "goal": "Migrate bbc_scalar math operations"
            },
            "metadata": {
                "trace_id": "tr_1",
                "replay_id": "rp_1"
            }
        }
        self.assertFalse(self.agent.validate_input(invalid_params))

        # Test execution
        plan = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(plan))

    def test_deterministic_replay(self) -> None:
        """2. Validate 100 runs on identical goal inputs produce identical tasks & hashes."""
        params = {
            "context": {
                "goal": "Sync note promotions to semantic memory",
                "goal_id": "goal_sync_notes"
            },
            "metadata": {
                "trace_id": "tr_det",
                "replay_id": "rp_det"
            }
        }
        
        first_plan = self.agent.execute(params)
        first_hash = first_plan["deterministic_hash"]
        
        for _ in range(100):
            next_plan = self.agent.execute(params)
            self.assertEqual(next_plan["deterministic_hash"], first_hash)
            self.assertEqual(next_plan["tasks"], first_plan["tasks"])

    def test_task_limits_and_depth(self) -> None:
        """3. Validate task counts (<= 20) and dependency depths (<= 5)."""
        goals = [
            "Decompose complex recovery systems step-by-step",
            "Generate short goal",
            "A very long goal that might generate more deterministic tasks based on sha256 calculations",
            "Core Shannon Chaos convergence loops calibrations"
        ]
        
        for idx, g in enumerate(goals):
            params = {
                "context": {
                    "goal": g,
                    "goal_id": f"goal_{idx}"
                },
                "metadata": {
                    "trace_id": f"tr_{idx}",
                    "replay_id": f"rp_{idx}"
                }
            }
            plan = self.agent.execute(params)
            self.assertTrue(self.agent.validate_output(plan))
            
            tasks = plan["tasks"]
            self.assertTrue(len(tasks) <= 20)
            
            # Recheck depths programmatically
            depths = {}
            for task in tasks:
                task_id = task["task_id"]
                deps = task["dependencies"]
                if not deps:
                    depths[task_id] = 1
                else:
                    depths[task_id] = max(depths[d] for d in deps) + 1
                self.assertTrue(depths[task_id] <= 5, f"Task {task_id} depth is {depths[task_id]}")

    def test_audit_generation(self) -> None:
        """4. Verify dispatches generate IntegrationAuditLog events."""
        params = {
            "context": {
                "goal": "Verify startup sequences",
                "goal_id": "goal_startup"
            },
            "metadata": {
                "trace_id": "tr_audit",
                "replay_id": "rp_audit"
            }
        }
        plan = self.agent.execute(params)
        
        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=plan["deterministic_hash"],
            payload=plan
        )
        
        # Routing via orchestrator dispatches and logs event
        res = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(res.success)
        
        events = self.audit_log.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trace_id, "tr_audit")
        self.assertEqual(events[0].replay_id, "rp_audit")
        self.assertEqual(events[0].deterministic_hash, plan["deterministic_hash"])


if __name__ == "__main__":
    unittest.main()
