"""Phase 11D Validation Suite - TesterAgent Production Implementation

Validates:
1. Syntax and schema validation (input/output contracts)
2. Deterministic replay (100 runs, zero variance)
3. Task count limits (validation_tasks <= 50)
4. Dependency depth limits (depth <= 5)
5. Risk classification mapping (LOW, MEDIUM, HIGH, CRITICAL)
6. Coverage targets mapping (syntax, unit, integration, regression, replay)
7. Audit event generation (IntegrationAuditLog compliance)
8. Stable task ordering (by priority and task_id)
"""

import os
import sys
import unittest
import hashlib
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.agents.tester_agent import TesterAgent, ValidationTask, ValidationPlan, _DeterministicValidationPlanner
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

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
    
    # Calculate deterministic hash
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


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestTesterAgentProduction(unittest.TestCase):

    def setUp(self) -> None:
        self.agent = TesterAgent()
        self.agent.initialize()
        self.audit_log = IntegrationAuditLog()

        # Integration subsystem mock setup
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
        # Valid params must pass
        params = _make_valid_params(audit_log=self.audit_log)
        self.assertTrue(self.agent.validate_input(params), "Valid params should pass input validation.")

        # Missing task block must fail
        bad = _make_valid_params(audit_log=self.audit_log)
        del bad["context"]["task"]
        self.assertFalse(self.agent.validate_input(bad))

        # Missing task_id must fail
        bad_task = _make_valid_params(audit_log=self.audit_log)
        del bad_task["context"]["task"]["task_id"]
        self.assertFalse(self.agent.validate_input(bad_task))

        # Missing code_diff block must fail
        bad_diff = _make_valid_params(audit_log=self.audit_log)
        del bad_diff["context"]["code_diff"]
        self.assertFalse(self.agent.validate_input(bad_diff))

        # Missing metadata block must fail
        bad_meta = _make_valid_params(audit_log=self.audit_log)
        del bad_meta["metadata"]
        self.assertFalse(self.agent.validate_input(bad_meta))

        # Empty params must fail
        self.assertFalse(self.agent.validate_input({}))
        self.assertFalse(self.agent.validate_input(None))

        print("[PASS] test_input_validation")

    def test_output_validation(self) -> None:
        """2. Execute and validate output schema compliance."""
        params = _make_valid_params(
            task_id="task_out",
            description="Verify core bbc_scalar math module changes",
            trace_id="tr_out",
            replay_id="rp_out",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result), "Output should pass validation.")

        # Check required fields present
        for field in ("trace_id", "replay_id", "deterministic_hash",
                      "validation_tasks", "risk_level", "coverage_targets"):
            self.assertIn(field, result, f"Missing field: {field}")

        # Check propagated metadata
        self.assertEqual(result["trace_id"], "tr_out")
        self.assertEqual(result["replay_id"], "rp_out")

        # Check SHA-256 hash length
        self.assertEqual(len(result["deterministic_hash"]), 64)

        # Check coverage targets keys
        targets = result["coverage_targets"]
        for key in ("syntax", "unit", "integration", "regression", "replay"):
            self.assertIn(key, targets, f"Missing coverage target key: {key}")

        print("[PASS] test_output_validation")

    def test_deterministic_replay(self) -> None:
        """3. Validate 100 runs on identical inputs produce identical validation plans."""
        params = _make_valid_params(
            task_id="task_det",
            description="Fix memory leak in state_manager",
            trace_id="tr_det",
            replay_id="rp_det",
            audit_log=self.audit_log,
        )

        first_result = self.agent.execute(params)
        first_hash = first_result["deterministic_hash"]
        first_tasks = first_result["validation_tasks"]
        first_risk = first_result["risk_level"]
        first_targets = first_result["coverage_targets"]

        for i in range(100):
            result = self.agent.execute(params)
            self.assertEqual(
                result["deterministic_hash"], first_hash,
                f"Hash mismatch at iteration {i + 1}"
            )
            self.assertEqual(
                result["validation_tasks"], first_tasks,
                f"validation_tasks mismatch at iteration {i + 1}"
            )
            self.assertEqual(
                result["risk_level"], first_risk,
                f"risk_level mismatch at iteration {i + 1}"
            )
            self.assertEqual(
                result["coverage_targets"], first_targets,
                f"coverage_targets mismatch at iteration {i + 1}"
            )

        print("[PASS] test_deterministic_replay (100 iterations, zero variance)")

    def test_task_limits(self) -> None:
        """4. Validate generated tasks limit (<= 50) and depth limit (<= 5)."""
        # Create a diff with 20 files. With 5 test types per file, this could lead to 100 tasks.
        # It must be capped at 50 tasks.
        code_diff_large = _make_code_diff(modified_count=20, added_count=5)
        params = _make_valid_params(
            task_id="task_large",
            description="Critical security refactor of network core",
            code_diff=code_diff_large,
            trace_id="tr_large",
            replay_id="rp_large",
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))

        tasks = result["validation_tasks"]
        self.assertLessEqual(len(tasks), 50, f"Task count ({len(tasks)}) exceeds limit of 50.")

        # Verify dependency depth of each task is <= 5
        for t in tasks:
            self.assertLessEqual(len(t["dependencies"]), 5, f"Task {t['task_id']} dependency count exceeds 5.")

        print("[PASS] test_task_limits")

    def test_risk_classification(self) -> None:
        """5. Validate risk classification mapping (LOW, MEDIUM, HIGH, CRITICAL)."""
        planner = _DeterministicValidationPlanner()

        test_cases = [
            ("Verify security layer authorization", ["f1.py"], [], [], "CRITICAL"), # security keyword
            ("Implement critical checkpoint recovery algorithm", ["f1.py"], [], [], "CRITICAL"), # critical/recovery keyword
            ("Optimize matrix inverse performance", ["f1.py"], [], [], "HIGH"), # performance keyword
            ("Refactor quantizer index structures", ["f1.py"], [], [], "HIGH"), # refactor keyword
            ("Fix crash in hmpu governor constraints check", ["f1.py"], [], [], "MEDIUM"), # fix keyword
            ("Bug in context compilation unit", ["f1.py"], [], [], "MEDIUM"), # bug keyword
            ("Minor layout alignment tweak", ["f1.py"], [], [], "LOW"), # default
        ]

        for desc, mod, add, rem, expected_risk in test_cases:
            risk = planner._classify_risk_level(desc, mod, add, rem)
            self.assertEqual(
                risk, expected_risk,
                f"Description '{desc}' should classify as '{expected_risk}' but got '{risk}'"
            )

        # File deletion forces CRITICAL risk
        risk_del = planner._classify_risk_level("Trivial delete", [], [], ["old_module.py"])
        self.assertEqual(risk_del, "CRITICAL")

        # Large modified files count (>15) forces CRITICAL risk
        risk_large = planner._classify_risk_level("Trivial change", [f"m_{i}.py" for i in range(16)], [], [])
        self.assertEqual(risk_large, "CRITICAL")

        # Large files count (>8) forces HIGH risk
        risk_high = planner._classify_risk_level("Trivial change", [f"m_{i}.py" for i in range(9)], [], [])
        self.assertEqual(risk_high, "HIGH")

        print("[PASS] test_risk_classification")

    def test_coverage_targets(self) -> None:
        """6. Validate generated coverage targets mapping."""
        planner = _DeterministicValidationPlanner()

        # Bugfix description triggers regression testing
        targets = planner._generate_coverage_targets("Fix memory leak in state_manager", "MEDIUM", ["f1.py"], [], [])
        self.assertTrue(targets["regression"])
        self.assertTrue(targets["syntax"])
        self.assertTrue(targets["unit"])
        self.assertTrue(targets["replay"])

        # High risk triggers integration testing
        targets_high = planner._generate_coverage_targets("Performance optimization", "HIGH", ["f1.py"], [], [])
        self.assertTrue(targets_high["integration"])
        self.assertTrue(targets_high["regression"])

        print("[PASS] test_coverage_targets")

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

        # Verify orchestrator dispatching
        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result,
        )
        dispatch_result = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(dispatch_result.success)

        print("[PASS] test_audit_event_generation")

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

        # Check priorities are in ascending order (sorted by priority first)
        priorities = [t["priority"] for t in tasks]
        self.assertEqual(priorities, sorted(priorities), "Tasks must be sorted by priority in ascending order.")

        # Check for same priority, task_id is sorted alphabetically
        for priority in range(1, 6):
            subset_ids = [t["task_id"] for t in tasks if t["priority"] == priority]
            self.assertEqual(subset_ids, sorted(subset_ids), f"Tasks with priority {priority} must be sorted by task_id.")

        print("[PASS] test_task_stable_ordering")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 11D Validation Suite - TesterAgent")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTesterAgentProduction)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n[ALL TESTS PASSED] TesterAgent Phase 11D validation complete.")
    else:
        print(f"\n[FAILED] {len(result.failures)} failures, {len(result.errors)} errors.")
        sys.exit(1)
