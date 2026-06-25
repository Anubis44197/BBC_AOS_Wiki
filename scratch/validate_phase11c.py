"""
Phase 11C Validation Suite - CoderAgent Production Implementation
Validates:
1. Syntax and schema validation (input/output contracts)
2. Deterministic replay (100 runs, zero variance)
3. Blast radius limits (selected_files <= 50, total diff files <= 20)
4. Audit event generation (IntegrationAuditLog compliance)
5. Immutability of CodeDiff structure
"""

import os
import sys
import unittest
import hashlib
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.agents.coder_agent import CoderAgent, CodeDiff, _DeterministicDiffEngine
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _make_packed_context(file_count: int = 3) -> dict:
    """Build a minimal mock packed_context as CoderAgent would receive from ContextAgent."""
    files = [f"bbc_aos/core/module_{i}.py" for i in range(file_count)]
    return {
        "code_structure": [{"path": f, "_relevance_score": 0.9} for f in files],
        "_path_aliases": {"bbc_aos/core": "@core"},
        "_shared_imports": ["import logging", "from typing import Any"],
        "metrics": {
            "packing_savings_pct": 12.5,
            "packing_mode": "safe",
        },
    }


def _make_selected_files(count: int = 3) -> list:
    return [f"bbc_aos/core/module_{i}.py" for i in range(count)]


