"""Hallucination checks for BBC-AOS patch proposals."""

import ast
import builtins
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set


class HallucinationDetector:
    """Detects references to files, imports, or symbols that are not in the project."""

    BUILTIN_SYMBOLS = set(dir(builtins)) | {
        "Any",
        "Dict",
        "Iterable",
        "List",
        "Optional",
        "Path",
        "Set",
        "Tuple",
        "True",
        "False",
        "None",
        "self",
        "cls",
    }

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
            symbol_data = self._symbol_references_from_patch(patch)
            known_or_local = known_symbol_set | symbol_data["defined"] | symbol_data["imported"] | self.BUILTIN_SYMBOLS
            for symbol in symbol_data["referenced"]:
                if symbol not in known_or_local:
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

    def _symbol_references_from_patch(self, patch: str) -> Dict[str, Set[str]]:
        added_lines = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        referenced: Set[str] = set()
        defined: Set[str] = set()
        imported: Set[str] = set()
        try:
            tree = ast.parse(added_lines or "\n")
        except SyntaxError:
            for line in added_lines.splitlines():
                referenced.update(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\s*(?=\()", line))
            return {"referenced": referenced, "defined": defined, "imported": imported}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)
                defined.update(arg.arg for arg in node.args.args)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)
            elif isinstance(node, ast.Import):
                imported.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.update(alias.asname or alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    referenced.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    referenced.add(node.func.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced.add(node.id)
        return {"referenced": referenced, "defined": defined, "imported": imported}

    def _module_exists(self, module_name: str, root: Path) -> bool:
        first = module_name.split(".")[0]
        if first in sys.stdlib_module_names:
            return True
        rel = Path(*module_name.split("."))
        return (root / f"{rel}.py").exists() or (root / rel / "__init__.py").exists()

    def _norm(self, path: str) -> str:
        return str(path).replace("\\", "/").lstrip("./")
