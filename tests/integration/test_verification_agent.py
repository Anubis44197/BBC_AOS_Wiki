import os
import sys
import unittest
import hashlib
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.agents.verification_agent import VerificationAgent, _VerificationEngine
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)


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
        "code_structure": [],
        "_path_aliases": {},
        "_shared_imports": [],
        "metrics": {"packing_savings_pct": 0, "packing_mode": "safe"},
    }


def _make_valid_params(
    task_id: str = "task_1",
    description: str = "Fix bug in scalar calculations",
    code_diff: dict = None,
    validation_plan: dict = None,
    packed_context: dict = None,
    trace_id: str = "tr_verify",
    replay_id: str = "rp_verify",
    audit_log=None,
) -> dict:
    """Creates parameter payload matching input schema contract."""
    if code_diff is None:
        code_diff = _make_code_diff(trace_id=trace_id, replay_id=replay_id)
    if validation_plan is None:
        validation_plan = _make_validation_plan(trace_id=trace_id, replay_id=replay_id)
    if packed_context is None:
        packed_context = _make_packed_context()

    return {
        "context": {
            "task": {
                "task_id": task_id,
                "description": description,
                "priority": 1,
                "dependencies": [],
            },
            "code_diff": code_diff,
            "validation_plan": validation_plan,
            "packed_context": packed_context,
            "integration_log": audit_log or IntegrationAuditLog(),
        },
        "metadata": {
            "trace_id": trace_id,
            "replay_id": replay_id,
        },
    }


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
        """1. Validate input schema — required fields enforcement."""
        params = _make_valid_params(audit_log=self.audit_log)
        self.assertTrue(self.agent.validate_input(params), "Valid params should pass.")

        bad = _make_valid_params(audit_log=self.audit_log)
        del bad["context"]["task"]["task_id"]
        self.assertFalse(self.agent.validate_input(bad))

        bad2 = _make_valid_params(audit_log=self.audit_log)
        del bad2["context"]["code_diff"]
        self.assertFalse(self.agent.validate_input(bad2))

        bad3 = _make_valid_params(audit_log=self.audit_log)
        del bad3["context"]["validation_plan"]
        self.assertFalse(self.agent.validate_input(bad3))

        bad4 = _make_valid_params(audit_log=self.audit_log)
        del bad4["context"]["packed_context"]
        self.assertFalse(self.agent.validate_input(bad4))

        self.assertFalse(self.agent.validate_input({}))
        self.assertFalse(self.agent.validate_input(None))

    def test_output_validation(self) -> None:
        """2. Execute and validate output schema compliance."""
        params = _make_valid_params(
            task_id="task_out",
            trace_id="tr_out",
            replay_id="rp_out",
            audit_log=self.audit_log,
        )
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result), "Output should pass validation.")

        for field in ("verdict", "violations", "trace_id", "replay_id", "deterministic_hash"):
            self.assertIn(field, result, f"Missing field: {field}")

        self.assertEqual(result["trace_id"], "tr_out")
        self.assertEqual(result["replay_id"], "rp_out")
        self.assertEqual(len(result["deterministic_hash"]), 64)

    def test_deterministic_replay(self) -> None:
        """3. Validate 100 runs on identical inputs produce identical verdicts."""
        params = _make_valid_params(
            task_id="task_det",
            trace_id="tr_det",
            replay_id="rp_det",
            audit_log=self.audit_log,
        )

        first_result = self.agent.execute(params)
        first_hash = first_result["deterministic_hash"]
        first_verdict = first_result["verdict"]

        for i in range(100):
            result = self.agent.execute(params)
            self.assertEqual(result["deterministic_hash"], first_hash)
            self.assertEqual(result["verdict"], first_verdict)

    def test_blast_radius_violation(self) -> None:
        """4. Reject diffs affecting files outside packed context selected_files."""
        code_diff = _make_code_diff(modified=["bbc_aos/core/hacked_file.py"])
        packed_context = _make_packed_context(selected=["bbc_aos/core/bbc_scalar.py"])
        params = _make_valid_params(
            task_id="task_blast",
            code_diff=code_diff,
            packed_context=packed_context,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("blast radius" in v.lower() for v in result["violations"]))

    def test_risk_level_mismatch_violation(self) -> None:
        """5. Reject if planner's task priority doesn't match tester's calculated risk."""
        # Task priority = 1 (LOW risk expected) but Tester plan has HIGH risk
        validation_plan = _make_validation_plan(risk_level="HIGH")
        params = _make_valid_params(
            task_id="task_risk",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("risk" in v.lower() for v in result["violations"]))

    def test_out_of_order_dependencies_violation(self) -> None:
        """6. Reject if validation tasks execute before dependencies."""
        bad_tasks = [
            {
                "task_id": "val_unit",
                "test_type": "unit",
                "target_file": "bbc_aos/core/bbc_scalar.py",
                "description": "Execute unit tests",
                "priority": 2,
                "dependencies": ["val_syntax"], # dependency declared but not present in registry yet
            }
        ]
        validation_plan = _make_validation_plan(tasks=bad_tasks)
        params = _make_valid_params(
            task_id="task_order",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("dependency" in v.lower() for v in result["violations"]))

    def test_cyclic_dependencies_violation(self) -> None:
        """7. Reject cyclic dependencies inside validation plan."""
        cyclic_tasks = [
            {"task_id": "t1", "test_type": "unit", "target_file": "f.py", "description": "T", "priority": 1, "dependencies": ["t2"]},
            {"task_id": "t2", "test_type": "unit", "target_file": "f.py", "description": "T", "priority": 1, "dependencies": ["t1"]},
        ]
        validation_plan = _make_validation_plan(tasks=cyclic_tasks)
        params = _make_valid_params(
            task_id="task_cyclic",
            validation_plan=validation_plan,
            audit_log=self.audit_log,
        )

        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertTrue(any("cyclic" in v.lower() for v in result["violations"]))

    def test_dependency_depth_violation(self) -> None:
        """8. Reject validation plan with dependency chain depth > 5."""
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

        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result,
        )
        dispatch_result = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(dispatch_result.success)


if __name__ == "__main__":
    unittest.main()