def _make_valid_params(
    task_id: str = "task_1",
    description: str = "Fix bug in matrix inverse solver",
    dependencies: list = None,
    file_count: int = 3,
    trace_id: str = "tr_test",
    replay_id: str = "rp_test",
    audit_log=None,
) -> dict:
    if dependencies is None:
        dependencies = []
    return {
        "context": {
            "task": {
                "task_id": task_id,
                "description": description,
                "priority": 1,
                "dependencies": dependencies,
            },
            "packed_context": _make_packed_context(file_count),
            "selected_files": _make_selected_files(file_count),
            "integration_log": audit_log or IntegrationAuditLog(),
        },
        "metadata": {
            "trace_id": trace_id,
            "replay_id": replay_id,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCoderAgentProduction(unittest.TestCase):

    def setUp(self) -> None:
        self.agent = CoderAgent()
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

    # -----------------------------------------------------------------------
    # Test 1: Input schema validation
    # -----------------------------------------------------------------------
    def test_input_validation(self) -> None:
        """1. Validate input schema — required fields enforcement."""
        # Valid params must pass
        params = _make_valid_params(audit_log=self.audit_log)
        self.assertTrue(self.agent.validate_input(params), "Valid params should pass.")

        # Missing task_id must fail
        bad = _make_valid_params(audit_log=self.audit_log)
        del bad["context"]["task"]["task_id"]
        self.assertFalse(self.agent.validate_input(bad))

        # Missing description must fail
        bad2 = _make_valid_params(audit_log=self.audit_log)
        del bad2["context"]["task"]["description"]
        self.assertFalse(self.agent.validate_input(bad2))

        # Missing packed_context must fail
        bad3 = _make_valid_params(audit_log=self.audit_log)
        del bad3["context"]["packed_context"]
        self.assertFalse(self.agent.validate_input(bad3))

        # Missing selected_files must fail
        bad4 = _make_valid_params(audit_log=self.audit_log)
        del bad4["context"]["selected_files"]
        self.assertFalse(self.agent.validate_input(bad4))

        # Missing trace_id must fail
        bad5 = _make_valid_params(audit_log=self.audit_log)
        del bad5["metadata"]["trace_id"]
        self.assertFalse(self.agent.validate_input(bad5))

        # Missing replay_id must fail
        bad6 = _make_valid_params(audit_log=self.audit_log)
        del bad6["metadata"]["replay_id"]
        self.assertFalse(self.agent.validate_input(bad6))

        # Empty params must fail
        self.assertFalse(self.agent.validate_input({}))
        self.assertFalse(self.agent.validate_input(None))

        print("[PASS] test_input_validation")

    # -----------------------------------------------------------------------
    # Test 2: Output schema validation
    # -----------------------------------------------------------------------
    def test_output_validation(self) -> None:
        """2. Execute and validate output schema compliance."""
        params = _make_valid_params(
            task_id="task_out",
            description="Fix bug in bbc_scalar module",
            trace_id="tr_out",
            replay_id="rp_out",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result), "Output should pass validation.")

        # Check required fields present
        for field in ("modified_files", "added_files", "removed_files", "patch",
                      "trace_id", "replay_id", "deterministic_hash"):
            self.assertIn(field, result, f"Missing field: {field}")

        # Check propagated metadata
        self.assertEqual(result["trace_id"], "tr_out")
        self.assertEqual(result["replay_id"], "rp_out")

        # Check SHA-256 hash is 64 hex chars
        self.assertEqual(len(result["deterministic_hash"]), 64)

        print("[PASS] test_output_validation")

    # -----------------------------------------------------------------------
    # Test 3: Deterministic replay (100 iterations, zero variance)
    # -----------------------------------------------------------------------
    def test_deterministic_replay(self) -> None:
        """3. Validate 100 runs on identical inputs produce identical diffs."""
        params = _make_valid_params(
            task_id="task_det",
            description="Refactor context optimization pipeline",
            file_count=5,
            trace_id="tr_det",
            replay_id="rp_det",
            audit_log=self.audit_log,
        )

        first_result = self.agent.execute(params)
        first_hash = first_result["deterministic_hash"]
        first_modified = first_result["modified_files"]
        first_patch = first_result["patch"]

        for i in range(100):
            result = self.agent.execute(params)
            self.assertEqual(
                result["deterministic_hash"], first_hash,
                f"Hash mismatch at iteration {i + 1}"
            )
            self.assertEqual(
                result["modified_files"], first_modified,
                f"modified_files mismatch at iteration {i + 1}"
            )
            self.assertEqual(
                result["patch"], first_patch,
                f"patch mismatch at iteration {i + 1}"
            )

        print("[PASS] test_deterministic_replay (100 iterations, zero variance)")

    # -----------------------------------------------------------------------
    # Test 4: Blast radius limits
    # -----------------------------------------------------------------------
    def test_blast_radius_limits(self) -> None:
        """4. Validate selected_files <= 50, diff files <= 20."""
        # Test with exactly 50 files — should work fine
        params_50 = _make_valid_params(
            task_id="task_50",
            description="Implement feature in core modules",
            file_count=50,
            trace_id="tr_50",
            replay_id="rp_50",
            audit_log=self.audit_log,
        )
        result_50 = self.agent.execute(params_50)
        self.assertTrue(self.agent.validate_output(result_50))
        total_diff = (
            len(result_50["modified_files"])
            + len(result_50["added_files"])
            + len(result_50["removed_files"])
        )
        self.assertLessEqual(total_diff, _DeterministicDiffEngine.MAX_DIFF_FILES)

        # Test with 60 files — agent must truncate to 50 internally
        params_60 = _make_valid_params(
            task_id="task_60",
            description="Implement feature in core modules",
            file_count=60,
            trace_id="tr_60",
            replay_id="rp_60",
            audit_log=self.audit_log,
        )
        result_60 = self.agent.execute(params_60)
        self.assertTrue(self.agent.validate_output(result_60))
        total_60 = (
            len(result_60["modified_files"])
            + len(result_60["added_files"])
            + len(result_60["removed_files"])
        )
        self.assertLessEqual(total_60, _DeterministicDiffEngine.MAX_DIFF_FILES)

        print("[PASS] test_blast_radius_limits")

    # -----------------------------------------------------------------------
    # Test 5: Audit event generation
    # -----------------------------------------------------------------------
    def test_audit_event_generation(self) -> None:
        """5. Verify IntegrationAuditLog events are emitted during execute()."""
        local_audit_log = IntegrationAuditLog()
        params = _make_valid_params(
            task_id="task_audit",
            description="Fix bug in matrix pseudo-inverse computation",
            trace_id="tr_audit",
            replay_id="rp_audit",
            audit_log=local_audit_log,
        )
        result = self.agent.execute(params)

        events = local_audit_log.get_events()
        self.assertGreater(len(events), 0, "At least one audit event should have been emitted.")

        # Check event fields
        event = events[-1]
        self.assertEqual(event.event_type, "code_diff_generated")
        self.assertEqual(event.trace_id, "tr_audit")
        self.assertEqual(event.replay_id, "rp_audit")
        self.assertEqual(event.deterministic_hash, result["deterministic_hash"])
        self.assertIn("task_id", event.details)
        self.assertIn("operation", event.details)

        # Verify orchestrator can dispatch audit-verified result
        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result,
        )
        dispatch_result = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(dispatch_result.success)

        print("[PASS] test_audit_event_generation")

    # -----------------------------------------------------------------------
    # Test 6: CodeDiff immutability
    # -----------------------------------------------------------------------
    def test_code_diff_immutability(self) -> None:
        """6. Validate that CodeDiff instances are fully immutable."""
        diff = CodeDiff(
            modified_files=["file_a.py"],
            added_files=[],
            removed_files=[],
            patch="--- a/file_a.py\n+++ b/file_a.py",
            trace_id="tr_imm",
            replay_id="rp_imm",
            deterministic_hash="a" * 64,
        )

        # Attempting to set any attribute must raise AttributeError
        with self.assertRaises(AttributeError):
            diff.modified_files = ["file_b.py"]

        with self.assertRaises(AttributeError):
            diff.patch = "# overwrite"

        with self.assertRaises(AttributeError):
            diff.deterministic_hash = "z" * 64

        # to_dict() must return correct values
        d = diff.to_dict()
        self.assertEqual(d["modified_files"], ["file_a.py"])
        self.assertEqual(d["trace_id"], "tr_imm")

        print("[PASS] test_code_diff_immutability")

    # -----------------------------------------------------------------------
    # Test 7: Operation classification
    # -----------------------------------------------------------------------
    def test_operation_classification(self) -> None:
        """7. Validate diff engine classifies operations correctly from descriptions."""
        engine = _DeterministicDiffEngine()

        test_cases = [
            ("Fix the memory leak in state_manager", "bugfix"),
            ("Refactor context optimization pipeline", "refactor"),
            ("Implement new feature for token tracking", "feature"),
            ("Review and audit the orchestrator module", "review"),
            ("Add missing validation for scalar types", "feature"),
            ("Analyse code structure for compliance", "review"),
            ("Patch null pointer dereference in resolver", "bugfix"),
        ]

        for description, expected_op in test_cases:
            actual = engine._classify_operation(description)
            self.assertEqual(
                actual, expected_op,
                f"Description '{description}' should classify as '{expected_op}' but got '{actual}'"
            )

        print("[PASS] test_operation_classification")

    # -----------------------------------------------------------------------
    # Test 8: Review task produces no-op diff
    # -----------------------------------------------------------------------
    def test_review_task_noop(self) -> None:
        """8. Validate that review tasks produce no file modifications."""
        params = _make_valid_params(
            task_id="task_review",
            description="Review and audit the orchestrator module implementation",
            file_count=5,
            trace_id="tr_review",
            replay_id="rp_review",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))

        # Review produces no modifications
        self.assertEqual(result["modified_files"], [])
        self.assertEqual(result["added_files"], [])
        self.assertEqual(result["removed_files"], [])

        # Patch should contain inspection annotations
        self.assertIn("INSPECT", result["patch"])

        print("[PASS] test_review_task_noop")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 11C Validation Suite - CoderAgent")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCoderAgentProduction)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n[ALL TESTS PASSED] CoderAgent Phase 11C validation complete.")
    else:
        print(f"\n[FAILED] {len(result.failures)} failures, {len(result.errors)} errors.")
        sys.exit(1)
