import os
import sys
import unittest
import hashlib
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.agents.tester_agent import TesterAgent, _DeterministicValidationPlanner
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)


def _make_code_diff(
    modified_count: int = 2,
    added_count: int = 1,
    removed_count: int = 0,
    trace_id: str = "tr_diff",
    replay_id: str = "rp_diff",
) -> dict:
    """Builds a mock CodeDiff dictionary matching CoderAgent's output contract."""
    modified_files = [f"bbc_aos/core/module_mod_{i}.py" for i in range(modified_count)]
    added_files = [f"bbc_aos/core/module_add_{i}.py" for i in range(added_count)]
    removed_files = [f"bbc_aos/core/module_rem_{i}.py" for i in range(removed_count)]

    # Mock diff hunks
    hunks = []
    for f in modified_files:
        hunks.append(f"--- a/{f}\n+++ b/{f}\n@@ -1,2 +1,3 @@\n-# orig\n+# mod")
    for f in added_files:
        hunks.append(f"--- /dev/null\n+++ b/{f}\n@@ -0,0 +1,2 @@\n+# add")
    for f in removed_files:
        hunks.append(f"--- a/{f}\n+++ /dev/null")

    patch = "\n".join(hunks)
    
    payload = {
        "modified_files": sorted(modified_files),
        "added_files": sorted(added_files),
        "removed_files": sorted(removed_files),
        "patch": patch,
    }
    payload_str = json.dumps(payload, sort_keys=True)
    deterministic_hash = hashlib.sha256(f"task_test_{trace_id}_{payload_str}".encode("utf-8")).hexdigest()

    return {
        "modified_files": sorted(modified_files),
        "added_files": sorted(added_files),
        "removed_files": sorted(removed_files),
        "patch": patch,
        "trace_id": trace_id,
        "replay_id": replay_id,
        "deterministic_hash": deterministic_hash,
    }


def _make_valid_params(
    task_id: str = "task_1",
    description: str = "Verify syntax and unit tests",
    dependencies: list = None,
    code_diff: dict = None,
    trace_id: str = "tr_test",
    replay_id: str = "rp_test",
    audit_log=None,
) -> dict:
    """Creates a valid parameter payload matching the TesterAgent input schema."""
    if dependencies is None:
        dependencies = []
    if code_diff is None:
        code_diff = _make_code_diff(trace_id=trace_id, replay_id=replay_id)

    return {
        "context": {
            "task": {
                "task_id": task_id,
                "description": description,
                "priority": 2,
                "dependencies": dependencies,
            },
            "code_diff": code_diff,
            "integration_log": audit_log or IntegrationAuditLog(),
        },
        "metadata": {
            "trace_id": trace_id,
            "replay_id": replay_id,
        },
    }


