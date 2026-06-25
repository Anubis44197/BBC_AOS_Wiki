"""Obsidian wikilink helpers."""

import re
from typing import Iterable, List


class BacklinkBuilder:
    """Creates stable Obsidian-style wikilinks."""

    def wikilink(self, target: str, label: str = "") -> str:
        safe = self.slug(target)
        return f"[[{safe}|{label}]]" if label else f"[[{safe}]]"

    def related_block(self, targets: Iterable[str]) -> str:
        links: List[str] = [self.wikilink(t) for t in targets if t]
        return "\n".join(f"- {link}" for link in links)

    def slug(self, text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_./ -]+", "", text).strip()
        return cleaned.replace("\\", "/") or "untitled"
