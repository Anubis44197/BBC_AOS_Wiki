import hashlib
import json
import logging
from typing import Any, Dict, List
from bbc_aos.agents.base_agent import BaseAgent

# Configure logger
logger = logging.getLogger("bbc_aos.agents.context_agent")


class ContextAgent(BaseAgent):
    """
    ContextAgent is a production-ready agent responsible for task-focused
    context retrieval and lossless semantic packing. It retrieves the codebase
    symbol graph and full context from MemoryManager, optimizes symbol relevance,
    compiles task-specific subsets, and compresses the final package.
    """
    AGENT_ID: str = "context_agent"
    AGENT_VERSION: str = "1.0.0"
    SUPPORTED_ACTIONS: List[str] = ["get_task_context", "get_symbol_context", "get_file_context"]

    def initialize(self) -> None:
        """Performs initial setup and logs initialization telemetry."""
        logger.info("[CONTEXT AGENT] Initializing ContextAgent.")

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """
        Validates the incoming JSON-RPC parameters.
        
        Args:
            params: Parameters dictionary containing context and metadata envelopes.
            
        Returns:
            True if input complies with schema rules, False otherwise.
        """
        if not params:
            return False
        context = params.get("context", {})
        if not isinstance(context, dict):
            return False
        # Task must be present in context
        if "task" not in context:
            return False
        task = context["task"]
        if not isinstance(task, dict):
            return False
        # task_id and description are mandatory
        if "task_id" not in task or "description" not in task:
            return False
        
        metadata = params.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        # Metadata trace and replay IDs are mandatory
        if "trace_id" not in metadata or "replay_id" not in metadata:
            return False
            
        return True

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes deterministic context retrieval, optimization, and packing.
        
        Args:
            params: Input parameters validated by validate_input.
            
        Returns:
            A dictionary matching the context package schema format.
        """
        context = params["context"]
        metadata = params["metadata"]
        
        task = context["task"]
        task_id = task["task_id"]
        description = task["description"]
        task_deps = task.get("dependencies", [])
        
        trace_id = metadata["trace_id"]
        replay_id = metadata["replay_id"]
        
        logger.info(f"[CONTEXT AGENT] Resolving context for task '{task_id}': '{description}'")

        # 1. Retrieve the memory manager from params or create a fallback
        memory_manager = context.get("memory_manager")
        if not memory_manager:
            from bbc_aos.memory.runtime.memory_manager import MemoryManager
            memory_manager = MemoryManager()

        # 2. Query symbol graph from MemoryManager
        from bbc_aos.memory.runtime.memory_query import MemoryQuery
        graph_query = MemoryQuery(
            layer="semantic",
            filters={"memory_id": "symbol_graph"}
        )
        graph_result = memory_manager.query(graph_query, actor_role="agent")
        if not graph_result.records:
            logger.error("[CONTEXT AGENT ERROR] Symbol graph not found in semantic memory")
            raise ValueError("Symbol graph not found in semantic memory")
        symbol_graph = graph_result.records[0].data

        # 3. Query full context from MemoryManager
        context_query = MemoryQuery(
            layer="semantic",
            filters={"memory_id": "full_context"}
        )
        context_result = memory_manager.query(context_query, actor_role="agent")
        if not context_result.records:
            logger.error("[CONTEXT AGENT ERROR] Full context not found in semantic memory")
            raise ValueError("Full context not found in semantic memory")
        full_context = context_result.records[0].data

        # 4. Resolve task details (profile, file, symbol)
        task_profile = context.get("task_profile")
        target_file = context.get("target_file")
        target_symbol = context.get("target_symbol")
        
        if not target_symbol or not target_file or not task_profile:
            desc_lower = description.lower()
            if "bbc_scalar" in desc_lower or "scalar" in desc_lower:
                target_file = target_file or "bbc_aos/core/bbc_scalar.py"
                target_symbol = target_symbol or "BBCScalar"
            elif "matrix" in desc_lower or "matrix_ops" in desc_lower:
                target_file = target_file or "bbc_aos/core/matrix_ops.py"
                target_symbol = target_symbol or "MatrixOps"
            elif "index" in desc_lower or "quantizer" in desc_lower:
                target_file = target_file or "bbc_aos/knowledge/indexes/hmpu_indexer.py"
                target_symbol = target_symbol or "HMPUIndexer"
            elif "context" in desc_lower or "compiler" in desc_lower or "packer" in desc_lower:
                target_file = target_file or "bbc_aos/core/context_compiler.py"
                target_symbol = target_symbol or "TaskContextCompiler"
            elif "orchestrator" in desc_lower or "hmpu_engine" in desc_lower:
                target_file = target_file or "bbc_aos/core/orchestrator.py"
                target_symbol = target_symbol or "RecipeValidator"
            elif "fastapi" in desc_lower or "asgi" in desc_lower or "oauth" in desc_lower or "auth" in desc_lower:
                target_file = target_file or "asgi_app.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "bedesten" in desc_lower:
                target_file = target_file or "bedesten_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "kvkk" in desc_lower:
                target_file = target_file or "kvkk_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "bddk" in desc_lower:
                target_file = target_file or "bddk_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "kik" in desc_lower:
                target_file = target_file or "kik_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "yargitay" in desc_lower:
                target_file = target_file or "yargitay_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "danistay" in desc_lower:
                target_file = target_file or "danistay_mcp_module/client.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif "mcp" in desc_lower or "tool" in desc_lower or "legal" in desc_lower:
                target_file = target_file or "mcp_server_main.py"
                target_symbol = target_symbol or self._first_symbol_in_file(symbol_graph, target_file)
            elif not target_file or not target_symbol:
                fallback_symbol, fallback_file = self._first_indexed_target(symbol_graph)
                target_file = target_file or fallback_file
                target_symbol = target_symbol or fallback_symbol
                
            if "fix" in desc_lower or "bug" in desc_lower or "validation" in desc_lower:
                task_profile = task_profile or "bugfix"
            elif "refactor" in desc_lower or "migration" in desc_lower:
                task_profile = task_profile or "refactor"
            elif "review" in desc_lower or "audit" in desc_lower:
                task_profile = task_profile or "review"
            else:
                task_profile = task_profile or "feature"

        if not self._has_exact_symbol(target_symbol, symbol_graph):
            fallback_symbol, fallback_file = self._first_indexed_target(symbol_graph)
            target_file = fallback_file
            target_symbol = fallback_symbol

        # 5. Context reduction using ContextOptimizer
        from bbc_aos.core.context_optimizer import ContextOptimizer
        optimizer = ContextOptimizer(symbol_graph=symbol_graph, min_reduction_ratio=0.0)
        optimizer.optimize(target_symbol, context_file=target_file)
        
        # 6. Compilation using TaskContextCompiler
        from bbc_aos.core.context_compiler import TaskContextCompiler
        compiler = TaskContextCompiler(context_path_or_dict=full_context)
        compiled_context = compiler.compile(
            task=task_profile,
            target_file=target_file,
            target_symbols=[target_symbol]
        )
        
        # Extract selected files
        selected_files = [recipe["path"] for recipe in compiled_context.get("code_structure", [])]
        # Guard: Maximum selected files = 50
        selected_files = selected_files[:50]
        
        # 7. Semantic packing compression
        from bbc_aos.core.semantic_packer import SemanticPacker
        packer = SemanticPacker(aggressive=False)
        packed_context = packer.pack(compiled_context)
        
        # 8. Deterministic hashing of output payload
        packed_json = json.dumps(packed_context, sort_keys=True)
        hash_input = f"{task_id}_{trace_id}_{packed_json}"
        payload_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        
        result = {
            "trace_id": trace_id,
            "replay_id": replay_id,
            "deterministic_hash": payload_hash,
            "task_id": task_id,
            "selected_files": selected_files,
            "dependencies": task_deps,
            "packed_context": packed_context
        }
        
        # 9. Enforce ValidationGateway checks inside the agent itself
        from bbc_aos.integration.validation_gateway import ValidationGateway
        gateway = ValidationGateway()
        gateway.validate_output(self.AGENT_ID, result)
        
        # 10. Generate IntegrationAuditLog event inside the agent itself
        from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent
        audit_log = context.get("integration_log")
        if not audit_log:
            audit_log = IntegrationAuditLog()
            
        event = IntegrationAuditEvent(
            event_id=f"context_{trace_id}",
            event_type="context_resolution",
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=payload_hash,
            details={"task_id": task_id, "selected_files_count": len(selected_files)}
        )
        audit_log.append(event)
        
        return result

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validates output schema conformity, maximum depth, and file counts.
        
        Args:
            result: Context package dictionary produced by execute().
            
        Returns:
            True if output validates correctly, False otherwise.
        """
        if not result:
            return False
        required_fields = ["trace_id", "replay_id", "deterministic_hash", "task_id", "selected_files", "dependencies", "packed_context"]
        if not all(field in result for field in required_fields):
            return False
            
        selected_files = result["selected_files"]
        if not isinstance(selected_files, list) or len(selected_files) > 50:
            logger.error("[CONTEXT AGENT ERROR] Exceeded maximum selected files limit of 50")
            return False
            
        task_deps = result["dependencies"]
        if not isinstance(task_deps, list) or len(task_deps) > 5:
             logger.error("[CONTEXT AGENT ERROR] Task dependency count exceeds 5")
             return False
             
        return True

    def _has_exact_symbol(self, target_symbol: str, symbol_graph: Dict[str, Any]) -> bool:
        symbols = symbol_graph.get("symbols", [])
        exact_symbols = {item.get("symbol") for item in symbols if isinstance(item, dict)}
        exact_short_names = {str(symbol).split(".")[-1] for symbol in exact_symbols if symbol}
        return target_symbol in exact_symbols or target_symbol in exact_short_names

    def _first_indexed_target(self, symbol_graph: Dict[str, Any]) -> tuple[str, str]:
        symbols = [item for item in symbol_graph.get("symbols", []) if isinstance(item, dict) and item.get("symbol")]
        if not symbols:
            raise ValueError("Strict symbol resolution failed: symbol graph is empty")
        first = sorted(symbols, key=lambda item: str(item["symbol"]))[0]
        return str(first["symbol"]).split(".")[-1], str(first.get("file", ""))

    def _first_symbol_in_file(self, symbol_graph: Dict[str, Any], file_path: str) -> str:
        normalized_target = file_path.replace("\\", "/")
        symbols = [
            item
            for item in symbol_graph.get("symbols", [])
            if isinstance(item, dict) and str(item.get("file", "")).replace("\\", "/").endswith(normalized_target)
        ]
        if symbols:
            return str(symbols[0].get("symbol", "module")).split(".")[-1]
        return "module"


    def finalize(self) -> None:
        """Performs cleanup and completes telemetry logging."""
        logger.info("[CONTEXT AGENT] Finalizing ContextAgent.")
