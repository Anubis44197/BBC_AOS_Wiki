"""Phase 11E Validation Suite - VerificationAgent Production Implementation

Validates:
1. Syntax and schema validation (input/output contracts)
2. Deterministic replay (100 runs, zero variance)
3. Verdict consistency (same input produces identical verdicts)
4. Violation detection (blast radius, risk mismatch, ordering, cyclic deps, depth limit)
5. Audit event generation (IntegrationAuditLog compliance)
6. Contract hash and structural rules validation
"""

import os
import sys
import unittest
import hashlib
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.agents.verification_agent import VerificationAgent, _VerificationEngine
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
    modified=["bbc_aos/core/bbc_scalar.py"],
    added=[],
    removed=[],
    trace_id="tr_verify",
    replay_id="rp_verify",
) -> dict:
    """Builds a mock CodeDiff dictionary."""
    return {
        "modified_files": modified,
        "added_files": added,
        "removed_files": removed,
        "patch": "--- a/some_file\n+++ b/some_file",
        "trace_id": trace_id,
        "replay_id": replay_id,
        "deterministic_hash": "a" * 64,
    }


def _make_validation_plan(
    tasks=None,
    risk_level="MEDIUM",
    trace_id="tr_verify",
    replay_id="rp_verify",
) -> dict:
    """Builds a mock ValidationPlan dictionary."""
    if tasks is None:
        tasks = [
            {
                "task_id": "val_0_syntax",
                "test_type": "syntax",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Verify syntax check",
                "priority": 1,
                "dependencies": [],
            },
            {
                "task_id": "val_0_unit",
                "test_type": "unit",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Execute unit tests",
                "priority": 2,
                "dependencies": ["val_0_syntax"],
            }
        ]

    return {
        "trace_id": trace_id,
        "replay_id": replay_id,
        "deterministic_hash": "b" * 64,
        "validation_tasks": tasks,
        "risk_level": risk_level,
        "coverage_targets": {
            "syntax": True,
            "unit": True,
            "integration": False,
            "regression": True,
            "replay": True,
        }
    }


def _make_packed_context(
    selected=["bbc_aos/core/bbc_scalar.py"]
) -> dict:
    """Builds a mock packed_context package."""
    return {
        "selected_files": selected,
        "dependencies": [],
        "packed_context": {},
    }


