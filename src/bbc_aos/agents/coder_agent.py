"""BBC-AOS CoderAgent.

The agent produces deterministic, workspace-bounded Python patches from the
blast radius selected by ContextAgent. It does not call external AI services and
does not write files directly; CommitManager remains the only write gateway.
"""

import ast
import difflib
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bbc_aos.agents.base_agent import BaseAgent

logger = logging.getLogger("bbc_aos.agents.coder_agent")


class CodeDiff:
    """Immutable representation of a deterministic code modification plan."""

    __slots__ = (
        "modified_files",
        "added_files",
        "removed_files",
        "patch",
        "trace_id",
        "replay_id",
        "deterministic_hash",
    )

    def __init__(
        self,
        modified_files: List[str],
        added_files: List[str],
        removed_files: List[str],
        patch: str,
        trace_id: str,
        replay_id: str,
        deterministic_hash: str,
    ) -> None:
        object.__setattr__(self, "modified_files", modified_files)
        object.__setattr__(self, "added_files", added_files)
        object.__setattr__(self, "removed_files", removed_files)
        object.__setattr__(self, "patch", patch)
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "replay_id", replay_id)
        object.__setattr__(self, "deterministic_hash", deterministic_hash)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("CodeDiff is immutable.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modified_files": self.modified_files,
            "added_files": self.added_files,
            "removed_files": self.removed_files,
            "patch": self.patch,
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "deterministic_hash": self.deterministic_hash,
        }


