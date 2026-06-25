"""Concept note generation for BBC Knowledge Vault."""

import re
import time
from typing import Any, Dict, Iterable

from bbc_aos.wiki.backlink_builder import BacklinkBuilder


class ConceptGenerator:
    """Creates task-concept markdown from goal text and related files."""

    def __init__(self) -> None:
        self.links = BacklinkBuilder()

    def concept_name(self, goal: str) -> str:
        words = [w for w in re.findall(r"[A-Za-z0-9]+", goal) if len(w) > 2]
        return " ".join(words[:4]).title() or "BBC Concept"

    def generate(self, goal: str, files: Iterable[str], execution: Dict[str, Any]) -> str:
        concept = self.concept_name(goal)
        date = execution.get("date") or time.strftime("%Y-%m-%d")
        file_links = self.links.related_block(files) or "- None"
        return "\n".join(
            [
                f"# Concept: {concept}",
                f"- First seen: {date}",
                "- Related files:",
                file_links,
                "- Pattern: Request -> Blast Radius -> Patch -> Verify",
                "",
            ]
        )
