"""Entity note generation for BBC Knowledge Vault."""

import time
from pathlib import Path
from typing import Any, Dict, Iterable

from bbc_aos.wiki.backlink_builder import BacklinkBuilder


class EntityGenerator:
    """Creates one entity note per affected file."""

    def __init__(self) -> None:
        self.links = BacklinkBuilder()

    def generate(self, file_path: str, execution: Dict[str, Any], related: Iterable[str] = ()) -> str:
        date = execution.get("date") or time.strftime("%Y-%m-%d")
        operation = execution.get("operation", "review")
        asks = execution.get("bbc_asks", 1)
        related_links = self.links.related_block(related) or "- None"
        return "\n".join(
            [
                f"# Entity: {file_path}",
                f"- Last BBC modification: {date}",
                f"- Modification type: {operation}",
                f"- BBC asks: {asks}",
                "- Related entities:",
                related_links,
                f"- Filename: {Path(file_path).name}",
                "",
            ]
        )
