import os
import sys
import unittest
from typing import Dict, Any

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.memory.runtime import (
    MemoryManager,
    MemorySupervisor,
    MemoryRecord,
    MemoryQuery,
    MemoryResult,
    MemoryIndex,
    MemoryAuditLog,
    MemoryLifecycleManager,
    MemoryPromotionManager,
    MemoryVisibilityPolicy,
    MemoryRegistry,
    MemoryException,
    MemoryFrozenRegistryException,
    MemoryLifecycleException,
    MemoryPromotionException,
    MemoryVisibilityException,
    MemoryConflictException,
)


class TestMemoryRuntimeSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = MemoryRegistry()
        self.registry.reset()
        self.manager = MemoryManager()

    def test_syntax_and_imports(self) -> None:
        """1. Validate syntax and imports of all memory classes."""
        self.assertIsNotNone(MemoryManager)
        self.assertIsNotNone(MemorySupervisor)
        self.assertIsNotNone(MemoryRecord)
        self.assertIsNotNone(MemoryQuery)
        self.assertIsNotNone(MemoryResult)
        self.assertIsNotNone(MemoryIndex)
        self.assertIsNotNone(MemoryAuditLog)
        self.assertIsNotNone(MemoryLifecycleManager)
        self.assertIsNotNone(MemoryPromotionManager)
        self.assertIsNotNone(MemoryVisibilityPolicy)
        self.assertIsNotNone(MemoryRegistry)

    def test_record_immutability(self) -> None:
        """2. Validate MemoryRecord is strictly immutable."""
        rec = MemoryRecord(
            memory_id="m_1",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            version=1,
            created_at="2026-06-24T18:20:00Z",
            originating_agent="agent_1",
            data={"key": "val"}
        )
        self.assertEqual(rec.memory_id, "m_1")
        
        # Modifying attribute should raise AttributeError since it is frozen
        with self.assertRaises(AttributeError):
            rec.version = 2 # type: ignore

    def test_registry_uniqueness_and_freeze(self) -> None:
        """3. Validate registry registration constraints and freeze locks."""
        self.assertFalse(self.registry.is_frozen)
        
        class DummyLayer1:
            pass
        class DummyLayer2:
            pass

        self.registry.register_layer("working", DummyLayer1)
        self.assertEqual(self.registry.get_layer("working"), DummyLayer1)

        # Uniqueness check
        with self.assertRaises(ValueError):
            self.registry.register_layer("working", DummyLayer2)

        # Freeze check
        self.registry.freeze()
        self.assertTrue(self.registry.is_frozen)

        # Re-registering after freeze must fail
        with self.assertRaises(MemoryFrozenRegistryException):
            self.registry.register_layer("episodic", DummyLayer2)

    def test_lifecycle_transitions(self) -> None:
        """4. Validate deterministic lifecycle transitions."""
        lm = MemoryLifecycleManager()
        self.assertEqual(lm.get_state("m_1"), MemoryLifecycleManager.CREATED)

        lm.transition_to("m_1", MemoryLifecycleManager.INDEXED, "Indexed record")
        self.assertEqual(lm.get_state("m_1"), MemoryLifecycleManager.INDEXED)

        lm.transition_to("m_1", MemoryLifecycleManager.ACTIVE, "Activated")
        self.assertEqual(lm.get_state("m_1"), MemoryLifecycleManager.ACTIVE)

        lm.transition_to("m_1", MemoryLifecycleManager.ARCHIVED, "Archived")
        self.assertEqual(lm.get_state("m_1"), MemoryLifecycleManager.ARCHIVED)

        # Invalid transition: ARCHIVED -> ACTIVE
        with self.assertRaises(MemoryLifecycleException):
            lm.transition_to("m_1", MemoryLifecycleManager.ACTIVE, "Invalid transition")

    def test_promotions_and_approval_gates(self) -> None:
        """5. Validate promotion rules and human approval requirements."""
        rec_params = {
            "memory_id": "m_promo",
            "trace_id": "t_p",
            "replay_id": "r_p",
            "deterministic_hash": "hash_p",
            "version": 1,
            "created_at": "2026-06-24T18:20:00Z",
            "originating_agent": "planner_agent",
            "layer": "working",
            "data": {"layer": "working"}
        }
        
        # Create record in working memory (Loop Actor)
        rec = self.manager.create_record(rec_params, actor_role="loop")
        self.assertEqual(rec.data["layer"], "working")
        
        # Promote Working -> Episodic (Loop Actor)
        promoted_epi = self.manager.promote(rec, target_layer="episodic", actor_role="loop")
        self.assertEqual(promoted_epi.data["layer"], "episodic")
        self.assertEqual(promoted_epi.version, 2)

        # Promote Episodic -> Experience (Loop Actor)
        promoted_exp = self.manager.promote(promoted_epi, target_layer="experience", actor_role="loop")
        self.assertEqual(promoted_exp.data["layer"], "experience")
        self.assertEqual(promoted_exp.version, 3)

        # Create record in human knowledge layer (Human Actor)
        rec_human_params = rec_params.copy()
        rec_human_params["memory_id"] = "m_human"
        rec_human_params["layer"] = "human_knowledge"
        rec_human_params["data"] = {"layer": "human_knowledge"}
        rec_human = self.manager.create_record(rec_human_params, actor_role="human")

        # Promote Human -> Semantic (Human Actor - No approval provider assigned yet)
        with self.assertRaises(MemoryPromotionException):
            self.manager.promote(rec_human, target_layer="semantic", actor_role="human")

        # Assign approval provider and simulate approval (Confirm promo)
        self.manager.promotion_manager.set_approval_provider(lambda r: True)
        promoted_sem = self.manager.promote(rec_human, target_layer="semantic", actor_role="human")
        self.assertEqual(promoted_sem.data["layer"], "semantic")
        self.assertEqual(promoted_sem.version, 2)

    def test_visibility_permissions(self) -> None:
        """6. Validate role visibility (agents, loops, humans)."""
        rec_params = {
            "memory_id": "m_vis",
            "trace_id": "t_v",
            "replay_id": "r_v",
            "deterministic_hash": "hash_v",
            "version": 1,
            "created_at": "2026-06-24T18:20:00Z",
            "originating_agent": "planner_agent",
            "layer": "human_knowledge",
            "data": {"layer": "human_knowledge"}
        }
        
        # Loop cannot write to human_knowledge layer
        with self.assertRaises(MemoryVisibilityException):
            self.manager.create_record(rec_params, actor_role="loop")

        # Human can write to human_knowledge layer
        rec = self.manager.create_record(rec_params, actor_role="human")
        self.assertEqual(rec.memory_id, "m_vis")

    def test_audit_generation(self) -> None:
        """7. Validate that every operation creates a transaction audit log."""
        rec_params = {
            "memory_id": "m_audit",
            "trace_id": "t_a",
            "replay_id": "r_a",
            "deterministic_hash": "hash_a",
            "version": 1,
            "created_at": "2026-06-24T18:20:00Z",
            "originating_agent": "planner_agent",
            "layer": "working",
            "data": {"layer": "working"}
        }
        
        self.manager.create_record(rec_params, actor_role="loop")
        
        # Verify query trigger audit reads
        query = MemoryQuery(layer="working", filters={"memory_id": "m_audit"})
        self.manager.query(query, actor_role="loop")

        audit_history = self.manager.audit()
        self.assertTrue(len(audit_history) >= 2)
        
        operations = [x["operation"] for x in audit_history]
        self.assertIn("CREATE", operations)
        self.assertIn("READ", operations)


if __name__ == "__main__":
    unittest.main()
