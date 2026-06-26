"""Hallucination checks for BBC-AOS patch proposals."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set


class HallucinationDetector:
    """Detects references to files, imports, or symbols that are not in the project."""

    def validate_patch(
        self,
        patch: str,
        workspace_root: str,
        known_files: Iterable[str],
        known_symbols: Iterable[str] = (),
    ) -> Dict[str, object]:
        root = Path(workspace_root or ".").resolve()
        known_file_set = {self._norm(p) for p in known_files}
        known_symbol_set = set(known_symbols)
        violations: List[str] = []

        for path in self._files_from_patch(patch):
            rel = self._norm(path)
            if not Path(rel).suffix:
                continue
            if rel.startswith("tests/test_"):
                continue
            if rel not in known_file_set and not (root / rel).exists():
                violations.append(f"Patch references unknown file: {rel}")

        for module_name in self._imports_from_patch(patch):
            if not self._module_exists(module_name, root):
                violations.append(f"Patch imports unknown module: {module_name}")

        if known_symbol_set:
            for symbol in self._symbol_references_from_patch(patch):
                if symbol not in known_symbol_set and symbol[:1].isupper():
                    violations.append(f"Patch references unknown symbol: {symbol}")

        return {
            "allowed": not violations,
            "violations": sorted(set(violations)),
        }

    def _files_from_patch(self, patch: str) -> Set[str]:
        files: Set[str] = set()
        for line in patch.splitlines():
            if line.startswith(("--- ", "+++ ")):
                path = line[4:].strip()
                if path != "/dev/null":
                    files.add(path[2:] if path.startswith(("a/", "b/")) else path)
        return files

    def _imports_from_patch(self, patch: str) -> Set[str]:
        imports: Set[str] = set()
        added_lines = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        try:
            tree = ast.parse(added_lines or "\n")
        except SyntaxError:
            return imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        return imports

    def _symbol_references_from_patch(self, patch: str) -> Set[str]:
        refs: Set[str] = set()
        for line in patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                refs.update(re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", line))
        return refs

    def _module_exists(self, module_name: str, root: Path) -> bool:
        first = module_name.split(".")[0]
        if first in {"os", "sys", "json", "logging", "typing", "pathlib", "re", "ast"}:
            return True
        rel = Path(*module_name.split("."))
        return (root / f"{rel}.py").exists() or (root / rel / "__init__.py").exists()

    def _norm(self, path: str) -> str:
        return str(path).replace("\\", "/").lstrip("./")
