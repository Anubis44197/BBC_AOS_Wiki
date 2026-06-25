import os
import time

from bbc_core.project_hygiene import clean_bbc_runtime, doctor_report, publish_check_report


def test_doctor_reports_missing_context_as_warning(tmp_path):
    (tmp_path / ".gitignore").write_text(".bbc/\nbbc_context.json\nbbc_rules.md\nBBC_CONTEXT.md\nBBC_INSTRUCTIONS.md\n", encoding="utf-8")

    report = doctor_report(str(tmp_path))

    assert report["status"] == "WARN"
    assert report["project_root"] == str(tmp_path.resolve())
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["project_exists"]["ok"]
    assert not checks["bbc_context"]["ok"]
    assert checks["gitignore_no_trace"]["ok"]
    assert report["usage_sources"]["cursor"]["status"] == "real_usage_supported"


def test_publish_check_flags_unignored_bbc_trace_and_personal_path(tmp_path):
    (tmp_path / ".bbc").mkdir()
    (tmp_path / "README.md").write_text("Local path: C:\\Users\\90535\\Desktop\\demo", encoding="utf-8")

    report = publish_check_report(str(tmp_path))

    assert report["status"] == "FAIL"
    assert any(f["path"] == ".bbc" and not f["ignored"] for f in report["trace_findings"])
    assert report["personal_path_markers"]


def test_publish_check_passes_when_bbc_trace_is_ignored(tmp_path):
    (tmp_path / ".bbc").mkdir()
    (tmp_path / ".gitignore").write_text(".bbc/\n", encoding="utf-8")

    report = publish_check_report(str(tmp_path))

    assert report["status"] == "PASS"
    assert any(f["path"] == ".bbc" and f["ignored"] for f in report["trace_findings"])


def test_clean_bbc_runtime_removes_only_old_runtime_files(tmp_path):
    logs = tmp_path / ".bbc" / "logs"
    cache = tmp_path / ".bbc" / "cache"
    logs.mkdir(parents=True)
    cache.mkdir(parents=True)
    old_log = logs / "old.log"
    fresh_cache = cache / "fresh.json"
    old_log.write_text("old", encoding="utf-8")
    fresh_cache.write_text("fresh", encoding="utf-8")

    old_time = time.time() - (30 * 24 * 60 * 60)
    os.utime(old_log, (old_time, old_time))

    report = clean_bbc_runtime(str(tmp_path), older_than_days=14, dry_run=False)

    assert ".bbc/logs/old.log" in report["removed"]
    assert not old_log.exists()
    assert fresh_cache.exists()
