"""
Central scan profile for BBC project analysis.

The profile keeps generated, dependency, cache, media, and oversized files out
of expensive analysis passes. It also supports a lightweight `.bbcignore` file
for project-specific exclusions.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Iterable, Iterator, Optional


SOURCE_EXTENSIONS = (
    ".py",
    ".md",
    ".json",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".sql",
    ".rs",
    ".go",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
)

EXCLUDED_DIRS = {
    ".bbc",
    ".cache",
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".old",
    ".parcel-cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".turbo",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "generated",
    "node_modules",
    "out",
    "target",
    "tmp",
    "venv",
    "vendor",
}

EXCLUDED_FILENAMES = {
    "bun.lockb",
    "cargo.lock",
    "composer.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}

EXCLUDED_SUFFIXES = (
    ".7z",
    ".avif",
    ".bmp",
    ".db",
    ".dll",
    ".dylib",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".lock",
    ".log",
    ".mp3",
    ".mp4",
    ".onnx",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".tgz",
    ".ttf",
    ".wasm",
    ".webm",
    ".webp",
    ".whl",
    ".woff",
    ".woff2",
    ".zip",
)

DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024


def load_bbcignore(project_root: str | Path) -> list[str]:
    """Load simple glob patterns from `.bbcignore`."""
    ignore_path = Path(project_root) / ".bbcignore"
    if not ignore_path.exists():
        return []
    patterns: list[str] = []
    try:
        for line in ignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped.replace("\\", "/"))
    except OSError:
        return []
    return patterns


def normalize_rel(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip("/")


def should_skip_dir_name(name: str) -> bool:
    lower = name.lower()
    if lower in EXCLUDED_DIRS:
        return True
    if lower.startswith(".pytest-tmp"):
        return True
    if lower.endswith(".egg-info"):
        return True
    return False


def _matches_ignore(rel_path: str, patterns: Iterable[str]) -> bool:
    rel = normalize_rel(rel_path)
    for raw in patterns:
        raw_pattern = str(raw).replace("\\", "/").strip()
        pattern = normalize_rel(raw_pattern)
        if not pattern:
            continue
        if raw_pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern):
            return True
    return False


def should_skip_file(
    path: str | Path,
    project_root: str | Path,
    ignore_patterns: Iterable[str] = (),
    output_file_abs: Optional[str] = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> bool:
    p = Path(path)
    if output_file_abs and os.path.abspath(str(p)) == os.path.abspath(output_file_abs):
        return True
    if p.name.lower() in EXCLUDED_FILENAMES:
        return True
    if p.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    try:
        rel = normalize_rel(p.resolve().relative_to(Path(project_root).resolve()))
    except Exception:
        rel = normalize_rel(p.name)
    if _matches_ignore(rel, ignore_patterns):
        return True
    try:
        if p.stat().st_size > max_file_bytes:
            return True
    except OSError:
        return True
    return False


def iter_source_files(
    project_root: str | Path,
    extensions: Iterable[str] = SOURCE_EXTENSIONS,
    max_files: Optional[int] = None,
    output_file_abs: Optional[str] = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> Iterator[Path]:
    """Yield source files according to BBC's large-repo scan profile."""
    root_path = Path(project_root)
    exts = {ext.lower() for ext in extensions}
    ignore_patterns = load_bbcignore(root_path)
    yielded = 0

    for root, dirs, files in os.walk(str(root_path)):
        dirs[:] = sorted(d for d in dirs if not should_skip_dir_name(d))
        for fname in sorted(files):
            if max_files is not None and yielded >= max_files:
                return
            path = Path(root) / fname
            if path.suffix.lower() not in exts:
                continue
            if should_skip_file(path, root_path, ignore_patterns, output_file_abs, max_file_bytes):
                continue
            yielded += 1
            yield path
