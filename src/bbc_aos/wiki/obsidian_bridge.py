"""Obsidian desktop integration helpers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


def ensure_workspace_vault_visible_in_obsidian(
    workspace_vault: str | Path,
    appdata_root: str | Path | None = None,
) -> dict[str, Any]:
    """Register the workspace vault and expose it inside existing Obsidian vaults."""

    vault = Path(workspace_vault).expanduser().resolve()
    _ensure_vault_metadata(vault)
    config_path = _obsidian_config_path(appdata_root)
    visible_links: list[str] = []
    conflicts: list[str] = []
    result: dict[str, Any] = {
        "obsidian_config": str(config_path),
        "workspace_vault": str(vault),
        "registered": False,
        "visible_links": visible_links,
        "conflicts": conflicts,
        "config_error": "",
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = _load_obsidian_config(config_path)
    vaults = data.setdefault("vaults", {})
    if not isinstance(vaults, dict):
        vaults = {}
        data["vaults"] = vaults

    configured_paths = _configured_vault_paths(vaults)
    fallback_vault = Path(os.environ.get("USERPROFILE", "")) / "Documents" / "Obsidian Vault"
    if fallback_vault.exists() and fallback_vault.resolve() not in configured_paths:
        configured_paths.append(fallback_vault.resolve())
    for configured in configured_paths:
        if configured == vault or not configured.exists():
            continue
        link_result = _ensure_visible_link(configured, vault)
        if link_result["status"] == "linked":
            visible_links.append(str(link_result["path"]))
        elif link_result["status"] == "conflict":
            conflicts.append(str(link_result["path"]))

    vault_id = _vault_id(vault)
    vaults[vault_id] = {
        "path": str(vault),
        "ts": 0,
        "open": True,
    }
    result["registered"] = True
    try:
        config_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except Exception as exc:
        result["registered"] = False
        result["config_error"] = str(exc)
    return result


def _obsidian_config_path(appdata_root: str | Path | None = None) -> Path:
    root = Path(appdata_root) if appdata_root else Path(os.environ.get("APPDATA", "")) / "obsidian"
    return root / "obsidian.json"


def _load_obsidian_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {"vaults": {}}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {"vaults": {}}
    return data if isinstance(data, dict) else {"vaults": {}}


def _configured_vault_paths(vaults: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for raw in vaults.values():
        if not isinstance(raw, dict):
            continue
        path = raw.get("path")
        if isinstance(path, str) and path:
            paths.append(Path(path).expanduser().resolve())
    return paths


def _ensure_vault_metadata(vault: Path) -> None:
    obsidian_dir = vault / ".obsidian"
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    app_json = obsidian_dir / "app.json"
    if not app_json.exists():
        app_json.write_text(
            json.dumps(
                {
                    "alwaysUpdateLinks": True,
                    "newFileLocation": "root",
                    "attachmentFolderPath": "Attachments",
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def _ensure_visible_link(open_vault: Path, workspace_vault: Path) -> dict[str, object]:
    link_path = open_vault / "BBC_KNOWLEDGE"
    if link_path.exists():
        try:
            if link_path.resolve() == workspace_vault:
                return {"status": "linked", "path": link_path}
        except Exception:
            pass
        return {"status": "conflict", "path": link_path}
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(workspace_vault)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return {"status": "conflict", "path": link_path}
    else:
        link_path.symlink_to(workspace_vault, target_is_directory=True)
    return {"status": "linked", "path": link_path}


def _vault_id(vault: Path) -> str:
    digest = hashlib.sha256(str(vault).encode("utf-8")).hexdigest()[:16]
    return f"bbc_{digest}"
