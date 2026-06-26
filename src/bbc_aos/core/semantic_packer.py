"""
BBC Semantic Packer - Phase 3
Applies lossless compression algorithms to context dictionaries, reducing
token count by removing empty fields, path prefixing, and collapse thresholds.
"""

import copy
import json
import logging
import os
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Centralized configuration component import
from bbc_aos.config import BBCConfig

# Set up logging namespace
logger = logging.getLogger("bbc_aos.core.semantic_packer")


class SemanticPacker:
    """
    Implements multi-stage compression on context dictionaries to reduce LLM input sizes.
    """

    def __init__(self, aggressive: bool = False) -> None:
        """
        Initializes SemanticPacker.

        Args:
            aggressive: If True, uses more aggressive collapsing thresholds.
        """
        self.aggressive: bool = aggressive
        logger.info(f"SemanticPacker initialized in {'AGGRESSIVE' if aggressive else 'SAFE'} mode.")

    def pack(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies all packing compression stages to a copy of the context.

        Args:
            context: A dictionary of the full or compiled context.

        Returns:
            The packed context dictionary.
        """
        logger.info("Starting context packing execution flow...")
        packed = copy.deepcopy(context)
        before_size = len(json.dumps(packed, ensure_ascii=False, default=str))

        # Stage 1: Clean empty structure/stats fields
        packed["code_structure"] = self._clean_recipes(packed.get("code_structure", []))

        # Stage 2: Deduplicate redundant imports
        packed["code_structure"], import_index = self._deduplicate_imports(packed["code_structure"])

        # Stage 3: Collapse files below threshold limits
        packed["code_structure"], collapsed = self._collapse_small_files(packed["code_structure"])

        # Stage 4: Shorten path prefixes using aliases
        packed, alias_table = self._alias_paths(packed)

        # Stage 5: Strip LLM-irrelevant metadata
        packed = self._strip_metadata(packed)

        # Stage 6 (aggressive mode only): Condense dependency graph to edges count summary
        if self.aggressive:
            packed = self._compress_dep_graph(packed)

        after_size = len(json.dumps(packed, ensure_ascii=False, default=str))
        saved_pct = round((1 - after_size / before_size) * 100, 1) if before_size > 0 else 0.0

        # Record metrics inside output
        packed.setdefault("metrics", {})
        packed["metrics"]["packing_before_bytes"] = before_size
        packed["metrics"]["packing_after_bytes"] = after_size
        packed["metrics"]["packing_savings_pct"] = saved_pct
        packed["metrics"]["packing_collapsed_files"] = collapsed
        packed["metrics"]["packing_mode"] = "aggressive" if self.aggressive else "safe"

        packed["_shared_imports"] = import_index
        packed["_path_aliases"] = alias_table

        logger.info(f"Context packing complete. Savings: {saved_pct}% (Collapsed files: {collapsed})")
        return packed

    def _clean_recipes(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes empty arrays, null values, and redundant metadata from structure recipes."""
        cleaned = []
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
            cr = {"path": recipe.get("path", "")}

            # Structure definitions
            struct = recipe.get("structure", {})
            if isinstance(struct, dict):
                clean_struct = {}
                for k, v in struct.items():
                    if isinstance(v, list) and len(v) == 0:
                        continue
                    if v is None:
                        continue
                    clean_struct[k] = v
                if clean_struct:
                    cr["structure"] = clean_struct

            # Stats definitions
            stats = recipe.get("stats", {})
            if isinstance(stats, dict):
                useful_stats = {}
                for k in ("lines", "code_lines"):
                    if k in stats and stats[k]:
                        useful_stats[k] = stats[k]
                if useful_stats:
                    cr["stats"] = useful_stats

            if "_relevance_score" in recipe:
                cr["_relevance_score"] = recipe["_relevance_score"]

            cleaned.append(cr)
        return cleaned

    def _deduplicate_imports(self, recipes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Extracts repeated imports appearing in 3+ files to a shared dictionary block."""
        import_counter: Counter = Counter()
        for recipe in recipes:
            struct = recipe.get("structure", {})
            for imp in struct.get("imports", []):
                import_counter[imp] += 1

        shared = {imp for imp, cnt in import_counter.items() if cnt >= 3}
        if not shared:
            return recipes, {}

        shared_list = sorted(shared)
        import_index = {f"I{i}": imp for i, imp in enumerate(shared_list)}
        reverse_index = {imp: key for key, imp in import_index.items()}

        for recipe in recipes:
            struct = recipe.get("structure", {})
            if "imports" in struct:
                new_imports = []
                refs = []
                for imp in struct["imports"]:
                    if imp in reverse_index:
                        refs.append(reverse_index[imp])
                    else:
                        new_imports.append(imp)
                if refs:
                    struct["imports"] = new_imports
                    struct["_shared_import_refs"] = refs

        return recipes, import_index

    def _collapse_small_files(self, recipes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Replaces files lacking symbol declarations and below line thresholds with a collapsed tag."""
        threshold = 10 if not self.aggressive else 30
        kept = []
        collapsed_count = 0

        for recipe in recipes:
            struct = recipe.get("structure", {})
            classes = struct.get("classes", [])
            functions = struct.get("functions", [])
            stats = recipe.get("stats", {})
            code_lines = stats.get("code_lines", 0)

            if not classes and not functions and code_lines < threshold:
                kept.append({"path": recipe.get("path", ""), "_collapsed": True})
                collapsed_count += 1
            else:
                kept.append(recipe)

        return kept, collapsed_count

    def _alias_paths(self, packed: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Abbreviates directory prefixes using shorthand aliases (e.g. @a/ for bbc_core/)."""
        all_paths = []
        for recipe in packed.get("code_structure", []):
            p = recipe.get("path", "")
            if "/" in p:
                prefix = p.rsplit("/", 1)[0] + "/"
                all_paths.append(prefix)

        if not all_paths:
            return packed, {}

        prefix_counts = Counter(all_paths)
        frequent = {prefix for prefix, cnt in prefix_counts.items() if cnt >= 3}
        if not frequent:
            return packed, {}

        alias_table = {}
        for i, prefix in enumerate(sorted(frequent, key=len, reverse=True)):
            alias = f"@{chr(97 + i)}/"
            alias_table[alias] = prefix

        for recipe in packed.get("code_structure", []):
            path = recipe.get("path", "")
            for alias, prefix in alias_table.items():
                if path.startswith(prefix):
                    recipe["path"] = alias + path[len(prefix):]
                    break

        skeleton = packed.get("project_skeleton", {})
        if "hierarchy" in skeleton:
            new_hier = []
            for path in skeleton["hierarchy"]:
                replaced = path
                for alias, prefix in alias_table.items():
                    if path.startswith(prefix):
                        replaced = alias + path[len(prefix):]
                        break
                new_hier.append(replaced)
            skeleton["hierarchy"] = new_hier

        dep = packed.get("dependency_graph", {})
        if dep:
            new_dep = {}
            for k, v in dep.items():
                nk = k
                for alias, prefix in alias_table.items():
                    if k.startswith(prefix):
                        nk = alias + k[len(prefix):]
                        break
                new_v = {}
                for rel_type in ("depends_on", "depended_by"):
                    old_list = v.get(rel_type, [])
                    new_list = []
                    for p in old_list:
                        np = p
                        for alias, prefix in alias_table.items():
                            if p.startswith(prefix):
                                np = alias + p[len(prefix):]
                                break
                        new_list.append(np)
                    new_v[rel_type] = new_list
                new_dep[nk] = new_v
            packed["dependency_graph"] = new_dep

        return packed, alias_table

    def _strip_metadata(self, packed: Dict[str, Any]) -> Dict[str, Any]:
        """Removes LLM-irrelevant verification variables to save tokens."""
        for recipe in packed.get("code_structure", []):
            stats = recipe.get("stats", {})
            stats.pop("hash", None)
            stats.pop("raw_bytes", None)

        packed.pop("index_path", None)
        packed.pop("incremental", None)

        m = packed.get("metrics", {})
        keep_keys = {"files_scanned", "total_lines", "code_lines",
                     "raw_tokens", "context_tokens", "savings_pct",
                     "packing_before_bytes", "packing_after_bytes",
                     "packing_savings_pct", "packing_collapsed_files",
                     "packing_mode", "full_context_tokens_est",
                     "compiled_tokens_est", "task_savings_pct"}
        for k in list(m.keys()):
            if k not in keep_keys:
                del m[k]

        return packed

    def _compress_dep_graph(self, packed: Dict[str, Any]) -> Dict[str, Any]:
        """Compresses full dependency list to metrics summary in aggressive mode."""
        dep = packed.get("dependency_graph", {})
        if not dep:
            return packed

        total_deps = sum(len(v.get("depends_on", [])) for v in dep.values())
        total_rev = sum(len(v.get("depended_by", [])) for v in dep.values())

        dep_counts = {}
        for k, v in dep.items():
            dep_counts[k] = len(v.get("depended_by", []))
        top_deps = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        packed["dependency_summary"] = {
            "total_edges": total_deps,
            "total_reverse_edges": total_rev,
            "most_depended": [{"file": f, "depended_by": c} for f, c in top_deps if c > 0],
        }
        del packed["dependency_graph"]

        return packed

    def save_packed(self, packed: Dict[str, Any], output_path: Optional[str] = None,
                    project_root: Optional[str] = None) -> str:
        """Saves packed context dictionary to target location."""
        if output_path is None:
            root = project_root or packed.get("project_skeleton", {}).get("root", ".")
            bbc_dir = BBCConfig.get_bbc_dir(root)
            output_path = os.path.join(bbc_dir, "packed_context.json")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(packed, f, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"Packed context saved to: '{output_path}'")
        return output_path
