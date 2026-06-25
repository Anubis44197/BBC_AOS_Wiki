"""
BBC Task-Aware Context Compiler - Phase 3
Generates task-specific subsets of context from the full bbc_context.json,
optimizing token count based on work profile configurations.
"""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Set, Union

# Centralized configuration component import
from bbc_aos.config import BBCConfig

# Set up logging namespace
logger = logging.getLogger("bbc_aos.core.context_compiler")

# Task profile definitions
TASK_PROFILES: Dict[str, Dict[str, Any]] = {
    "bugfix": {
        "description": "Bug fix — target file + direct dependencies + error context",
        "include_target": True,
        "include_direct_deps": True,
        "include_reverse_deps": True,
        "include_indirect_deps": False,
        "include_critical_symbols": False,
        "depth": 1,
        "max_files": 15,
        "priority_weight": {"target": 1.0, "direct_dep": 0.8, "reverse_dep": 0.6},
    },
    "feature": {
        "description": "New feature — related modules + interfaces + critical symbols",
        "include_target": True,
        "include_direct_deps": True,
        "include_reverse_deps": False,
        "include_indirect_deps": True,
        "include_critical_symbols": True,
        "depth": 2,
        "max_files": 25,
        "priority_weight": {"target": 1.0, "direct_dep": 0.7, "indirect_dep": 0.4, "critical": 0.5},
    },
    "refactor": {
        "description": "Refactor — target + full blast radius (all dependents)",
        "include_target": True,
        "include_direct_deps": True,
        "include_reverse_deps": True,
        "include_indirect_deps": True,
        "include_critical_symbols": False,
        "depth": 3,
        "max_files": 30,
        "priority_weight": {"target": 1.0, "direct_dep": 0.8, "reverse_dep": 0.9, "indirect_dep": 0.5},
    },
    "review": {
        "description": "Code review — broad structural view + critical symbols",
        "include_target": False,
        "include_direct_deps": False,
        "include_reverse_deps": False,
        "include_indirect_deps": False,
        "include_critical_symbols": True,
        "depth": 0,
        "max_files": 40,
        "priority_weight": {"critical": 0.8, "structure": 0.6},
    },
}


