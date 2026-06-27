"""Workspace and blast-radius permission checks for BBC-AOS."""

from pathlib import Path
from typing import Dict, Iterable, List


class PermissionEngine:
    """Blocks writes outside workspace, outside blast radius, or to disallowed suffixes."""

    ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".yaml", ".yml", ".toml"}

    def validate_change_set(
        self,
        changed_files: Iterable[str],
        workspace_root: str,
        blast_radius: Iterable[str],
        allow_new_tests: bool = True,
    ) -> Dict[str, object]:
        root = Path(workspace_root or ".").resolve()
        allowed = {self._norm(p) for p in blast_radius}
        violations: List[str] = []

        for raw_path in changed_files:
            rel_path = self._norm(raw_path)
            target = (root / rel_path).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                violations.append(f"{rel_path}: outside workspace root")
                continue

            suffix = target.suffix.lower()
            if suffix not in self.ALLOWED_EXTENSIONS:
                violations.append(f"{rel_path}: extension '{suffix}' is not allowed")

            is_allowed_new_test = allow_new_tests and rel_path.startswith("tests/test_") and suffix == ".py"
            if rel_path not in allowed and not is_allowed_new_test:
                violations.append(f"{rel_path}: outside approved blast radius")

        return {
            "allowed": not violations,
            "violations": violations,
        }

    def _norm(self, path: str) -> str:
        return str(path).replace("\\", "/").lstrip("./")
