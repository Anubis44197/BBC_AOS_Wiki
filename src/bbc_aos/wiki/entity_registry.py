"""Append-only canonical entity registry for BBC Knowledge Vault."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXTENSION_PATTERN = re.compile(r"\.(?:py|pyi|js|jsx|ts|tsx|md|json|yaml|yml|toml|txt|html|css|scss|pdf)$", re.IGNORECASE)


def normalize_entity_name(value: str) -> str:
    """Normalize paths, titles, and labels to one canonical Obsidian entity id."""
    raw = (value or "").strip()
    raw = raw.split("|", 1)[0].split("#", 1)[0]
    raw = raw.replace("\\", "/")
    raw = EXTENSION_PATTERN.sub("", raw)
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw.lower()).strip("_")
    parts: list[str] = []
    seen: set[str] = set()
    for part in raw.split("_"):
        if not part or part in seen:
            continue
        seen.add(part)
        parts.append(part)
    return "_".join(parts) or "entity"


class EntityRegistry:
    """Maintains an append-only map from canonical entity ids to note paths."""

    def __init__(self, project_root: Path, runtime_root: Path | None = None) -> None:
        self.project_root = project_root
        self.runtime_root = runtime_root or Path.cwd()
        self.registry_path = self.runtime_root / ".bbc" / "wiki" / "entity_registry.json"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.entities_dir = self.project_root / "Entities"
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self._entries = self._load()

    def register(self, raw_name: str, source_note: str = "") -> str:
        canonical = normalize_entity_name(raw_name)
        if canonical not in self._entries:
            self._entries[canonical] = f"Entities/{canonical}.md"
            self._write()
        self.ensure_note(canonical, source_note)
        return canonical

    def resolve(self, raw_name: str) -> str:
        return self.register(raw_name)

    def ensure_note(self, canonical: str, source_note: str = "") -> Path:
        path = self.project_root / self._entries.get(canonical, f"Entities/{canonical}.md")
        if path.exists() and path.read_text(encoding="utf-8", errors="ignore").strip():
            return path
        lines = [
            f"# Entity: {canonical}",
            f"- Canonical name: {canonical}",
            f"- Source: {source_note or 'auto-created'}",
            "- Related:",
            f"- [[{canonical}]]",
            "",
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def entries(self) -> dict[str, str]:
        return dict(self._entries)

    def _load(self) -> dict[str, str]:
        if not self.registry_path.exists():
            return {}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}

    def _write(self) -> None:
        self.registry_path.write_text(json.dumps(self._entries, indent=2, sort_keys=True), encoding="utf-8")