class TestTesterAgentProduction(unittest.TestCase):

    def setUp(self) -> None:
        self.agent = TesterAgent()
        self.agent.initialize()
        self.audit_log = IntegrationAuditLog()

        # Integration subsystem mock
        self.registry = SubsystemRegistry()
        self.registry.reset()

        class MockSubsystem:
            def get_health_status(self):
                return {"subsystem": "agent", "status": "OK", "is_frozen": True}

        self.registry.register_subsystem("agent", MockSubsystem())
        self.registry.register_subsystem("memory", MockSubsystem())
        self.registry.freeze()
        self.orchestrator = IntegrationOrchestrator(self.registry, self.audit_log)

    def tearDown(self) -> None:
        self.agent.finalize()

    def test_input_validation(self) -> None:
        """1. Validate input schema — required fields enforcement."""
        params = _make_valid_params(audit_log=self.audit_log)
        self.assertTrue(self.agent.validate_input(params), "Valid params should pass.")

        bad = _make_valid_params(audit_log=self.audit_log)
        del bad["context"]["task"]["task_id"]
        self.assertFalse(self.agent.validate_input(bad))

        bad2 = _make_valid_params(audit_log=self.audit_log)
        del bad2["context"]["task"]["description"]
        self.assertFalse(self.agent.validate_input(bad2))

        bad3 = _make_valid_params(audit_log=self.audit_log)
        del bad3["context"]["code_diff"]
        self.assertFalse(self.agent.validate_input(bad3))

        bad4 = _make_valid_params(audit_log=self.audit_log)
        del bad4["metadata"]["trace_id"]
        self.assertFalse(self.agent.validate_input(bad4))

        self.assertFalse(self.agent.validate_input({}))
        self.assertFalse(self.agent.validate_input(None))

    def test_output_validation(self) -> None:
        """2. Execute and validate output schema compliance."""
        params = _make_valid_params(
            task_id="task_out",
            description="Verify changes inside state manager",
            trace_id="tr_out",
            replay_id="rp_out",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result), "Output should pass validation.")

        for field in ("validation_tasks", "risk_level", "coverage_targets",
                      "trace_id", "replay_id", "deterministic_hash"):
            self.assertIn(field, result, f"Missing field: {field}")

        self.assertEqual(result["trace_id"], "tr_out")
        self.assertEqual(result["replay_id"], "rp_out")
        self.assertEqual(len(result["deterministic_hash"]), 64)

    def test_deterministic_replay(self) -> None:
        """3. Validate 100 runs on identical inputs produce identical validation plans."""
        params = _make_valid_params(
            task_id="task_det",
            description="Refactor scalar matrix inverse solver",
            trace_id="tr_det",
            replay_id="rp_det",
            audit_log=self.audit_log,
        )

        first_result = self.agent.execute(params)
        first_hash = first_result["deterministic_hash"]
        first_tasks = first_result["validation_tasks"]

        for i in range(100):
            result = self.agent.execute(params)
            self.assertEqual(result["deterministic_hash"], first_hash)
            self.assertEqual(result["validation_tasks"], first_tasks)

    def test_task_limits_and_depth(self) -> None:
        """4. Validate validation_tasks <= 50, depths <= 5."""
        code_diff = _make_code_diff(modified_count=60, added_count=0)
        params = _make_valid_params(
            task_id="task_limits",
            description="Stress test planner with high modified file counts",
            code_diff=code_diff,
            trace_id="tr_limits",
            replay_id="rp_limits",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))

        tasks = result["validation_tasks"]
        self.assertLessEqual(len(tasks), _DeterministicValidationPlanner.MAX_VALIDATION_TASKS)

        depths = {}
        for task in tasks:
            task_id = task["task_id"]
            deps = task["dependencies"]
            if not deps:
                depths[task_id] = 1
            else:
                depths[task_id] = max(depths[d] for d in deps) + 1
            self.assertLessEqual(depths[task_id], 5)

    def test_risk_classification(self) -> None:
        """5. Validate risk classification mapping."""
        planner = _DeterministicValidationPlanner()

        # Bugfix description classification
        self.assertEqual(planner._classify_risk_level("Fix the memory leak in state_manager", ["f1.py"], [], []), "MEDIUM")
        # Critical keywords classification
        self.assertEqual(planner._classify_risk_level("Critical security refactor of context packer", ["f1.py"], [], []), "CRITICAL")
        # Empty file modifications classification
        self.assertEqual(planner._classify_risk_level("Analyse code structure for compliance", [], [], []), "LOW")
        # High file modifications count classification
        self.assertEqual(planner._classify_risk_level("Refactor core engine components", ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py", "f6.py"], [], []), "HIGH")

    def test_coverage_targets(self) -> None:
        """6. Validate generated coverage targets mapping."""
        planner = _DeterministicValidationPlanner()

        targets = planner._generate_coverage_targets("Fix memory leak in state_manager", "MEDIUM", ["f1.py"], [], [])
        self.assertTrue(targets["regression"])
        self.assertTrue(targets["syntax"])
        self.assertTrue(targets["unit"])
        self.assertTrue(targets["replay"])

        targets_high = planner._generate_coverage_targets("Performance optimization", "HIGH", ["f1.py"], [], [])
        self.assertTrue(targets_high["integration"])
        self.assertTrue(targets_high["regression"])

    def test_audit_event_generation(self) -> None:
        """7. Verify IntegrationAuditLog events are generated on execute()."""
        local_audit_log = IntegrationAuditLog()
        params = _make_valid_params(
            task_id="task_audit",
            description="Critical security refactor of context packer",
            trace_id="tr_audit",
            replay_id="rp_audit",
            audit_log=local_audit_log,
        )

        result = self.agent.execute(params)
        events = local_audit_log.get_events()

        self.assertGreater(len(events), 0, "At least one audit event should be emitted.")
        event = events[-1]
        self.assertEqual(event.event_type, "validation_plan_generated")
        self.assertEqual(event.trace_id, "tr_audit")
        self.assertEqual(event.replay_id, "rp_audit")
        self.assertEqual(event.deterministic_hash, result["deterministic_hash"])
        self.assertEqual(event.details["risk_level"], "CRITICAL")
        self.assertEqual(event.details["task_id"], "task_audit")

        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result,
        )
        dispatch_result = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(dispatch_result.success)

    def test_task_stable_ordering(self) -> None:
        """8. Verify stable task ordering sorted by priority and task_id."""
        code_diff = _make_code_diff(modified_count=5, added_count=0)
        params = _make_valid_params(
            task_id="task_order",
            description="Refactor scalar matrix inverse solver",
            code_diff=code_diff,
            trace_id="tr_order",
            replay_id="rp_order",
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        tasks = result["validation_tasks"]

        priorities = [t["priority"] for t in tasks]
        self.assertEqual(priorities, sorted(priorities), "Tasks must be sorted by priority in ascending order.")

        for priority in range(1, 6):
            subset_ids = [t["task_id"] for t in tasks if t["priority"] == priority]
            self.assertEqual(subset_ids, sorted(subset_ids), f"Tasks with priority {priority} must be sorted by task_id.")


if __name__ == "__main__":
    unittest.main()
