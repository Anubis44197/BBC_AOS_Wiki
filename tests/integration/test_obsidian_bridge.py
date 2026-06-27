import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.wiki.obsidian_bridge import ensure_workspace_vault_visible_in_obsidian


class TestObsidianBridgeProduction(unittest.TestCase):
    def test_registers_workspace_vault_and_links_existing_vault(self) -> None:
        root = Path(tempfile.mkdtemp())
        appdata = root / "appdata" / "obsidian"
        open_vault = root / "Documents" / "Obsidian Vault"
        workspace_vault = root / "repo" / "BBC_KNOWLEDGE"
        open_vault.mkdir(parents=True)
        workspace_vault.mkdir(parents=True)
        config = {"vaults": {"old": {"path": str(open_vault), "ts": 1, "open": True}}}
        appdata.mkdir(parents=True)
        (appdata / "obsidian.json").write_text(json.dumps(config), encoding="utf-8")

        result = ensure_workspace_vault_visible_in_obsidian(workspace_vault, appdata)

        self.assertTrue(result["registered"])
        self.assertTrue((workspace_vault / ".obsidian" / "app.json").exists())
        linked_path = open_vault / "BBC_KNOWLEDGE"
        self.assertTrue(linked_path.exists())
        updated = json.loads((appdata / "obsidian.json").read_text(encoding="utf-8"))
        paths = [row["path"] for row in updated["vaults"].values()]
        self.assertIn(str(workspace_vault.resolve()), paths)

    def test_existing_non_link_conflict_is_reported(self) -> None:
        root = Path(tempfile.mkdtemp())
        appdata = root / "appdata" / "obsidian"
        open_vault = root / "Documents" / "Obsidian Vault"
        workspace_vault = root / "repo" / "BBC_KNOWLEDGE"
        (open_vault / "BBC_KNOWLEDGE").mkdir(parents=True)
        workspace_vault.mkdir(parents=True)
        config = {"vaults": {"old": {"path": str(open_vault), "ts": 1, "open": True}}}
        appdata.mkdir(parents=True)
        (appdata / "obsidian.json").write_text(json.dumps(config), encoding="utf-8")

        result = ensure_workspace_vault_visible_in_obsidian(workspace_vault, appdata)

        self.assertIn(str(open_vault / "BBC_KNOWLEDGE"), result["conflicts"])


if __name__ == "__main__":
    unittest.main()
