"""Obsidian configuration helpers for BBC Knowledge Vault."""

import json
from pathlib import Path
from typing import Dict


class ObsidianSync:
    """Manages local `.obsidian` settings without configuring GitHub sync."""

    def __init__(self, vault_root: str) -> None:
        self.vault_root = Path(vault_root)
        self.obsidian_dir = self.vault_root / ".obsidian"

    def ensure_config(self) -> Dict[str, str]:
        self.obsidian_dir.mkdir(parents=True, exist_ok=True)
        app_json = self.obsidian_dir / "app.json"
        data = {"promptDelete": False, "alwaysUpdateLinks": True}
        if app_json.exists():
            try:
                existing = json.loads(app_json.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    data.update(existing)
            except Exception:
                pass
        app_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"status": "configured", "path": str(app_json)}