class _DeterministicDiffEngine:
    """Generates deterministic real patches from in-scope Python files."""

    _OPERATION_MAP: Dict[str, str] = {
        "fix": "bugfix",
        "bug": "bugfix",
        "patch": "bugfix",
        "error": "bugfix",
        "repair": "bugfix",
        "refactor": "refactor",
        "restructure": "refactor",
        "clean": "refactor",
        "reorganize": "refactor",
        "migrate": "refactor",
        "feature": "feature",
        "add": "feature",
        "implement": "feature",
        "extend": "feature",
        "introduce": "feature",
        "review": "review",
        "audit": "review",
        "analyse": "review",
        "analyze": "review",
        "inspect": "review",
        "check": "review",
        "test": "test",
        "tests": "test",
        "pytest": "test",
    }

    MAX_DIFF_FILES: int = 20

    def generate(
        self,
        task_id: str,
        description: str,
        selected_files: List[str],
        packed_context: Dict[str, Any],
        trace_id: str,
        workspace_root: str = ".",
    ) -> Dict[str, Any]:
        operation = self._classify_operation(description)
        blast_radius = selected_files[: self.MAX_DIFF_FILES]
        resolved_files = self._resolve_existing_python_files(
            blast_radius,
            packed_context,
            workspace_root,
        )

        if not resolved_files:
            logger.warning("[DIFF ENGINE] No readable Python files in blast radius.")
            return self._build_review_result(task_id, blast_radius, "No readable Python files in scope")

        if operation == "review":
            return self._build_review_result(task_id, [rel for rel, _ in resolved_files], "Review mode")
        if operation == "test":
            return self._build_test_result(task_id, resolved_files)

        modified_files: List[str] = []
        patch_chunks: List[str] = []
        for rel_path, abs_path in resolved_files:
            original = abs_path.read_text(encoding="utf-8", errors="ignore")
            updated = self._transform_python_source(original, operation, task_id, description)
            if updated == original:
                continue
            modified_files.append(rel_path)
            patch_chunks.extend(
                difflib.unified_diff(
                    original.splitlines(),
                    updated.splitlines(),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
            )

        if not modified_files:
            return self._build_review_result(
                task_id,
                [rel for rel, _ in resolved_files],
                "No safe AST transform available",
            )

        return self._build_result(modified_files, [], [], "\n".join(patch_chunks), operation)

    def _classify_operation(self, description: str) -> str:
        """Classifies the task operation type from the description string."""
        desc_lower = description.lower()
        for keyword, op in self._OPERATION_MAP.items():
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, desc_lower):
                return op
        return "feature"

    def _resolve_existing_python_files(
        self,
        selected_files: List[str],
        packed_context: Dict[str, Any],
        workspace_root: str,
    ) -> List[Tuple[str, Path]]:
        root = Path(workspace_root or ".").resolve()
        aliases = packed_context.get("_path_aliases", {})
        resolved: List[Tuple[str, Path]] = []

        for raw_path in selected_files:
            rel_path = self._expand_alias(str(raw_path).replace("\\", "/"), aliases)
            if not rel_path.endswith(".py"):
                continue
            candidate = (root / rel_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                logger.warning("[DIFF ENGINE] Skipping out-of-workspace path: %s", rel_path)
                continue
            if candidate.exists() and candidate.is_file():
                resolved.append((rel_path, candidate))
        return resolved

    def _expand_alias(self, path: str, aliases: Dict[str, str]) -> str:
        for alias, prefix in aliases.items():
            if path.startswith(alias):
                return prefix + path[len(alias) :]
        return path

    def _transform_python_source(
        self,
        source: str,
        operation: str,
        task_id: str,
        description: str,
    ) -> str:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source

        if operation == "bugfix":
            return self._add_try_except_guard(source, tree)
        if operation == "feature":
            return self._append_feature_stub(source, task_id, description)
        if operation == "refactor":
            return self._add_type_hints_and_docstrings(source, tree)
        return source

    def _add_try_except_guard(self, source: str, tree: ast.AST) -> str:
        lines = source.splitlines()
        target = self._first_function(tree)
        if not target or not getattr(target, "body", None):
            return source
        if any(isinstance(stmt, ast.Try) for stmt in target.body):
            return source

        lines = self._ensure_logger(lines)
        try:
            refreshed_source = "\n".join(lines)
            refreshed_tree = ast.parse(refreshed_source)
        except SyntaxError:
            return source

        target = self._first_function(refreshed_tree)
        if not target or not getattr(target, "body", None):
            return source

        body_index = 0
        first_body = target.body[0]
        if (
            isinstance(first_body, ast.Expr)
            and isinstance(getattr(first_body, "value", None), ast.Constant)
            and isinstance(first_body.value.value, str)
        ):
            body_index = 1
        if body_index >= len(target.body):
            return self._with_original_trailing_newline("\n".join(lines), source)

        first_stmt = target.body[body_index]
        start = first_stmt.lineno - 1
        end = target.end_lineno or first_stmt.end_lineno or first_stmt.lineno
        body_indent = len(lines[start]) - len(lines[start].lstrip(" "))
        try_indent = " " * body_indent
        child_indent = " " * (body_indent + 4)

        guarded = [f"{try_indent}try:"]
        guarded.extend(f"{child_indent}{line}" if line.strip() else line for line in lines[start:end])
        guarded.extend(
            [
                f"{try_indent}except Exception as exc:",
                f"{child_indent}logger.error(\"BBC-AOS guarded execution failed: %s\", exc)",
                f"{child_indent}raise",
            ]
        )
        new_lines = lines[:start] + guarded + lines[end:]
        return self._with_original_trailing_newline("\n".join(new_lines), source)

    def _append_feature_stub(self, source: str, task_id: str, description: str) -> str:
        lines = self._ensure_import(source.splitlines(), "from typing import Any")
        safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", description.lower()).strip("_")
        safe_name = safe_name[:32] or task_id
        function_name = f"bbc_feature_{safe_name}"

        try:
            existing_tree = ast.parse("\n".join(lines))
        except SyntaxError:
            return source
        existing_names = {
            node.name for node in ast.walk(existing_tree) if isinstance(node, ast.FunctionDef)
        }
        if function_name in existing_names:
            return source

        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(
            [
                "",
                f"def {function_name}(payload: Any = None) -> Any:",
                f"    \"\"\"BBC-AOS generated feature stub for {task_id}.\"\"\"",
                "    return payload",
            ]
        )
        return "\n".join(lines) + "\n"

    def _add_type_hints_and_docstrings(self, source: str, tree: ast.AST) -> str:
        lines = source.splitlines()
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for node in sorted(functions, key=lambda n: n.lineno, reverse=True):
            def_idx = node.lineno - 1
            def_line = lines[def_idx]
            if node.returns is None and def_line.rstrip().endswith(":") and "->" not in def_line:
                lines[def_idx] = def_line.rstrip()[:-1] + " -> None:"
            if ast.get_docstring(node) is None:
                indent = " " * (node.col_offset + 4)
                lines.insert(def_idx + 1, f'{indent}"""BBC-AOS reviewed function."""')
        return self._with_original_trailing_newline("\n".join(lines), source)

    def _first_function(self, tree: ast.AST) -> Optional[ast.AST]:
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        return min(functions, key=lambda n: n.lineno) if functions else None

    def _ensure_import(self, lines: List[str], import_line: str) -> List[str]:
        if import_line in lines:
            return lines
        insert_at = 0
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = idx + 1
            elif stripped and not stripped.startswith("#") and insert_at:
                break
        return lines[:insert_at] + [import_line] + lines[insert_at:]

    def _ensure_logger(self, lines: List[str]) -> List[str]:
        lines = self._ensure_import(lines, "import logging")
        if any("logging.getLogger" in line and "logger" in line for line in lines):
            return lines
        insert_at = 0
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = idx + 1
        return lines[:insert_at] + ["logger = logging.getLogger(__name__)"] + lines[insert_at:]

    def _with_original_trailing_newline(self, text: str, original: str) -> str:
        return text + ("\n" if original.endswith("\n") else "")

    def _build_review_result(self, task_id: str, files: List[str], reason: str) -> Dict[str, Any]:
        patch_lines = [
            f"# Review analysis for task: {task_id}",
            f"# Reason: {reason}",
            f"# Files in scope: {len(files)}",
        ]
        for file_path in files:
            patch_lines.append(f"# INSPECT: {file_path}")
        return self._build_result([], [], [], "\n".join(patch_lines), "review")

    def _build_test_result(self, task_id: str, files: List[Tuple[str, Path]]) -> Dict[str, Any]:
        """Builds a deterministic pytest stub for the first in-scope module."""
        source_rel = files[0][0]
        stem = Path(source_rel).stem
        safe_stem = re.sub(r"[^a-zA-Z0-9_]+", "_", stem).strip("_") or "module"
        test_path = f"tests/test_{safe_stem}.py"
        module_hint = source_rel.replace("/", ".").removesuffix(".py")
        content = [
            '"""BBC-AOS generated regression tests."""',
            "",
            f"def test_{safe_stem}_import_contract() -> None:",
            f"    __import__({module_hint!r})",
        ]
        diff_lines = [
            "--- /dev/null",
            f"+++ b/{test_path}",
            f"@@ -0,0 +1,{len(content)} @@",
        ]
        diff_lines.extend(f"+{line}" for line in content)
        return self._build_result([], [test_path], [], "\n".join(diff_lines), "test")

    def _build_result(
        self,
        modified_files: List[str],
        added_files: List[str],
        removed_files: List[str],
        patch: str,
        operation: str,
    ) -> Dict[str, Any]:
        return {
            "modified_files": sorted(set(modified_files)),
            "added_files": sorted(set(added_files)),
            "removed_files": sorted(set(removed_files)),
            "patch": patch,
            "operation": operation,
        }


class CoderAgent(BaseAgent):
    """Generates deterministic CodeDiff payloads inside the provided blast radius."""

    AGENT_ID: str = "coder_agent"
    AGENT_VERSION: str = "1.0.0"
    SUPPORTED_ACTIONS: List[str] = ["generate_diff", "plan_modification", "plan_refactor"]

    def __init__(self) -> None:
        self._diff_engine = _DeterministicDiffEngine()

    def initialize(self) -> None:
        logger.info("[CODER AGENT] Initializing CoderAgent v%s.", self.AGENT_VERSION)

    def validate_input(self, params: Dict[str, Any]) -> bool:
        if not params or not isinstance(params, dict):
            return False

        context = params.get("context", {})
        if not isinstance(context, dict):
            return False

        task = context.get("task")
        if not isinstance(task, dict):
            return False
        if "task_id" not in task or "description" not in task:
            return False

        packed_context = context.get("packed_context")
        if not isinstance(packed_context, dict):
            return False

        selected_files = context.get("selected_files")
        if not isinstance(selected_files, list):
            return False

        metadata = params.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        if "trace_id" not in metadata or "replay_id" not in metadata:
            return False

        return True

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        context = params["context"]
        metadata = params["metadata"]

        task = context["task"]
        task_id: str = task["task_id"]
        description: str = task["description"]
        task_deps: List[str] = task.get("dependencies", [])

        packed_context: Dict[str, Any] = context["packed_context"]
        selected_files: List[str] = context["selected_files"]
        workspace_root = context.get("workspace_root") or packed_context.get("project_skeleton", {}).get("root", ".")

        trace_id: str = metadata["trace_id"]
        replay_id: str = metadata["replay_id"]

        logger.info(
            "[CODER AGENT] Generating code diff for task '%s': '%s'. Blast radius: %d files.",
            task_id,
            description,
            len(selected_files),
        )

        from bbc_aos.security.prompt_firewall import PromptFirewall

        firewall_result = PromptFirewall().scan(description, source="task_description")
        if firewall_result.blocked:
            raise ValueError(
                "Prompt injection detected in task description: "
                + ", ".join(firewall_result.detected_patterns)
            )

        if len(selected_files) > 50:
            logger.warning("[CODER AGENT] selected_files (%d) exceeds limit 50; truncating.", len(selected_files))
            selected_files = selected_files[:50]

        if len(task_deps) > 5:
            logger.warning("[CODER AGENT] task dependencies (%d) exceeds depth limit 5.", len(task_deps))

        diff_result = self._diff_engine.generate(
            task_id=task_id,
            description=description,
            selected_files=selected_files,
            packed_context=packed_context,
            trace_id=trace_id,
            workspace_root=workspace_root,
        )

        diff_payload_str = json.dumps(diff_result, sort_keys=True)
        hash_input = f"{task_id}_{trace_id}_{diff_payload_str}"
        deterministic_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        code_diff = CodeDiff(
            modified_files=diff_result["modified_files"],
            added_files=diff_result["added_files"],
            removed_files=diff_result["removed_files"],
            patch=diff_result["patch"],
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
        )
        result = code_diff.to_dict()

        from bbc_aos.integration.validation_gateway import ValidationGateway

        gateway = ValidationGateway()
        gateway.validate_output(self.AGENT_ID, result)

        from bbc_aos.integration.integration_audit_log import IntegrationAuditEvent, IntegrationAuditLog

        audit_log = context.get("integration_log") or IntegrationAuditLog()
        event = IntegrationAuditEvent(
            event_id=f"coder_{trace_id}",
            event_type="code_diff_generated",
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            details={
                "task_id": task_id,
                "operation": diff_result["operation"],
                "modified_count": len(code_diff.modified_files),
                "added_count": len(code_diff.added_files),
                "removed_count": len(code_diff.removed_files),
                "blast_radius_files": len(selected_files),
            },
        )
        audit_log.append(event)

        return result

    def validate_output(self, result: Dict[str, Any]) -> bool:
        if not result or not isinstance(result, dict):
            return False

        required_fields = [
            "modified_files",
            "added_files",
            "removed_files",
            "patch",
            "trace_id",
            "replay_id",
            "deterministic_hash",
        ]
        if not all(field in result for field in required_fields):
            logger.error("[CODER AGENT ERROR] Output missing required fields.")
            return False

        for list_field in ("modified_files", "added_files", "removed_files"):
            if not isinstance(result[list_field], list):
                logger.error("[CODER AGENT ERROR] Field '%s' is not a list.", list_field)
                return False

        total_files = (
            len(result["modified_files"])
            + len(result["added_files"])
            + len(result["removed_files"])
        )
        if total_files > _DeterministicDiffEngine.MAX_DIFF_FILES:
            logger.error(
                "[CODER AGENT ERROR] Total diff files (%d) exceeds MAX_DIFF_FILES (%d).",
                total_files,
                _DeterministicDiffEngine.MAX_DIFF_FILES,
            )
            return False

        for str_field in ("patch", "trace_id", "replay_id", "deterministic_hash"):
            if not isinstance(result[str_field], str):
                logger.error("[CODER AGENT ERROR] Field '%s' is not a string.", str_field)
                return False

        if len(result["deterministic_hash"]) != 64:
            logger.error("[CODER AGENT ERROR] deterministic_hash is not valid SHA-256.")
            return False

        return True

    def finalize(self) -> None:
        logger.info("[CODER AGENT] Finalizing CoderAgent.")
