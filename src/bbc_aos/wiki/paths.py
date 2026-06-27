"""Canonical BBC Knowledge Vault path resolution."""

from __future__ import annotations

from pathlib import Path


def resolve_workspace_vault(
    workspace_root: str | Path = ".",
    requested_vault_path: str | Path | None = None,
) -> Path:
    """Return the only valid vault path for a workspace.

    BBC-AOS must never write knowledge artifacts to the installed package,
    source repository, user home, or a temporary directory by default. The
    canonical vault is always workspace_root/BBC_KNOWLEDGE.
    """

    root = Path(workspace_root).expanduser().resolve()
    canonical = (root / "BBC_KNOWLEDGE").resolve()
    candidate = canonical
    if requested_vault_path:
        candidate = Path(requested_vault_path).expanduser().resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Vault path must stay inside workspace root: {candidate}") from exc
    if candidate != canonical:
        raise ValueError(f"Vault path must be workspace_root/BBC_KNOWLEDGE: {candidate}")
    return canonical