class TaskContextCompiler:
    """
    Compiles a task-specific context subset from a full context definition.
    Ranks files by target-relevance and dependencies, reducing model input tokens.
    """

    def __init__(self, context_path_or_dict: Union[str, Dict[str, Any]]) -> None:
        """
        Initializes the TaskContextCompiler.

        Args:
            context_path_or_dict: File path to bbc_context.json or parsed dictionary of full context.
        """
        if isinstance(context_path_or_dict, dict):
            self.full_context: Dict[str, Any] = context_path_or_dict
            self.context_path: str = ""
        else:
            if not os.path.exists(context_path_or_dict):
                logger.error(f"Target context file does not exist: '{context_path_or_dict}'")
                raise FileNotFoundError(f"Context not found: {context_path_or_dict}")
            with open(context_path_or_dict, "r", encoding="utf-8") as f:
                self.full_context = json.load(f)
            self.context_path = context_path_or_dict
            
        self.dep_graph: Dict[str, Any] = self.full_context.get("dependency_graph", {})
        self.code_structure: List[Dict[str, Any]] = self.full_context.get("code_structure", [])
        self.symbol_analysis: Dict[str, Any] = self.full_context.get("symbol_analysis", {})
        self.project_root: str = self.full_context.get("project_skeleton", {}).get("root", "")

        logger.info(f"TaskContextCompiler initialized. Full context file: '{self.context_path}'")

        # Build path -> recipe lookup and normalize windows separators in-place
        self._recipe_map: Dict[str, Dict[str, Any]] = {}
        for recipe in self.code_structure:
            path = recipe.get("path", "").replace("\\", "/")
            if path:
                recipe["path"] = path
                self._recipe_map[path] = recipe

        # Normalize keys in dependency graph
        normalized_graph: Dict[str, Any] = {}
        for k, v in self.dep_graph.items():
            nk = k.replace("\\", "/")
            normalized_graph[nk] = {
                "depends_on": [d.replace("\\", "/") for d in v.get("depends_on", [])],
                "depended_by": [d.replace("\\", "/") for d in v.get("depended_by", [])],
            }
        self.dep_graph = normalized_graph

    def compile(self, task: str, target_file: Optional[str] = None,
                target_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compiles the task-specific context based on the task profile.

        Args:
            task: Task type (one of 'bugfix', 'feature', 'refactor', 'review').
            target_file: Relative path to the focal file.
            target_symbols: Optional list of symbols being changed.

        Returns:
            A compiled context dictionary.
        """
        logger.info(f"Compiling context for task '{task}' (Target File: {target_file})")
        if task not in TASK_PROFILES:
            logger.error(f"Requested invalid task profile type: '{task}'")
            raise ValueError(f"Unknown task type '{task}'. Must be one of: {list(TASK_PROFILES.keys())}")

        profile = TASK_PROFILES[task]

        # Normalize target file path format
        if target_file:
            target_file = target_file.replace("\\", "/")
            if target_file not in self._recipe_map:
                for known in self._recipe_map:
                    if known.endswith(target_file) or target_file.endswith(known):
                        target_file = known
                        break

        scored_files: Dict[str, float] = {}

        # 1. Target file inclusion
        if profile["include_target"] and target_file and target_file in self._recipe_map:
            scored_files[target_file] = profile["priority_weight"].get("target", 1.0)

        # 2. Direct dependencies
        if profile["include_direct_deps"] and target_file:
            for dep in self._get_direct_deps(target_file):
                w = profile["priority_weight"].get("direct_dep", 0.7)
                scored_files[dep] = max(scored_files.get(dep, 0.0), w)

        # 3. Reverse dependencies
        if profile["include_reverse_deps"] and target_file:
            for dep in self._get_reverse_deps(target_file):
                w = profile["priority_weight"].get("reverse_dep", 0.6)
                scored_files[dep] = max(scored_files.get(dep, 0.0), w)

        # 4. Indirect transitive dependencies
        if profile["include_indirect_deps"] and target_file:
            depth = profile.get("depth", 2)
            for dep in self._get_transitive_deps(target_file, depth):
                if dep not in scored_files:
                    w = profile["priority_weight"].get("indirect_dep", 0.4)
                    scored_files[dep] = max(scored_files.get(dep, 0.0), w)

        # 5. Critical symbols
        if profile["include_critical_symbols"]:
            critical = self.symbol_analysis.get("critical_symbols", [])
            for sym in critical:
                sym_file = sym.get("file", "")
                if sym_file and sym_file in self._recipe_map:
                    w = profile["priority_weight"].get("critical", 0.5)
                    scored_files[sym_file] = max(scored_files.get(sym_file, 0.0), w)

        # 6. Fallback structural review allocation
        if task == "review" and not scored_files:
            for recipe in self.code_structure:
                path = recipe.get("path", "")
                stats = recipe.get("stats", {})
                code_lines = stats.get("code_lines", 0)
                if code_lines > 0:
                    score = min(1.0, code_lines / 500.0) * profile["priority_weight"].get("structure", 0.6)
                    scored_files[path] = max(scored_files.get(path, 0.0), score)

        # 7. Safety fallback to prevent completely empty context files
        if not scored_files:
            for recipe in self.code_structure:
                path = recipe.get("path", "")
                stats = recipe.get("stats", {})
                code_lines = stats.get("code_lines", 0)
                if code_lines > 0:
                    score = min(1.0, code_lines / 500.0) * 0.5
                    scored_files[path] = max(scored_files.get(path, 0.0), score)

        # Sort and limit target count
        max_files = profile["max_files"]
        ranked = sorted(scored_files.items(), key=lambda x: x[1], reverse=True)[:max_files]

        compiled_recipes = []
        compiled_files = []
        total_lines = 0
        total_code_lines = 0

        for file_path, score in ranked:
            recipe = self._recipe_map.get(file_path)
            if not recipe:
                continue
            compiled_recipes.append({
                **recipe,
                "_relevance_score": round(score, 3),
            })
            compiled_files.append(file_path)
            stats = recipe.get("stats", {})
            total_lines += stats.get("lines", 0)
            total_code_lines += stats.get("code_lines", 0)

        # Build local sub-graph
        compiled_deps = {}
        for fp in compiled_files:
            if fp in self.dep_graph:
                entry = self.dep_graph[fp]
                compiled_deps[fp] = {
                    "depends_on": [d for d in entry.get("depends_on", []) if d in compiled_files],
                    "depended_by": [d for d in entry.get("depended_by", []) if d in compiled_files],
                }

        # Filter critical symbols
        compiled_critical = []
        if self.symbol_analysis.get("critical_symbols"):
            compiled_file_set = set(compiled_files)
            for sym in self.symbol_analysis["critical_symbols"]:
                if sym.get("file", "") in compiled_file_set:
                    compiled_critical.append(sym)

        # Compute metric efficiencies
        full_context_str = json.dumps(self.full_context, ensure_ascii=False, default=str)
        compiled_output = {
            "bbc_instructions_version": self.full_context.get("bbc_instructions_version", "1.0"),
            "context_schema_version": self.full_context.get("context_schema_version", "8.5"),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "context_fresh": self.full_context.get("context_fresh", True),
            "fail_policy": self.full_context.get("fail_policy", "fail_closed"),
            "enforcement_level": self.full_context.get("enforcement_level", "strict"),
            "task_context": {
                "task_type": task,
                "task_profile": profile["description"],
                "target_file": target_file,
                "target_symbols": target_symbols or [],
                "files_included": len(compiled_files),
                "files_total": len(self.code_structure),
                "file_reduction_pct": round(
                    (1 - len(compiled_files) / max(len(self.code_structure), 1)) * 100, 1
                ),
            },
            "project_skeleton": {
                "root": self.project_root,
                "file_count": len(compiled_files),
                "hierarchy": compiled_files,
            },
            "code_structure": compiled_recipes,
            "dependency_graph": compiled_deps,
            "constraint_status": self.full_context.get("constraint_status", "verified"),
            "critical_symbols": compiled_critical,
            "metrics": {
                "files_scanned": len(compiled_files),
                "total_lines": total_lines,
                "code_lines": total_code_lines,
            },
        }

        compiled_str = json.dumps(compiled_output, ensure_ascii=False, default=str)
        full_tokens_est = len(full_context_str) // 4
        compiled_tokens_est = len(compiled_str) // 4
        saved = full_tokens_est - compiled_tokens_est
        pct = (saved / full_tokens_est * 100) if full_tokens_est > 0 else 0.0

        compiled_output["metrics"]["full_context_tokens_est"] = full_tokens_est
        compiled_output["metrics"]["compiled_tokens_est"] = compiled_tokens_est
        compiled_output["metrics"]["task_savings_pct"] = round(pct, 1)

        logger.info(f"Context compiled successfully. Token savings: {round(pct, 1)}%")
        return compiled_output

    def _get_direct_deps(self, file_path: str) -> List[str]:
        """Gets direct imports declared by the file."""
        entry = self.dep_graph.get(file_path, {})
        return entry.get("depends_on", [])

    def _get_reverse_deps(self, file_path: str) -> List[str]:
        """Gets reverse dependencies importing this file."""
        entry = self.dep_graph.get(file_path, {})
        return entry.get("depended_by", [])

    def _get_transitive_deps(self, file_path: str, max_depth: int = 2) -> List[str]:
        """Performs transitive traversal mapping dependencies."""
        visited: Set[str] = set()
        queue = [(file_path, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            entry = self.dep_graph.get(current, {})
            for dep in entry.get("depends_on", []) + entry.get("depended_by", []):
                if dep not in visited:
                    queue.append((dep, depth + 1))
        visited.discard(file_path)
        return list(visited)

    def save_compiled(self, compiled: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Saves compiled context to target file path."""
        if output_path is None:
            bbc_dir = BBCConfig.get_bbc_dir(self.project_root)
            task = compiled.get("task_context", {}).get("task_type", "unknown")
            output_path = os.path.join(bbc_dir, f"compiled_{task}.json")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(compiled, f, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"Compiled context saved to: '{output_path}'")
        return output_path
