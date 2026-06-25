import json
import sys

import pytest

import bbc
import bbc_core.cli as core_cli


def test_cli_version_flag(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bbc", "--version"])

    with pytest.raises(SystemExit) as exc:
        bbc.main()

    assert exc.value.code == 0
    assert "BBC 8.6.0" in capsys.readouterr().out


def test_benchmark_reports_context_metrics(tmp_path, capsys):
    bbc_dir = tmp_path / ".bbc"
    bbc_dir.mkdir()
    context = {
        "constraint_status": "sealed",
        "context_fresh": True,
        "project_skeleton": {"file_count": 2},
        "code_structure": [
            {"path": "a.py", "structure": {"classes": ["A"], "functions": ["main"]}},
            {"path": "b.py", "structure": {"classes": [], "functions": ["helper"]}},
        ],
        "metrics": {
            "files_scanned": 2,
            "raw_tokens": 1000,
            "context_tokens": 100,
            "unified_tokens_saved": 900,
            "unified_savings_pct": 90.0,
        },
    }
    (bbc_dir / "bbc_context.json").write_text(json.dumps(context), encoding="utf-8")

    code = bbc.BBCCLI().benchmark(str(tmp_path), json_output=True)
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["files_scanned"] == 2
    assert output["symbols_extracted"] == 3
    assert output["normal_tokens"] == 1000
    assert output["bbc_tokens"] == 100
    assert output["tokens_avoided"] == 900
    assert output["reduction_pct"] == 90.0


def test_core_cli_inject_uses_global_bbc_config(tmp_path, monkeypatch):
    bbc_dir = tmp_path / ".bbc"
    bbc_dir.mkdir()
    (tmp_path / "sample.py").write_text("def hello():\n    return 'ok'\n", encoding="utf-8")
    context = {
        "constraint_status": "sealed",
        "context_fresh": True,
        "project_skeleton": {"root": str(tmp_path), "file_count": 1},
        "code_structure": [
            {"path": "sample.py", "structure": {"classes": [], "functions": ["hello"], "imports": []}},
        ],
        "metrics": {"files_scanned": 1, "savings_pct": 90.0},
    }
    (bbc_dir / "bbc_context.json").write_text(json.dumps(context), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        ["bbc", "inject", str(tmp_path), "--silent", "--allow-stale", "--no-optimize"],
    )

    core_cli.main()

    instructions = (bbc_dir / "BBC_INSTRUCTIONS.md").read_text(encoding="utf-8")
    assert "REUSE-FIRST" in instructions


def test_preview_reports_no_source_or_github_writes(tmp_path, capsys):
    code = bbc.BBCCLI().preview(str(tmp_path), json_output=True)
    report = json.loads(capsys.readouterr().out)

    assert code == 0
    assert report["status"] == "PASS"
    assert any(item["action"] == "analyze" for item in report["actions"])
    assert any("will not push anything to GitHub" in item for item in report["skipped"])
    assert any("will not touch project source files" in item for item in report["skipped"])


def test_rule_health_passes_for_core_invariants(tmp_path, capsys):
    bbc_dir = tmp_path / ".bbc"
    bbc_dir.mkdir()
    (bbc_dir / "BBC_INSTRUCTIONS.md").write_text(
        "sealed context\nno hallucination\nREUSE-FIRST reuse verified\n",
        encoding="utf-8",
    )
    (bbc_dir / "bbc_rules.md").write_text(
        "read bbc_context.json\nnever hallucinate\nreuse verified symbols\n",
        encoding="utf-8",
    )

    code = bbc.BBCCLI().rule_health(str(tmp_path), json_output=True)
    report = json.loads(capsys.readouterr().out)

    assert code == 0
    assert report["status"] == "PASS"


def test_security_check_flags_secret_marker(tmp_path, capsys):
    (tmp_path / ".gitignore").write_text(".bbc/\n", encoding="utf-8")
    (tmp_path / "settings.py").write_text("SECRET=real-value-123456789\n", encoding="utf-8")

    code = bbc.BBCCLI().security_check(str(tmp_path), json_output=True)
    report = json.loads(capsys.readouterr().out)

    assert code == 1
    assert report["status"] == "FAIL"
    assert report["secret_findings"][0]["file"] == "settings.py"


def test_readiness_combines_core_checks(tmp_path, capsys):
    bbc_dir = tmp_path / ".bbc"
    bbc_dir.mkdir()
    (tmp_path / ".gitignore").write_text(".bbc/\nbbc_context.json\nbbc_rules.md\nBBC_CONTEXT.md\nBBC_INSTRUCTIONS.md\n", encoding="utf-8")
    (bbc_dir / "BBC_INSTRUCTIONS.md").write_text(
        "sealed context\nno hallucination\nREUSE-FIRST reuse verified\n",
        encoding="utf-8",
    )
    (bbc_dir / "bbc_rules.md").write_text(
        "read bbc_context.json\nnever hallucinate\nreuse verified symbols\n",
        encoding="utf-8",
    )
    (bbc_dir / "bbc_context.json").write_text(
        json.dumps({
            "constraint_status": "sealed",
            "context_fresh": True,
            "project_skeleton": {"file_count": 1},
            "code_structure": [{"path": "a.py", "structure": {"classes": [], "functions": ["main"]}}],
            "metrics": {"files_scanned": 1, "raw_tokens": 100, "context_tokens": 10, "unified_tokens_saved": 90},
        }),
        encoding="utf-8",
    )

    code = bbc.BBCCLI().readiness(str(tmp_path), json_output=True)
    report = json.loads(capsys.readouterr().out)

    assert code == 0
    assert report["status"] == "PASS"


def test_mode_writes_context_mode_config(tmp_path, capsys):
    code = bbc.BBCCLI().mode(str(tmp_path), value="quality", json_output=True)
    report = json.loads(capsys.readouterr().out)
    config = json.loads((tmp_path / ".bbc" / "config.json").read_text(encoding="utf-8"))

    assert code == 0
    assert report["mode"] == "quality"
    assert config["context_mode"] == "quality"
