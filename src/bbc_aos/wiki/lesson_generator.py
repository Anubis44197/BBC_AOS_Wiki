"""Lesson note generation for BBC Knowledge Vault."""

import time
from typing import Any, Dict

from bbc_aos.wiki.backlink_builder import BacklinkBuilder


class LessonGenerator:
    """Creates Lesson Learned markdown notes from execution summaries."""

    def __init__(self) -> None:
        self.links = BacklinkBuilder()

    def generate(self, execution: Dict[str, Any]) -> str:
        goal = execution.get("goal") or execution.get("goal_description") or "BBC execution"
        risk = execution.get("risk_level", "LOW")
        files = execution.get("files", []) or execution.get("affected_files", [])
        operation = execution.get("operation", "review")
        date = execution.get("date") or time.strftime("%Y-%m-%d")
        file_lines = "\n".join(f"- {self.links.wikilink(str(f))}" for f in files) or "- None"
        return "\n".join(
            [
                f"# Lesson: {goal} ({date})",
                f"- Risk: {risk}",
                f"- Pattern: {operation}",
                "- Files:",
                file_lines,
                "- Next time: Check existing imports and blast radius before patching.",
                "",
            ]
        )
