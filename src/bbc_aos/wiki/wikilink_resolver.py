"""Canonical Obsidian wikilink resolver."""

from __future__ import annotations

import re
from pathlib import Path

from bbc_aos.wiki.entity_registry import EntityRegistry, normalize_entity_name


WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


class WikilinkResolver:
    """Repairs wikilinks through the entity registry and creates missing entities."""

    def __init__(self, registry: EntityRegistry) -> None:
        self.registry = registry

    def repair_project(self) -> dict[str, int]:
        repaired = 0
        created_before = len(self.registry.entries())
        for note in self.registry.project_root.rglob("*.md"):
            if ".obsidian" in note.parts:
                continue
            original = note.read_text(encoding="utf-8", errors="ignore")
            updated = self.repair_text(original, note)
            if updated != original:
                note.write_text(updated, encoding="utf-8")
                repaired += 1
        for raw in self._broken_links():
            self.registry.register(raw, "wikilink repair")
        for note in self.registry.project_root.rglob("*.md"):
            if ".obsidian" in note.parts:
                continue
            original = note.read_text(encoding="utf-8", errors="ignore")
            updated = self.repair_text(original, note)
            if updated != original:
                note.write_text(updated, encoding="utf-8")
                repaired += 1
        return {
            "notes_repaired": repaired,
            "entities_created": max(0, len(self.registry.entries()) - created_before),
        }

    def repair_text(self, text: str, source_note: Path) -> str:
        existing_stems = {
            normalize_entity_name(note.stem)
            for note in self.registry.project_root.rglob("*.md")
        }

        def replace(match: re.Match[str]) -> str:
            raw = match.group(1)
            canonical_raw = normalize_entity_name(raw)
            if canonical_raw in existing_stems:
                return f"[[{canonical_raw}]]"
            canonical = self.registry.register(raw, source_note.name)
            return f"[[{canonical}]]"

        return WIKILINK_PATTERN.sub(replace, text)

    def broken_link_count(self) -> int:
        return len(self._broken_links())

    def _broken_links(self) -> list[str]:
        notes = list(self.registry.project_root.rglob("*.md"))
        stems = {normalize_entity_name(note.stem) for note in notes}
        broken: list[str] = []
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="ignore")
            for raw in WIKILINK_PATTERN.findall(text):
                if normalize_entity_name(raw) not in stems:
                    broken.append(raw)
        return sorted(set(broken), key=normalize_entity_name)
