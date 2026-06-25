import json

from bbc_core.agent_adapter import BBC_REUSE_FIRST_RULE, BBCAgentAdapter, inject_to_project


def _sealed_context(tmp_path):
    return {
        "constraint_status": "sealed",
        "project_skeleton": {
            "root": str(tmp_path),
            "file_count": 2,
            "hierarchy": ["app.py", "helpers.py"],
        },
        "code_structure": [
            {
                "path": "app.py",
                "structure": {
                    "classes": ["App"],
                    "functions": ["main"],
                    "imports": ["helpers"],
                },
                "stats": {"lines": 20},
            },
            {
                "path": "helpers.py",
                "structure": {
                    "classes": [],
                    "functions": ["normalize_name"],
                    "imports": [],
                },
                "stats": {"lines": 12},
            },
        ],
        "metrics": {
            "files_scanned": 2,
            "compression_ratio": 0.91,
            "savings_pct": 91.0,
        },
        "context_fresh": True,
        "enforcement_level": "strict",
        "fail_policy": "fail_closed",
    }


def test_agent_adapter_outputs_keep_reuse_first_invariant(tmp_path):
    adapter = BBCAgentAdapter(_sealed_context(tmp_path))
    outputs = {
        "copilot": adapter.to_copilot_prompt(),
        "cursor": adapter.to_cursor_context(),
        "gemini": adapter.to_gemini_context(),
        "kilo": adapter.to_kilo_context(),
        "vscode": adapter.to_vscode_context(),
        "generic": json.dumps(adapter.to_generic_context()),
    }

    for label, content in outputs.items():
        assert "hallucinat" in content.lower(), label
        assert (
            "reuse verified symbols" in content.lower()
            or "reuse_first" in content.lower()
        ), label


def test_inject_to_project_keeps_reuse_first_in_central_and_ide_rules(tmp_path):
    context_path = tmp_path / ".bbc" / "bbc_context.json"
    context_path.parent.mkdir()
    context_path.write_text(json.dumps(_sealed_context(tmp_path)), encoding="utf-8")
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    (tmp_path / ".cursorrules").write_text("Cursor project rules", encoding="utf-8")

    created = inject_to_project(
        str(context_path),
        str(tmp_path),
        optimize=False,
        active_command="inject",
        model="gpt-4",
    )

    central = (tmp_path / ".bbc" / "BBC_INSTRUCTIONS.md").read_text(encoding="utf-8")
    rules = (tmp_path / ".bbc" / "bbc_rules.md").read_text(encoding="utf-8")
    cursor = (tmp_path / ".cursorrules").read_text(encoding="utf-8")

    assert "BBC Instructions" in created
    assert "REUSE-FIRST" in central
    assert "Before adding new code" in central
    assert "Reuse verified symbols" in rules
    assert "Reuse verified symbols" in cursor
