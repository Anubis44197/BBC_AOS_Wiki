import asyncio

from bbc_core.change_tracker import ChangeTracker
from bbc_core.native_adapter import BBCNativeAdapter
from bbc_core.scan_profile import iter_source_files
from bbc_core.symbol_extractor import SymbolExtractor


def _write(path, text="def keep():\n    return 1\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_scan_profile_excludes_large_repo_noise(tmp_path):
    _write(tmp_path / "src" / "app.py")
    _write(tmp_path / "node_modules" / "pkg" / "bad.py")
    _write(tmp_path / "target" / "debug" / "generated.rs", "fn bad() {}\n")
    _write(tmp_path / "dist" / "bundle.js", "function bad() {}\n")
    _write(tmp_path / "ignored" / "skip.py")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / "large.json").write_text("x" * (2 * 1024 * 1024 + 1), encoding="utf-8")
    (tmp_path / ".bbcignore").write_text("ignored/\n", encoding="utf-8")

    files = sorted(p.relative_to(tmp_path).as_posix() for p in iter_source_files(tmp_path))

    assert files == ["src/app.py"]


def test_change_tracker_uses_scan_profile(tmp_path):
    _write(tmp_path / "src" / "app.py")
    _write(tmp_path / "node_modules" / "pkg" / "bad.py")
    _write(tmp_path / "target" / "debug" / "generated.rs", "fn bad() {}\n")

    tracker = ChangeTracker(str(tmp_path))
    current = tracker.scan_current_state()

    assert sorted(current) == ["src\\app.py"] or sorted(current) == ["src/app.py"]


def test_symbol_extractor_uses_scan_profile(tmp_path):
    _write(tmp_path / "src" / "app.py")
    _write(tmp_path / "node_modules" / "pkg" / "bad.py")

    results = SymbolExtractor().extract_from_directory(str(tmp_path))
    files = sorted(result.file.replace("\\", "/") for result in results)

    assert len(files) == 1
    assert files[0].endswith("/src/app.py")


def test_native_analyze_uses_scan_profile(tmp_path):
    _write(tmp_path / "src" / "app.py")
    _write(tmp_path / "node_modules" / "pkg" / "bad.py")
    _write(tmp_path / "target" / "debug" / "generated.rs", "fn bad() {}\n")

    adapter = BBCNativeAdapter(str(tmp_path))
    context = asyncio.run(adapter.analyze_project(str(tmp_path), silent=True))
    hierarchy = sorted(path.replace("\\", "/") for path in context["project_skeleton"]["hierarchy"])

    assert hierarchy == ["src/app.py"]
    assert context["metrics"]["files_scanned"] == 1
