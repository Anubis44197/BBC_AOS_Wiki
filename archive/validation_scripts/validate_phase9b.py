import os
import sys
import unittest
from typing import Dict, Any

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.integration import (
    IntegrationException,
    IntegrationFrozenRegistryException,
    IntegrationValidationException,
    IntegrationSyncException,
    IntegrationLifecycleException,
    SubsystemRegistry,
    IntegrationContext,
    IntegrationResult,
    IntegrationAuditLog,
    IntegrationAuditEvent,
    ValidationGateway,
    ReplayEngine,
    HealthManager,
    IntegrationSupervisor,
    IntegrationOrchestrator,
)


class TestIntegrationRuntimeSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SubsystemRegistry()
        self.registry.reset()
        self.audit_log = IntegrationAuditLog()
        self.orchestrator = IntegrationOrchestrator(self.registry, self.audit_log)

    def test_syntax_and_imports(self) -> None:
        """1. Validate syntax and imports of all integration package classes."""
        self.assertIsNotNone(IntegrationException)
        self.assertIsNotNone(IntegrationFrozenRegistryException)
        self.assertIsNotNone(IntegrationValidationException)
        self.assertIsNotNone(IntegrationSyncException)
        self.assertIsNotNone(IntegrationLifecycleException)
        self.assertIsNotNone(SubsystemRegistry)
        self.assertIsNotNone(IntegrationContext)
        self.assertIsNotNone(IntegrationResult)
        self.assertIsNotNone(IntegrationAuditLog)
        self.assertIsNotNone(IntegrationAuditEvent)
        self.assertIsNotNone(ValidationGateway)
        self.assertIsNotNone(ReplayEngine)
        self.assertIsNotNone(HealthManager)
        self.assertIsNotNone(IntegrationSupervisor)
        self.assertIsNotNone(IntegrationOrchestrator)

    def test_context_and_result_immutability(self) -> None:
        """2. Validate IntegrationContext and IntegrationResult are strictly immutable."""
        context = IntegrationContext(
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            payload={"action": "run"},
        )
        self.assertEqual(context.trace_id, "t_1")
        with self.assertRaises(AttributeError):
            context.trace_id = "t_new"  # type: ignore

        result = IntegrationResult(
            success=True,
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            data={"result": "ok"},
        )
        self.assertTrue(result.success)
        with self.assertRaises(AttributeError):
            result.success = False  # type: ignore

    def test_registry_uniqueness_and_freeze(self) -> None:
        """3. Validate registry uniqueness checks and freeze gates."""
        self.assertFalse(self.registry.is_frozen)

        class MockSubsystem1:
            pass

        class MockSubsystem2:
            pass

        self.registry.register_subsystem("memory", MockSubsystem1())
        self.assertIsInstance(self.registry.get_subsystem("memory"), MockSubsystem1)

        # Uniqueness violation
        with self.assertRaises(ValueError):
            self.registry.register_subsystem("memory", MockSubsystem2())

        # Freeze check
        self.registry.freeze()
        self.assertTrue(self.registry.is_frozen)

        with self.assertRaises(IntegrationFrozenRegistryException):
            self.registry.register_subsystem("knowledge", MockSubsystem2())

    def test_health_validation(self) -> None:
        """4. Verify HealthManager health contracts checks."""
        class MockHealthySubsystem:
            def get_health_status(self) -> Dict[str, Any]:
                return {
                    "subsystem": "test_sub",
                    "status": "OK",
                    "is_frozen": True,
                    "metrics": {},
                    "timestamp": "2026-06-24T18:40:00Z"
                }

        class MockUnhealthySubsystem:
            def get_health_status(self) -> Dict[str, Any]:
                return {
                    "subsystem": "test_sub_unhealthy",
                    "status": "UNHEALTHY",
                    "is_frozen": False,
                    "metrics": {},
                    "timestamp": "2026-06-24T18:40:00Z"
                }

        self.registry.register_subsystem("healthy", MockHealthySubsystem())
        self.registry.register_subsystem("unhealthy", MockUnhealthySubsystem())

        health_mgr = HealthManager(self.registry)
        self.assertEqual(health_mgr.check_subsystem_health("healthy")["status"], "OK")
        self.assertEqual(health_mgr.check_subsystem_health("unhealthy")["status"], "UNHEALTHY")

        # Supervisor health sweep checks
        self.assertTrue(self.orchestrator.check_health(["healthy"]))
        self.assertFalse(self.orchestrator.check_health(["healthy", "unhealthy"]))

    def test_startup_and_shutdown_sequencing(self) -> None:
        """5. Verify deterministic startup, shutdown and recovery sequencing."""
        sequence = ["core", "memory", "knowledge"]
        
        # Test startup sequencing
        self.orchestrator.startup(sequence)
        events = self.audit_log.get_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "startup_step")
        self.assertEqual(events[0].details["step"], "core")
        self.assertEqual(events[2].details["step"], "knowledge")

        # Test shutdown sequencing
        self.orchestrator.shutdown(sequence[::-1])
        events_after_stop = self.audit_log.get_events()
        self.assertEqual(len(events_after_stop), 6)
        self.assertEqual(events_after_stop[3].event_type, "shutdown_step")
        self.assertEqual(events_after_stop[3].details["step"], "knowledge")

        # Test recovery sequencing
        self.orchestrator.recover("checkpoint_99", "t_rec", "r_rec")
        events_after_rec = self.audit_log.get_events()
        self.assertEqual(len(events_after_rec), 7)
        self.assertEqual(events_after_rec[6].event_type, "recovery_step")
        self.assertEqual(events_after_rec[6].details["checkpoint_id"], "checkpoint_99")

    def test_validation_gateway_and_dispatches(self) -> None:
        """6. Validate ValidationGateway and Orchestrator dispatch validations."""
        context_ok = IntegrationContext(
            trace_id="t_ok",
            replay_id="r_ok",
            deterministic_hash="hash_ok",
            payload={"trigger_validation_failure": False},
        )
        res_ok = self.orchestrator.dispatch("agent", "memory", context_ok)
        self.assertTrue(res_ok.success)

        context_fail = IntegrationContext(
            trace_id="t_fail",
            replay_id="r_fail",
            deterministic_hash="hash_fail",
            payload={"trigger_validation_failure": True},
        )
        with self.assertRaises(IntegrationValidationException):
            self.orchestrator.dispatch("agent", "memory", context_fail)

    def test_replay_reconstruction(self) -> None:
        """7. Verify ReplayEngine gathers history chronologically matching replay_id."""
        context_rep = IntegrationContext(
            trace_id="t_rep",
            replay_id="r_rep",
            deterministic_hash="hash_rep",
            payload={"action": "repay_test"},
        )
        self.orchestrator.dispatch("agent", "memory", context_rep)

        reconstructed = self.orchestrator.replay_engine.reconstruct_execution("r_rep", self.audit_log)
        self.assertEqual(len(reconstructed), 1)
        self.assertEqual(reconstructed[0].trace_id, "t_rep")
        self.assertEqual(reconstructed[0].deterministic_hash, "hash_rep")


if __name__ == "__main__":
    unittest.main()
