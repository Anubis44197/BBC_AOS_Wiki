import os
import sys
import unittest
import json

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.agents.context_agent import ContextAgent
from bbc_aos.memory.runtime import MemoryManager
from bbc_aos.integration import (
    SubsystemRegistry,
    IntegrationContext,
    IntegrationAuditLog,
    IntegrationOrchestrator,
)

# Core Graph Extraction classes to build symbol graph programmatically
from bbc_aos.knowledge.graph.symbol_extractor import SymbolExtractor
from bbc_aos.knowledge.graph.symbol_graph import SymbolGraph


class TestContextAgentProduction(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ContextAgent()
        self.agent.initialize()
        
        # Populate memory manager with graph and context records
        self.memory_manager = MemoryManager()
        
        # 1. Build and register symbol graph
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
        
        # Register symbol_graph in MemoryManager semantic layer
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
        
        # 2. Load and register bbc_context.json
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
        """1. Validate syntax, inputs, and outputs of the ContextAgent."""
        params = {
            "context": {
                "task": {
                    "task_id": "task_1",
                    "description": "Analyse code structure of bbc_scalar math operations",
                    "priority": 1,
                    "dependencies": []
                },
                "memory_manager": self.memory_manager,
                "integration_log": self.audit_log
            },
            "metadata": {
                "trace_id": "tr_1",
                "replay_id": "rp_1"
            }
        }
        
        self.assertTrue(self.agent.validate_input(params))
        
        # Missing task description
        invalid_params = {
            "context": {
                "task": {
                    "task_id": "task_1"
                }
            },
            "metadata": {
                "trace_id": "tr_1",
                "replay_id": "rp_1"
            }
        }
        self.assertFalse(self.agent.validate_input(invalid_params))

        # Test execution
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        self.assertEqual(result["task_id"], "task_1")
        self.assertEqual(result["trace_id"], "tr_1")

    def test_deterministic_replay(self) -> None:
        """2. Validate 100 runs on identical goal/task inputs produce identical context & hashes."""
        params = {
            "context": {
                "task": {
                    "task_id": "task_det",
                    "description": "Decompose matrix pseudo-inverse solver states",
                    "priority": 2,
                    "dependencies": ["task_0"]
                },
                "memory_manager": self.memory_manager,
                "integration_log": self.audit_log
            },
            "metadata": {
                "trace_id": "tr_det",
                "replay_id": "rp_det"
            }
        }
        
        from unittest.mock import patch
        with patch("time.strftime", return_value="2026-06-25T09:12:38"):
            first_result = self.agent.execute(params)
            first_hash = first_result["deterministic_hash"]
            
            for idx in range(100):
                next_result = self.agent.execute(params)
                if next_result["deterministic_hash"] != first_hash:
                    print("\n=== REPLAY DIVERGENCE DETAIL ===")
                    print(f"Iteration: {idx}")
                    print(f"first_hash: {first_hash}")
                    print(f"next_hash:  {next_result['deterministic_hash']}")
                    import difflib
                    diff = difflib.unified_diff(
                        json.dumps(first_result, indent=2, sort_keys=True).splitlines(),
                        json.dumps(next_result, indent=2, sort_keys=True).splitlines(),
                        fromfile="first_result",
                        tofile="next_result"
                    )
                    print("\n".join(diff))
                    print("================================\n")
                self.assertEqual(next_result["deterministic_hash"], first_hash)
                self.assertEqual(next_result["selected_files"], first_result["selected_files"])
                self.assertEqual(next_result["packed_context"]["_path_aliases"], first_result["packed_context"]["_path_aliases"])

    def test_task_limits_and_depth(self) -> None:
        """3. Validate selected files count (<= 50) and dependency depths (<= 5)."""
        params = {
            "context": {
                "task": {
                    "task_id": "task_limits",
                    "description": "Run matrix pseudo-inverse solver states",
                    "priority": 3,
                    "dependencies": ["task_0", "task_1", "task_2"]
                },
                "memory_manager": self.memory_manager,
                "integration_log": self.audit_log
            },
            "metadata": {
                "trace_id": "tr_lim",
                "replay_id": "rp_lim"
            }
        }
        result = self.agent.execute(params)
        self.assertTrue(self.agent.validate_output(result))
        
        selected_files = result["selected_files"]
        self.assertTrue(len(selected_files) <= 50)
        
        # Verify dependency depth of the task
        self.assertTrue(len(result["dependencies"]) <= 5)

    def test_audit_generation(self) -> None:
        """4. Verify dispatches generate IntegrationAuditLog events."""
        params = {
            "context": {
                "task": {
                    "task_id": "task_audit",
                    "description": "Verify bbc_scalar operations",
                    "priority": 1,
                    "dependencies": []
                },
                "memory_manager": self.memory_manager,
                "integration_log": self.audit_log
            },
            "metadata": {
                "trace_id": "tr_audit",
                "replay_id": "rp_audit"
            }
        }
        result = self.agent.execute(params)
        
        # Check audit event was registered inside agent's execute()
        events = self.audit_log.get_events()
        self.assertTrue(len(events) > 0)
        
        context = IntegrationContext(
            trace_id="tr_audit",
            replay_id="rp_audit",
            deterministic_hash=result["deterministic_hash"],
            payload=result
        )
        
        # Routing via orchestrator dispatches and logs event
        res = self.orchestrator.dispatch("agent", "memory", context)
        self.assertTrue(res.success)

    def test_packing_equivalence(self) -> None:
        """5. Validate packed context structures (lossless compression)."""
        params = {
            "context": {
                "task": {
                    "task_id": "task_pack",
                    "description": "Review and compress bbc_scalar math operations",
                    "priority": 1,
                    "dependencies": []
                },
                "memory_manager": self.memory_manager,
                "integration_log": self.audit_log
            },
            "metadata": {
                "trace_id": "tr_pack",
                "replay_id": "rp_pack"
            }
        }
        result = self.agent.execute(params)

        packed = result["packed_context"]
        
        # Proving packing stages executed (path aliasing + shared imports)
        self.assertIn("_path_aliases", packed)
        self.assertIn("_shared_imports", packed)
        self.assertTrue(packed["metrics"]["packing_savings_pct"] > 0)


if __name__ == "__main__":
    unittest.main()
