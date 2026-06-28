"""Architectural invariant checks for BBC-AOS."""

import fnmatch
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from bbc_aos.runtime_paths import runtime_file


DEFAULT_INVARIANTS: Dict[str, Any] = {
    "forbidden_paths": [],
    "must_not_modify": [],
    "max_files_per_commit": 25,
    "require_tests": False,
    "require_docstrings": False,
    "forbidden_imports": ["subprocess", "os.system"],
}


class InvariantEngine:
    """Loads `.bbc/invariants.yaml` and validates proposed change sets."""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.path = runtime_file(self.project_root, "invariants.yaml")

    def ensure_config(self) -> Dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(
                "\n".join(
                    [
                        "forbidden_paths: []",
                        "must_not_modify: []",
                        "max_files_per_commit: 25",
                        "require_tests: false",
                        "require_docstrings: false",
                        "forbidden_imports:",
                        "  - subprocess",
                        "  - os.system",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        return self.load()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_INVARIANTS)
        return self._parse_simple_yaml(self.path.read_text(encoding="utf-8", errors="ignore"))

    def validate(
        self,
        changed_files: Iterable[str],
        patch: str,
        validation_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        invariants = self.load()
        files = [str(f).replace("\\", "/").lstrip("./") for f in changed_files]
        violations: List[str] = []

        max_files = int(invariants.get("max_files_per_commit", 25) or 25)
        if len(files) > max_files:
            violations.append(f"max_files_per_commit exceeded: {len(files)} > {max_files}")

        for pattern in invariants.get("forbidden_paths", []):
            for file_path in files:
                if fnmatch.fnmatch(file_path, pattern):
                    violations.append(f"forbidden path modified: {file_path}")

        for pattern in invariants.get("must_not_modify", []):
            for file_path in files:
                if fnmatch.fnmatch(file_path, pattern) or Path(file_path).name == pattern:
                    violations.append(f"must_not_modify path changed: {file_path}")

        if invariants.get("require_tests"):
            plan = validation_plan or {}
            test_tasks = [t for t in plan.get("validation_tasks", []) if t.get("test_type") in ("unit", "regression")]
            has_test_file = any(file_path.startswith("tests/") for file_path in files)
            if not test_tasks and not has_test_file:
                violations.append("require_tests invariant not satisfied")

        if invariants.get("require_docstrings") and "+def " in patch:
            added_docstrings = re.findall(r'^\+\s+"""', patch, re.MULTILINE)
            if not added_docstrings:
                violations.append("require_docstrings invariant not satisfied")

        for forbidden in invariants.get("forbidden_imports", []):
            if re.search(rf"^\+.*\b{re.escape(forbidden)}\b", patch, re.MULTILINE):
                violations.append(f"forbidden import or call: {forbidden}")

        return {"allowed": not violations, "violations": violations}

    def _parse_simple_yaml(self, text: str) -> Dict[str, Any]:
        data = dict(DEFAULT_INVARIANTS)
        current_key = ""
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- ") and current_key:
                data.setdefault(current_key, [])
                if isinstance(data[current_key], list):
                    data[current_key].append(stripped[2:].strip().strip('"'))
                continue
            if ":" in stripped:
                key, raw_value = stripped.split(":", 1)
                current_key = key.strip()
                value = raw_value.strip()
                if value == "[]":
                    data[current_key] = []
                elif value.lower() in ("true", "false"):
                    data[current_key] = value.lower() == "true"
                elif value.isdigit():
                    data[current_key] = int(value)
                elif value:
                    data[current_key] = value.strip('"')
                else:
                    data[current_key] = []
        return data
