# tests/test_auto_detect.py
import os
import pytest
from pathlib import Path
from bbc_core.ide_auto_config import IDEAutoConfigurator
from bbc_core.cli import count_tokens
from bbc_core.native_adapter import BBCNativeAdapter

def test_tokenizer_model_specific():
    sample_text = "def hello_world():\n    print('Hello from Bitter Brain Context')"
    
    # Check that different models return custom estimated counts or tiktoken counts
    gpt4_count = count_tokens(sample_text, model="gpt-4")
    claude_count = count_tokens(sample_text, model="claude")
    gemini_count = count_tokens(sample_text, model="gemini")
    
    # Ratios check
    assert claude_count == int(len(sample_text) / 3.8)
    assert gemini_count == int(len(sample_text) / 3.7)
    assert gpt4_count > 0

def test_auto_detect_from_existing_files(tmp_path):
    configurator = IDEAutoConfigurator()
    
    # 1. No files in temp directory -> no integrations detected
    integrations = configurator.detect_active_integrations(tmp_path)
    # Filter out any globally running processes detected in test environment
    local_ids = {i["id"] for i in integrations if i["id"] in ("cursor", "cline")}
    assert len(local_ids) == 0
    
    # 2. Create .cursorrules in temp directory -> Cursor should be detected
    (tmp_path / ".cursorrules").write_text("BBC Cursor Rules", encoding="utf-8")
    integrations = configurator.detect_active_integrations(tmp_path)
    ids = {i["id"] for i in integrations}
    assert "cursor" in ids
    
    # 3. Create .clinerules -> Cline should be detected
    (tmp_path / ".clinerules").write_text("BBC Cline Rules", encoding="utf-8")
    integrations = configurator.detect_active_integrations(tmp_path)
    ids = {i["id"] for i in integrations}
    assert "cursor" in ids
    assert "cline" in ids

    # 4. Existing Antigravity rules should keep Antigravity injection alive
    antigravity_dir = tmp_path / ".antigravity"
    antigravity_dir.mkdir()
    (antigravity_dir / "rules.md").write_text("BBC Antigravity Rules", encoding="utf-8")
    integrations = configurator.detect_active_integrations(tmp_path)
    ids = {i["id"] for i in integrations}
    assert "antigravity" in ids

def test_auto_detect_from_env(tmp_path, monkeypatch):
    configurator = IDEAutoConfigurator()
    
    # Mock CURSOR_SESSION env variable
    monkeypatch.setenv("CURSOR_SESSION", "test-session-123")
    
    integrations = configurator.detect_active_integrations(tmp_path)
    ids = {i["id"] for i in integrations}
    assert "cursor" in ids

def test_dependency_graph_accepts_normalized_import_names():
    adapter = BBCNativeAdapter()
    files = ["mcp_server_main.py", "app.py", "nested/worker.py"]
    recipes = [
        {"path": "mcp_server_main.py", "structure": {"imports": []}},
        {"path": "app.py", "structure": {"imports": ["mcp_server_main"]}},
        {"path": "nested/worker.py", "structure": {"imports": ["from mcp_server_main import app"]}},
    ]

    graph = adapter._build_dependency_graph(recipes, files)

    assert graph["app.py"]["depends_on"] == ["mcp_server_main.py"]
    assert graph["nested/worker.py"]["depends_on"] == ["mcp_server_main.py"]
    assert set(graph["mcp_server_main.py"]["depended_by"]) == {"app.py", "nested/worker.py"}


def test_dependency_graph_accepts_dynamic_imports():
    adapter = BBCNativeAdapter()
    files = ["plugins/foo.py", "loader.py", "legacy_loader.py"]
    recipes = [
        {"path": "plugins/foo.py", "structure": {"imports": []}},
        {"path": "loader.py", "structure": {"imports": ['importlib.import_module("plugins.foo")']}},
        {"path": "legacy_loader.py", "structure": {"imports": ["__import__('plugins.foo')"]}},
    ]

    graph = adapter._build_dependency_graph(recipes, files)

    assert graph["loader.py"]["depends_on"] == ["plugins/foo.py"]
    assert graph["legacy_loader.py"]["depends_on"] == ["plugins/foo.py"]
    assert set(graph["plugins/foo.py"]["depended_by"]) == {"loader.py", "legacy_loader.py"}
