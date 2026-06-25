"""BBC Knowledge Vault compiler, search, and health checks."""

import os
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List


class WikiCompiler:
    """Compiles markdown vault indexes and lightweight semantic search results."""

    NOTE_DIRS = ["Executions", "Failures", "Decisions", "Lessons_Learned", "Architecture", "Entities", "Concepts"]

    def __init__(self, vault_root: str = "") -> None:
        self.vault_root = Path(vault_root or os.path.expanduser("~/BBC_KNOWLEDGE"))

    def ensure_project(self, project_id: str) -> Path:
        project = self.vault_root / "Projects" / project_id
        for note_dir in self.NOTE_DIRS:
            (project / note_dir).mkdir(parents=True, exist_ok=True)
        return project

    def compile_index(self, project_id: str) -> Path:
        project = self.ensure_project(project_id)
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
            lines.append(f"- {time.strftime('%Y-%m-%d', time.localtime(note.stat().st_mtime))}: [[{note.stem}]]")
        output = project / "00_INDEX.md"
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
        return {
            "vault_healthy": root.exists(),
            "counts": counts,
            "broken_links": broken_links,
            "orphan_notes": orphan_notes,
            "last_sync": self._last_sync(root),
        }

    def _link_health(self, root: Path) -> tuple[int, int]:
        notes = list(root.rglob("*.md"))
        stems = {note.stem for note in notes}
        linked = set()
        broken = 0
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="ignore")
            for raw in re.findall(r"\[\[([^\]|]+)", text):
                target = Path(raw).stem
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
