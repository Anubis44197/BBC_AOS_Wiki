"""Wiki reflection note generation."""

import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from bbc_aos.wiki.backlink_builder import BacklinkBuilder


class ReflectionGenerator:
    """Writes reflection notes into Lessons_Learned."""

    def __init__(self) -> None:
        self.links = BacklinkBuilder()

    def filename(self, goal: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", goal.lower()).strip("_")[:48] or "reflection"
        return f"{time.strftime('%Y-%m-%d')}_{slug}.md"

    def generate(
        self,
        goal: str,
        reflection: Dict[str, Any],
        affected_files: Iterable[str] = (),
        replay_id: str = "",
    ) -> str:
        links = [self.links.wikilink(goal)]
        links.extend(self.links.wikilink(str(f)) for f in affected_files)
        if reflection.get("failure_patterns"):
            links.append(self.links.wikilink("verification_failure"))
        return "\n".join(
            [
                f"# Reflection: {goal}",
                f"- Outcome: {'reusable' if reflection.get('reusable') else 'single-use'}",
                f"- Risk: {', '.join(reflection.get('future_risks', [])) or 'LOW'}",
                f"- Failure Pattern: {', '.join(reflection.get('failure_patterns', [])) or 'None'}",
                f"- Recommendation: {'; '.join(reflection.get('recommendations', [])) or 'None'}",
                f"- Reusable: {bool(reflection.get('reusable'))}",
                f"- Replay ID: {replay_id}",
                "",
                "## Backlinks",
                "\n".join(f"- {link}" for link in links),
                "",
            ]
        )

    def write(
        self,
        project_root: Path,
        goal: str,
        reflection: Dict[str, Any],
        affected_files: Iterable[str] = (),
        replay_id: str = "",
    ) -> Path:
        lessons = project_root / "Lessons_Learned"
        lessons.mkdir(parents=True, exist_ok=True)
        path = lessons / self.filename(goal)
        path.write_text(self.generate(goal, reflection, affected_files, replay_id), encoding="utf-8")
        return path
