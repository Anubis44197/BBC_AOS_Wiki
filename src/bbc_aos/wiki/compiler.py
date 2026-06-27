"""BBC Knowledge Vault compiler, search, and health checks."""

import os
import re
import time
from pathlib import Path
from typing import Dict, List

from bbc_aos.wiki.entity_registry import EntityRegistry, normalize_entity_name
from bbc_aos.wiki.wikilink_resolver import WikilinkResolver


class WikiCompiler:
    """Compiles markdown vault indexes and lightweight semantic search results."""

    NOTE_DIRS = [
        "Executions",
        "Failures",
        "Decisions",
        "Lessons_Learned",
        "Architecture",
        "Entities",
        "Concepts",
        "Timeline",
        "Backlinks",
    ]

    def __init__(self, vault_root: str = "") -> None:
        configured_root = vault_root or os.environ.get("BBC_KNOWLEDGE_DIR", "")
        self.vault_root = Path(configured_root or os.path.expanduser("~/BBC_KNOWLEDGE"))

    def ensure_project(self, project_id: str) -> Path:
        project = self.vault_root / "Projects" / project_id
        for note_dir in self.NOTE_DIRS:
            (project / note_dir).mkdir(parents=True, exist_ok=True)
        return project

    def compile_index(self, project_id: str) -> Path:
        project = self.ensure_project(project_id)
        registry = EntityRegistry(project)
        self.normalize_entities(project)
        self.deduplicate_concepts(project)
        self.remove_duplicate_entity_notes(project)
        self.extract_entities(project, registry)
        resolver = WikilinkResolver(registry)
        resolver.repair_project()
        self.generate_backlinks(project)
        self.generate_timeline(project)
        notes = list(project.rglob("*.md"))
        executions = len(list((project / "Executions").glob("*.md")))
        failures = len(list((project / "Failures").glob("*.md")))
        lines = [
            "# 00_INDEX.md - BBC Knowledge Vault",
            f"Generated: {time.strftime('%Y-%m-%d')}",
            "## Projects",
            f"- [[{project_id}]] - {executions} executions, {failures} failures",
            "## Recent Activity",
        ]
        for note in sorted(notes, key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
            lines.append(f"- {time.strftime('%Y-%m-%d', time.localtime(note.stat().st_mtime))}: [[{registry.register(note.stem, '00_INDEX.md')}]]")
        output = project / "00_INDEX.md"
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        resolver.repair_project()
        self.generate_backlinks(project)
        self.generate_timeline(project)
        return output

    def search(self, query: str, project_id: str = "") -> List[Dict[str, str]]:
        root = self.vault_root / "Projects" / project_id if project_id else self.vault_root
        if not root.exists():
            return []
        terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", query)]
        results: List[Dict[str, str]] = []
        for note in root.rglob("*.md"):
            text = note.read_text(encoding="utf-8", errors="ignore")
            haystack = f"{note.name}\n{text}".lower()
            score = sum(haystack.count(term) for term in terms)
            if score:
                title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else note.stem
                results.append({"title": title, "path": str(note), "score": str(score)})
        return sorted(results, key=lambda r: int(r["score"]), reverse=True)[:10]

    def status(self, project_id: str = "") -> Dict[str, object]:
        root = self.vault_root / "Projects" / project_id if project_id else self.vault_root
        counts = {name: 0 for name in self.NOTE_DIRS}
        if root.exists():
            for name in self.NOTE_DIRS:
                counts[name] = len(list(root.rglob(f"{name}/*.md")))
        broken_links, orphan_notes = self._link_health(root) if root.exists() else (0, 0)
        quality = self.quality_metrics(project_id) if root.exists() else {
            "duplicate_rate": 0.0,
            "orphan_rate": 0.0,
            "backlink_density": 0.0,
            "empty_note_rate": 0.0,
        }
        return {
            "vault_healthy": root.exists(),
            "counts": counts,
            "broken_links": broken_links,
            "orphan_notes": orphan_notes,
            "quality": quality,
            "last_sync": self._last_sync(root),
        }

    def normalize_entities(self, project: Path) -> None:
        entities_dir = project / "Entities"
        if not entities_dir.exists():
            return
        seen: dict[str, Path] = {}
        for note in sorted(entities_dir.glob("*.md")):
            normalized = normalize_entity_name(note.stem)
            target = entities_dir / f"{normalized}.md"
            if normalized in seen:
                self._merge_note(seen[normalized], note)
                note.unlink(missing_ok=True)
                continue
            if note != target and not target.exists():
                note.rename(target)
                note = target
            elif note != target and target.exists():
                self._merge_note(target, note)
                note.unlink(missing_ok=True)
                note = target
            seen[normalized] = note

    def deduplicate_concepts(self, project: Path) -> None:
        concepts_dir = project / "Concepts"
        if not concepts_dir.exists():
            return
        seen: dict[str, Path] = {}
        for note in sorted(concepts_dir.glob("*.md")):
            normalized = normalize_entity_name(note.stem)
            target = concepts_dir / f"{normalized}.md"
            if normalized in seen:
                self._merge_note(seen[normalized], note)
                note.unlink(missing_ok=True)
                continue
            if note != target and not target.exists():
                note.rename(target)
                note = target
            elif note != target and target.exists():
                self._merge_note(target, note)
                note.unlink(missing_ok=True)
                note = target
            seen[normalized] = note

    def generate_backlinks(self, project: Path) -> Path:
        backlinks_dir = project / "Backlinks"
        backlinks_dir.mkdir(parents=True, exist_ok=True)
        notes = [p for p in project.rglob("*.md") if "Backlinks" not in p.parts]
        index: dict[str, list[str]] = {}
        stems = {note.stem: note for note in notes}
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="ignore")
            for raw in re.findall(r"\[\[([^\]|#]+)", text):
                target = Path(raw).stem
                if target in stems:
                    index.setdefault(target, []).append(note.stem)
        lines = ["# Backlinks", ""]
        for target in sorted(stems):
            sources = sorted(set(index.get(target, [])))
            if not sources:
                continue
            lines.append(f"## [[{target}]]")
            lines.extend(f"- [[{source}]]" for source in sources)
            lines.append("")
        output = backlinks_dir / "BACKLINKS.md"
        output.write_text("\n".join(lines), encoding="utf-8")
        return output

    def generate_timeline(self, project: Path) -> Path:
        timeline_dir = project / "Timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        notes = sorted(
            [p for p in project.rglob("*.md") if "Timeline" not in p.parts],
            key=lambda p: p.stat().st_mtime,
        )
        lines = ["# Timeline", ""]
        for note in notes:
            stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(note.stat().st_mtime))
            lines.append(f"- {stamp}: [[{note.stem}]]")
        output = timeline_dir / "TIMELINE.md"
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output

    def extract_entities(self, project: Path, registry: EntityRegistry) -> None:
        source_dirs = [
            project / "Executions",
            project / "Lessons_Learned",
            project / "Concepts",
            project / "Architecture",
            project / "Decisions",
        ]
        candidates: set[str] = set()
        existing_non_entities = {
            normalize_entity_name(note.stem)
            for note in project.rglob("*.md")
            if "Entities" not in note.parts
        }
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
            for note in source_dir.glob("*.md"):
                text = note.read_text(encoding="utf-8", errors="ignore")
                candidates.update(re.findall(r"\b[A-Za-z0-9_./-]+\.(?:py|md|json|toml|yaml|yml)\b", text))
                candidates.update(re.findall(r"\b(?:FastAPI|MCP|OAuth|JWT|Bedesten|KVKK|BDDK|KIK|Yargitay|Danistay|Sayistay|Anayasa|UYAP|ASGI|Redis|Markdown|Obsidian|Replay|Audit|Security|Wiki|Context|Planner|Coder|Tester|Verification)\b", text))
        for candidate in sorted(candidates):
            if normalize_entity_name(candidate) in existing_non_entities:
                continue
            registry.register(candidate, "entity_extraction")

    def remove_duplicate_entity_notes(self, project: Path) -> None:
        entities_dir = project / "Entities"
        if not entities_dir.exists():
            return
        protected = {
            normalize_entity_name(note.stem)
            for note in project.rglob("*.md")
            if "Entities" not in note.parts
        }
        for note in entities_dir.glob("*.md"):
            if normalize_entity_name(note.stem) in protected:
                note.unlink(missing_ok=True)

    def quality_metrics(self, project_id: str = "") -> Dict[str, float]:
        root = self.vault_root / "Projects" / project_id if project_id else self.vault_root
        notes = list(root.rglob("*.md")) if root.exists() else []
        if not notes:
            return {
                "duplicate_rate": 0.0,
                "orphan_rate": 0.0,
                "backlink_density": 0.0,
                "empty_note_rate": 0.0,
            }
        names = [normalize_entity_name(note.stem) for note in notes]
        duplicate_count = len(names) - len(set(names))
        link_count = 0
        linked: set[str] = set()
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="ignore")
            links = re.findall(r"\[\[([^\]|#]+)", text)
            link_count += len(links)
            linked.update(normalize_entity_name(Path(raw).stem) for raw in links)
        empty_count = sum(1 for note in notes if len(note.read_text(encoding="utf-8", errors="ignore").strip()) < 20)
        orphan_count = sum(1 for name in names if name not in linked)
        return {
            "duplicate_rate": round((duplicate_count / max(1, len(notes))) * 100, 2),
            "orphan_rate": round((orphan_count / max(1, len(notes))) * 100, 2),
            "backlink_density": round(link_count / max(1, len(notes)), 2),
            "empty_note_rate": round((empty_count / max(1, len(notes))) * 100, 2),
        }

    def _normalize_name(self, value: str) -> str:
        return normalize_entity_name(value)

    def _merge_note(self, target: Path, duplicate: Path) -> None:
        target_text = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""
        duplicate_text = duplicate.read_text(encoding="utf-8", errors="ignore")
        if duplicate_text and duplicate_text not in target_text:
            target.write_text(target_text.rstrip() + "\n\n## Merged Duplicate\n\n" + duplicate_text.strip() + "\n", encoding="utf-8")

    def _link_health(self, root: Path) -> tuple[int, int]:
        notes = list(root.rglob("*.md"))
        stems = {normalize_entity_name(note.stem) for note in notes}
        linked: set[str] = set()
        broken = 0
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="ignore")
            for raw in re.findall(r"\[\[([^\]|]+)", text):
                target = normalize_entity_name(Path(raw).stem)
                linked.add(target)
                if target not in stems:
                    broken += 1
        orphan = len([note for note in notes if note.stem not in linked and note.name != "00_INDEX.md"])
        return broken, orphan

    def _last_sync(self, root: Path) -> str:
        notes = list(root.rglob("*.md")) if root.exists() else []
        if not notes:
            return "never"
        latest = max(note.stat().st_mtime for note in notes)
        minutes = int((time.time() - latest) / 60)
        return f"{minutes} min ago"
