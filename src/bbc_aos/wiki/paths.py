"""Canonical BBC Knowledge Vault path resolution."""

from __future__ import annotations

from pathlib import Path

from bbc_aos.runtime_paths import wiki_vault_dir


def resolve_workspace_vault(
    workspace_root: str | Path = ".",
    requested_vault_path: str | Path | None = None,
) -> Path:
    """Return the only valid vault path for a workspace.

    BBC-AOS must never write knowledge artifacts into the target project by
    default. The canonical vault lives in the project-specific ghost workspace.
    """

    root = Path(workspace_root).expanduser().resolve()
    canonical = wiki_vault_dir(root).resolve()
    candidate = canonical
    if requested_vault_path:
        candidate = Path(requested_vault_path).expanduser().resolve()
    if candidate != canonical:
        raise ValueError(f"Vault path must be the BBC ghost workspace vault: {candidate}")
    return canonical
