import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.wiki.compiler import WikiCompiler
from bbc_aos.wiki.paths import resolve_workspace_vault


class TestWikiPathHardeningProduction(unittest.TestCase):
    def test_resolver_uses_workspace_vault(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.assertEqual(resolve_workspace_vault(root), (root / "BBC_KNOWLEDGE").resolve())

    def test_resolver_rejects_outside_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        outside = Path(tempfile.mkdtemp()) / "BBC_KNOWLEDGE"
        with self.assertRaises(ValueError):
            resolve_workspace_vault(root, outside)

    def test_resolver_rejects_noncanonical_inside_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        with self.assertRaises(ValueError):
            resolve_workspace_vault(root, root / "nested" / "BBC_KNOWLEDGE")

    def test_wiki_compiler_creates_project_inside_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        project = WikiCompiler(workspace_root=root).ensure_project("demo")
        self.assertTrue(str(project.resolve()).startswith(str((root / "BBC_KNOWLEDGE").resolve())))


if __name__ == "__main__":
    unittest.main()
