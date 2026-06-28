"""Ghost workspace path resolution for BBC-AOS runtime artifacts."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path


def project_id(project_root: str | Path = ".") -> str:
    """Return a stable, filesystem-safe id for a project root."""

    root = Path(project_root).expanduser().resolve()
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", root.name).strip("._") or "project"
    digest = hashlib.sha256(str(root).lower().encode("utf-8")).hexdigest()[:16]
    return f"{slug}_{digest}"


def workspaces_root() -> Path:
    """Return the base directory for all BBC-AOS ghost workspaces."""

    configured = os.environ.get("BBC_AOS_WORKSPACES", "")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / "BBC_WORKSPACES").resolve()


def workspace_root(project_root: str | Path = ".") -> Path:
    """Return the project-specific BBC-AOS ghost workspace."""

    return workspaces_root() / project_id(project_root)


def runtime_dir(project_root: str | Path = ".") -> Path:
    return workspace_root(project_root) / "runtime"


def logs_dir(project_root: str | Path = ".") -> Path:
    return runtime_dir(project_root) / "logs"


def state_dir(project_root: str | Path = ".") -> Path:
    return runtime_dir(project_root) / "state"


def loop_dir(project_root: str | Path = ".") -> Path:
    return runtime_dir(project_root) / "loop"


def wiki_vault_dir(project_root: str | Path = ".") -> Path:
    return workspace_root(project_root) / "wiki" / "BBC_KNOWLEDGE"


def reports_dir(project_root: str | Path = ".") -> Path:
    return workspace_root(project_root) / "reports"


def runtime_file(project_root: str | Path, *parts: str) -> Path:
    return runtime_dir(project_root).joinpath(*parts)
