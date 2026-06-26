import json
import os
import sqlite3

from bbc_core.ide_parser import IDETokenParser
from bbc_core.memory_store import MemoryStore


def test_memory_store_remember_recall_conflict_force(tmp_path):
    store = MemoryStore(str(tmp_path))

    ok, msg = store.remember("Policy", "Always inspect before edit")
    assert ok, msg

    ok, msg = store.remember("Policy", "Conflicting value")
    assert not ok
    assert "CONFLICT" in msg

    results = store.recall("inspect")
    assert len(results) == 1
    assert results[0]["topic"] == "Policy"
    assert results[0]["content"] == "Always inspect before edit"

    ok, msg = store.remember("Policy", "Overwrite allowed", force=True)
    assert ok, msg
    results = store.recall("Overwrite")
    assert len(results) == 1
    assert results[0]["content"] == "Overwrite allowed"

    memory_md = tmp_path / ".bbc" / "BBC_MEMORY.md"
    assert memory_md.exists()
    assert "Overwrite allowed" in memory_md.read_text(encoding="utf-8")


def test_ide_parser_reads_cursor_sqlite(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    db_dir = appdata / "Cursor" / "User" / "globalStorage"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "state.vscdb"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
    chat_data = {
        "tabs": [
            {
                "bubbles": [
                    {"type": "user", "text": "abcd" * 10},
                    {"type": "ai", "text": "efgh" * 6, "modelType": "gpt-4o"},
                ]
            }
        ]
    }
    conn.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
        ("workbench.panel.aichat.view.aichat.chatdata", json.dumps(chat_data)),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("APPDATA", str(appdata))
    parser = IDETokenParser(str(tmp_path))

    success, msg, data = parser.get_real_usage("cursor")
    assert success, msg
    assert data["input_tokens"] == 10
    assert data["output_tokens"] == 6
    assert data["total_tokens"] == 16
    assert data["total_chars"] == 64
    assert data["message_count"] == 2
    assert data["model"] == "gpt-4o"


def test_ide_parser_does_not_return_synthetic_usage(tmp_path, monkeypatch):
    monkeypatch.delenv("APPDATA", raising=False)
    parser = IDETokenParser(str(tmp_path))

    for ide_name in ("vscode", "windsurf"):
        success, msg, data = parser.get_real_usage(ide_name)
        assert not success
        assert data == {}
        assert "not found" in msg.lower() or "not implemented" in msg.lower()

    success, msg, data = parser.get_real_usage("unknown")
    assert not success
    assert data == {}
    assert "Unsupported IDE" in msg