def _make_valid_params(
    task_id="task_verify",
    description="Fix bug in scalar calculations",
    code_diff=None,
    validation_plan=None,
    packed_context=None,
    trace_id="tr_verify",
    replay_id="rp_verify",
    audit_log=None,
) -> dict:
    """Combines inputs into valid parameters envelope."""
    return {
        "context": {
            "task": {
                "task_id": task_id,
                "description": description,
                "dependencies": [],
            },
            "code_diff": code_diff or _make_code_diff(trace_id=trace_id, replay_id=replay_id),
            "validation_plan": validation_plan or _make_validation_plan(trace_id=trace_id, replay_id=replay_id),
            "packed_context": packed_context or _make_packed_context(),
            "integration_log": audit_log or IntegrationAuditLog(),
        },
        "metadata": {
            "trace_id": trace_id,
            "replay_id": replay_id,
        }
    }


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestVerificationAgentProduction(unittest.TestCase):

    def setUp(self) -> None:
        self.agent = VerificationAgent()
        self.agent.initialize()
        self.audit_log = IntegrationAuditLog()

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
        """1. Validate input schema enforcement."""
        params = _make_valid_params(audit_log=self.audit_log)
        self.assertTrue(self.agent.validate_input(params), "Valid params should pass.")

        # Missing task
        bad = _make_valid_params(audit_log=self.audit_log)
        del bad["context"]["task"]
        self.assertFalse(self.agent.validate_input(bad))

        # Missing code_diff
        bad2 = _make_valid_params(audit_log=self.audit_log)
        del bad2["context"]["code_diff"]
        self.assertFalse(self.agent.validate_input(bad2))

        # Missing validation_plan
        bad3 = _make_valid_params(audit_log=self.audit_log)
        del bad3["context"]["validation_plan"]
        self.assertFalse(self.agent.validate_input(bad3))

        # Missing packed_context
        bad4 = _make_valid_params(audit_log=self.audit_log)
        del bad4["context"]["packed_context"]
        self.assertFalse(self.agent.validate_input(bad4))

        # Missing metadata
        bad5 = _make_valid_params(audit_log=self.audit_log)
        del bad5["metadata"]
        self.assertFalse(self.agent.validate_input(bad5))

        print("[PASS] test_input_validation")

    def test_output_validation(self) -> None:
        """2. Execute and validate output schema compliance."""
        params = _make_valid_params(
            task_id="task_out",
            description="Fix bug in scalar matrix inverse solver",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result), "Output should pass validation.")

        # Check fields
        for field in ("trace_id", "replay_id", "deterministic_hash",
                      "verdict", "violations", "risk_level", "validation_summary"):
            self.assertIn(field, result, f"Missing field: {field}")

        self.assertEqual(result["verdict"], "APPROVED")
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(len(result["deterministic_hash"]), 64)

        print("[PASS] test_output_validation")

    def test_deterministic_replay(self) -> None:
        """3. Validate 100 runs on identical inputs produce identical verdicts and hashes."""
        params = _make_valid_params(
            task_id="task_det",
            description="Fix memory leak in state_manager",
            audit_log=self.audit_log,
        )

        first = self.agent.execute(params)
        first_hash = first["deterministic_hash"]
        first_verdict = first["verdict"]

        for i in range(100):
            res = self.agent.execute(params)
            self.assertEqual(res["deterministic_hash"], first_hash, f"Hash mismatch at run {i}")
            self.assertEqual(res["verdict"], first_verdict, f"Verdict mismatch at run {i}")

        print("[PASS] test_deterministic_replay (100 iterations, zero variance)")

    def test_blast_radius_violation(self) -> None:
        """4. Verify that blast radius violation produces REJECTED verdict."""
        # Modifies a file not selected in context
        code_diff = _make_code_diff(modified=["bbc_aos/core/hacker_module.py"])
        packed_context = _make_packed_context(selected=["bbc_aos/core/bbc_scalar.py"])

        params = _make_valid_params(
            task_id="task_blast",
            description="Fix bug in scalar calculations",
            code_diff=code_diff,
            packed_context=packed_context,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertGreater(len(result["violations"]), 0)
        self.assertTrue(any("Blast radius" in v for v in result["violations"]))

        print("[PASS] test_blast_radius_violation")

    def test_risk_mismatch_violation(self) -> None:
        """5. Verify that risk level mismatch produces REJECTED verdict."""
        # Description triggers MEDIUM risk, but plan claims LOW
        validation_plan = _make_validation_plan(risk_level="LOW")
        params = _make_valid_params(
            task_id="task_risk",
            description="Fix bug in scalar calculations",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("Risk" in v for v in result["violations"]))

        print("[PASS] test_risk_mismatch_violation")

    def test_sorting_contract_violation(self) -> None:
        """6. Verify that validation tasks sorting mismatch produces REJECTED verdict."""
        # Unsorted tasks (priority 2 before priority 1)
        unsorted_tasks = [
            {
                "task_id": "val_0_unit",
                "test_type": "unit",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Execute unit tests",
                "priority": 2,
                "dependencies": [],
            },
            {
                "task_id": "val_0_syntax",
                "test_type": "syntax",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Verify syntax check",
                "priority": 1,
                "dependencies": [],
            }
        ]
        validation_plan = _make_validation_plan(tasks=unsorted_tasks)
        params = _make_valid_params(
            task_id="task_sort",
            description="Fix bug in scalar calculations",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("Contract" in v for v in result["violations"]))

        print("[PASS] test_sorting_contract_violation")

    def test_cyclic_dependency_violation(self) -> None:
        """7. Verify that task cyclic dependency produces REJECTED verdict."""
        # Cyclic dependency: val_0_syntax depends on val_0_unit, and val_0_unit depends on val_0_syntax
        cyclic_tasks = [
            {
                "task_id": "val_0_syntax",
                "test_type": "syntax",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Verify syntax check",
                "priority": 1,
                "dependencies": ["val_0_unit"],
            },
            {
                "task_id": "val_0_unit",
                "test_type": "unit",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Execute unit tests",
                "priority": 2,
                "dependencies": ["val_0_syntax"],
            }
        ]
        validation_plan = _make_validation_plan(tasks=cyclic_tasks)
        params = _make_valid_params(
            task_id="task_cycle",
            description="Fix bug in scalar calculations",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("Cyclic dependency" in v for v in result["violations"]))

        print("[PASS] test_cyclic_dependency_violation")

    def test_dependency_depth_violation(self) -> None:
        """8. Verify that task dependency depth > 5 produces REJECTED verdict."""
        # Chain of 6 dependencies: val_5 -> val_4 -> val_3 -> val_2 -> val_1 -> val_0
        chain_tasks = [
            {"task_id": "val_0", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": []},
            {"task_id": "val_1", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": ["val_0"]},
            {"task_id": "val_2", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": ["val_1"]},
            {"task_id": "val_3", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": ["val_2"]},
            {"task_id": "val_4", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": ["val_3"]},
            {"task_id": "val_5", "test_type": "syntax", "target_file": "bbc_aos/core/bbc_scalar.py", "description": "T", "priority": 1, "dependencies": ["val_4"]},
        ]
        validation_plan = _make_validation_plan(tasks=chain_tasks)
        params = _make_valid_params(
            task_id="task_depth",
            description="Fix bug in scalar calculations",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("depth" in v for v in result["violations"]))

        print("[PASS] test_dependency_depth_violation")

    def test_audit_event_generation(self) -> None:
        """9. Verify IntegrationAuditLog events are generated on execute()."""
        local_audit_log = IntegrationAuditLog()
        params = _make_valid_params(
            task_id="task_audit",
            description="Fix bug in scalar calculations",
            trace_id="tr_audit",
            replay_id="rp_audit",
            audit_log=local_audit_log,
        )

        result = self.agent.execute(params)
        events = local_audit_log.get_events()

        self.assertGreater(len(events), 0, "At least one audit event should be emitted.")
        event = events[-1]
        self.assertEqual(event.event_type, "contract_verified")
        self.assertEqual(event.trace_id, "tr_audit")
        self.assertEqual(event.replay_id, "rp_audit")
        self.assertEqual(event.deterministic_hash, result["deterministic_hash"])
        self.assertEqual(event.details["verdict"], "APPROVED")
        self.assertEqual(event.details["violations_count"], 0)

        # Dispatching through orchestrator
        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result,
        )
        dispatch_result = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(dispatch_result.success)

        print("[PASS] test_audit_event_generation")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 11E Validation Suite - VerificationAgent")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestVerificationAgentProduction)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n[ALL TESTS PASSED] VerificationAgent Phase 11E validation complete.")
    else:
        print(f"\n[FAILED] {len(result.failures)} failures, {len(result.errors)} errors.")
        sys.exit(1)
