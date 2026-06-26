"""Strict hallucination and write-authorization guard."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from bbc_aos.security.hallucination_detector import HallucinationDetector


class HallucinationGuard:
    """Rejects unknown entities and unauthorized writes before execution."""

    def validate_execution(
        self,
        patch: str,
        workspace_root: str,
        changed_files: Iterable[str],
        selected_files: Iterable[str],
        approved_files: Iterable[str] = (),
        known_symbols: Iterable[str] = (),
    ) -> dict[str, object]:
        root = Path(workspace_root or ".").resolve()
        selected = {self._norm(path) for path in selected_files}
        approved = {self._norm(path) for path in approved_files}
        changed = {self._norm(path) for path in changed_files}
        violations: list[str] = []

        for rel_path in sorted(changed):
            target = (root / rel_path).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                violations.append(f"Unauthorized write outside workspace: {rel_path}")
                continue
            if rel_path not in selected and rel_path not in approved:
                violations.append(f"Unauthorized write outside selected_files: {rel_path}")
            if not target.exists() and rel_path not in selected and rel_path not in approved:
                violations.append(f"Implicit file creation is not approved: {rel_path}")

        detector_result = HallucinationDetector().validate_patch(
            patch=patch,
            workspace_root=str(root),
            known_files=sorted(selected | approved | changed),
            known_symbols=known_symbols,
        )
        detector_violations = detector_result.get("violations", [])
        if isinstance(detector_violations, list):
            violations.extend(str(v) for v in detector_violations)
        return {
            "allowed": not violations,
            "violations": sorted(set(violations)),
        }

    def _norm(self, path: str) -> str:
        return str(path).replace("\\", "/").lstrip("./")
