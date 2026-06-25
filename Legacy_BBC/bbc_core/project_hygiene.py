import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BBC_TRACE_PATHS = [
    ".bbc",
    ".bbc/",
    "bbc_context.json",
    "bbc_rules.md",
    "ai-context.json",
    "BBC_CONTEXT.md",
    "BBC_INSTRUCTIONS.md",
    "BBC_README.md",
    ".cursorrules",
    ".clinerules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
    ".windsurf/bbc_rules.md",
    ".antigravity/rules.md",
    ".continue/config.json",
    ".roo-code/config.json",
    ".zed/settings.json",
    ".idea/bbc-ai-assistant.xml",
    ".fleet/bbc_rules.md",
    ".theia/settings.json",
    ".trae/rules.md",
]

PERSONAL_PATH_MARKERS = [
    "C:/Users/",
    "C:\\Users\\",
    "/Users/",
    "/home/",
]

SCAN_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".bat",
    ".ps1",
}

SKIP_DIRS = {
    ".git",
    ".bbc",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".pytest_cache",
    "tests",
}


def _resolve_project(project_path: str) -> Path:
    return Path(project_path).expanduser().resolve()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _run_git(project_root: Path, args: List[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(project_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _load_gitignore(project_root: Path) -> List[str]:
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        return []
    try:
        return [
            line.strip()
            for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    except Exception:
        return []


def _is_ignored_by_pattern(rel_path: str, patterns: Iterable[str]) -> bool:
    normalized = rel_path.replace("\\", "/").strip("/")
    for raw in patterns:
        pattern = raw.replace("\\", "/").strip()
        if not pattern:
            continue
        if pattern.endswith("/"):
            prefix = pattern.strip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif normalized == pattern.strip("/"):
            return True
    return False


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [
            d
            for d in dirs
            if d not in SKIP_DIRS and not d.endswith(".egg-info") and not d.startswith(".pytest-tmp")
        ]
        for file_name in files:
            path = Path(root) / file_name
            if path.suffix.lower() in SCAN_EXTENSIONS:
                yield path


def _path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def _format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def scan_personal_markers(project_path: str, limit: int = 25) -> List[Dict[str, Any]]:
    project_root = _resolve_project(project_path)
    findings: List[Dict[str, Any]] = []
    for path in _iter_project_files(project_root):
        rel = path.relative_to(project_root).as_posix()
        if rel == "bbc_core/project_hygiene.py":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for marker in PERSONAL_PATH_MARKERS:
            if marker not in text:
                continue
            findings.append({"file": rel, "marker": marker})
            break
        if len(findings) >= limit:
            break
    return findings


def doctor_report(project_path: str = ".") -> Dict[str, Any]:
    project_root = _resolve_project(project_path)
    bbc_dir = project_root / ".bbc"
    context_path = bbc_dir / "bbc_context.json"
    gitignore_patterns = _load_gitignore(project_root)

    try:
        from bbc_core.ide_auto_config import IDEAutoConfigurator

        integrations = IDEAutoConfigurator().detect_active_integrations(project_root)
    except Exception:
        integrations = []

    try:
        from bbc_core.ide_parser import IDETokenParser

        usage_sources = IDETokenParser(str(project_root)).supported_sources()
    except Exception:
        usage_sources = {}

    missing_ignore = [
        item
        for item in [".bbc/", "bbc_context.json", "bbc_rules.md", "BBC_CONTEXT.md", "BBC_INSTRUCTIONS.md"]
        if not _is_ignored_by_pattern(item, gitignore_patterns)
    ]

    checks = [
        {
            "name": "project_exists",
            "ok": project_root.is_dir(),
            "detail": str(project_root),
        },
        {
            "name": "python_version",
            "ok": sys.version_info >= (3, 8),
            "detail": platform.python_version(),
        },
        {
            "name": "bbc_context",
            "ok": context_path.exists(),
            "detail": str(context_path),
        },
        {
            "name": "gitignore_no_trace",
            "ok": len(missing_ignore) == 0,
            "detail": "ok" if not missing_ignore else ", ".join(missing_ignore),
        },
        {
            "name": "ide_detection",
            "ok": True,
            "detail": ", ".join(sorted({i.get("id", "unknown") for i in integrations})) or "none detected",
        },
    ]

    bbc_size = _path_size(bbc_dir)
    status = "PASS" if all(c["ok"] for c in checks if c["name"] != "bbc_context") else "WARN"
    if not context_path.exists():
        status = "WARN"

    return {
        "status": status,
        "project_root": str(project_root),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "bbc_dir_exists": bbc_dir.exists(),
        "bbc_size_bytes": bbc_size,
        "bbc_size": _format_bytes(bbc_size),
        "checks": checks,
        "integrations": integrations,
        "usage_sources": usage_sources,
    }


def publish_check_report(project_path: str = ".") -> Dict[str, Any]:
    project_root = _resolve_project(project_path)
    gitignore_patterns = _load_gitignore(project_root)
    tracked_output = _run_git(project_root, ["ls-files"])
    tracked = set(tracked_output.splitlines()) if tracked_output is not None else set()

    trace_findings = []
    for trace in BBC_TRACE_PATHS:
        rel = trace.rstrip("/")
        path = project_root / rel
        exists = path.exists()
        tracked_match = rel in tracked or any(item == rel or item.startswith(rel.rstrip("/") + "/") for item in tracked)
        ignored = _is_ignored_by_pattern(trace, gitignore_patterns)
        if exists or tracked_match:
            severity = "error" if tracked_match or not ignored else "info"
            trace_findings.append(
                {
                    "path": trace,
                    "exists": exists,
                    "tracked": tracked_match,
                    "ignored": ignored,
                    "severity": severity,
                }
            )

    personal_markers = scan_personal_markers(str(project_root))
    errors = [
        f
        for f in trace_findings
        if f["severity"] == "error"
    ]
    if personal_markers:
        errors.append({"path": "personal_path_markers", "severity": "error", "count": len(personal_markers)})

    return {
        "status": "PASS" if not errors else "FAIL",
        "project_root": str(project_root),
        "git_available": tracked_output is not None,
        "trace_findings": trace_findings,
        "personal_path_markers": personal_markers,
        "error_count": len(errors),
    }


def clean_bbc_runtime(
    project_path: str = ".",
    older_than_days: int = 14,
    max_mb: int = 50,
    dry_run: bool = False,
) -> Dict[str, Any]:
    project_root = _resolve_project(project_path)
    bbc_dir = project_root / ".bbc"
    if not bbc_dir.exists():
        return {"status": "PASS", "project_root": str(project_root), "removed": [], "bytes_removed": 0}

    allowed_dirs = [bbc_dir / "logs", bbc_dir / "cache", bbc_dir / "telemetry"]
    cutoff = time.time() - (older_than_days * 24 * 60 * 60)
    candidates: List[Path] = []

    for base in allowed_dirs:
        if not base.exists() or not _is_under(base, bbc_dir):
            continue
        for item in base.rglob("*"):
            if not item.is_file() or not _is_under(item, bbc_dir):
                continue
            try:
                if item.stat().st_mtime < cutoff:
                    candidates.append(item)
            except OSError:
                continue

    current_size = _path_size(bbc_dir)
    max_bytes = max_mb * 1024 * 1024
    if current_size > max_bytes:
        all_files = []
        for base in allowed_dirs:
            if not base.exists() or not _is_under(base, bbc_dir):
                continue
            for item in base.rglob("*"):
                if item.is_file() and _is_under(item, bbc_dir):
                    try:
                        all_files.append((item.stat().st_mtime, item))
                    except OSError:
                        continue
        all_files.sort()
        size_to_remove = current_size - max_bytes
        planned = 0
        for _, item in all_files:
            if item in candidates:
                continue
            candidates.append(item)
            try:
                planned += item.stat().st_size
            except OSError:
                pass
            if planned >= size_to_remove:
                break

    removed = []
    bytes_removed = 0
    for item in candidates:
        if not _is_under(item, bbc_dir):
            continue
        try:
            size = item.stat().st_size
        except OSError:
            size = 0
        if not dry_run:
            try:
                item.unlink()
            except OSError:
                continue
        removed.append(str(item.relative_to(project_root).as_posix()))
        bytes_removed += size

    if not dry_run:
        for base in allowed_dirs:
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base, topdown=False):
                if files or dirs:
                    continue
                p = Path(root)
                if p != base and _is_under(p, bbc_dir):
                    try:
                        p.rmdir()
                    except OSError:
                        pass

    return {
        "status": "PASS",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "removed": removed,
        "bytes_removed": bytes_removed,
        "bytes_removed_human": _format_bytes(bytes_removed),
        "bbc_size_before": _format_bytes(current_size),
        "bbc_size_after": _format_bytes(_path_size(bbc_dir)),
    }


def print_doctor_report(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(" BBC DOCTOR")
    print("=" * 60)
    print(f"Project: {report['project_root']}")
    print(f"Status:  {report['status']}")
    print(f"Python:  {report['python']}")
    print(f".bbc:    {report['bbc_size']}")
    print("-" * 60)
    for check in report.get("checks", []):
        mark = "OK" if check.get("ok") else "WARN"
        print(f"[{mark:4}] {check['name']}: {check['detail']}")
    if report.get("usage_sources"):
        print("-" * 60)
        for name, meta in sorted(report["usage_sources"].items()):
            print(f"[INFO] {name}: {meta.get('status')} ({meta.get('source')})")
    print("=" * 60 + "\n")


def print_publish_check_report(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(" BBC PUBLISH CHECK")
    print("=" * 60)
    print(f"Project: {report['project_root']}")
    print(f"Status:  {report['status']}")
    print("-" * 60)
    for finding in report.get("trace_findings", []):
        mark = "ERR" if finding["severity"] == "error" else "INFO"
        print(
            f"[{mark:4}] {finding['path']} "
            f"exists={finding['exists']} tracked={finding['tracked']} ignored={finding['ignored']}"
        )
    for marker in report.get("personal_path_markers", []):
        print(f"[ERR ] personal path marker in {marker['file']} ({marker['marker']})")
    if report["status"] == "PASS":
        print("[OK  ] No publish-blocking BBC traces or personal path markers found.")
    print("=" * 60 + "\n")


def print_clean_report(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(" BBC RUNTIME CLEAN")
    print("=" * 60)
    print(f"Project: {report['project_root']}")
    print(f"Removed: {len(report.get('removed', []))} file(s), {report.get('bytes_removed_human', '0 B')}")
    print(f"Size:    {report.get('bbc_size_before', '0 B')} -> {report.get('bbc_size_after', '0 B')}")
    if report.get("dry_run"):
        print("Mode:    dry-run")
    print("=" * 60 + "\n")
