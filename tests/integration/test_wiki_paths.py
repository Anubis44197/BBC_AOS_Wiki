import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.wiki.compiler import WikiCompiler
from bbc_aos.wiki.entity_registry import EntityRegistry, normalize_entity_name
from bbc_aos.wiki.paths import resolve_workspace_vault
from bbc_aos.wiki.wikilink_resolver import WikilinkResolver
from bbc_aos.runtime_paths import wiki_vault_dir


class TestWikiPathHardeningProduction(unittest.TestCase):
    def setUp(self) -> None:
        self._old_workspace_env = os.environ.get("BBC_AOS_WORKSPACES")
        self._ghost_root = Path(tempfile.mkdtemp()) / "BBC_WORKSPACES"
        os.environ["BBC_AOS_WORKSPACES"] = str(self._ghost_root)

    def tearDown(self) -> None:
        if self._old_workspace_env is None:
            os.environ.pop("BBC_AOS_WORKSPACES", None)
        else:
            os.environ["BBC_AOS_WORKSPACES"] = self._old_workspace_env

    def test_resolver_uses_ghost_workspace_vault(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.assertEqual(resolve_workspace_vault(root), wiki_vault_dir(root).resolve())
        self.assertFalse((root / "BBC_KNOWLEDGE").exists())

    def test_resolver_rejects_outside_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        outside = root / "BBC_KNOWLEDGE"
        with self.assertRaises(ValueError):
            resolve_workspace_vault(root, outside)

    def test_resolver_rejects_noncanonical_ghost_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        with self.assertRaises(ValueError):
            resolve_workspace_vault(root, wiki_vault_dir(root).parent / "nested")

    def test_wiki_compiler_creates_project_outside_source_workspace(self) -> None:
        root = Path(tempfile.mkdtemp())
        project = WikiCompiler(workspace_root=root).ensure_project("demo")
        self.assertTrue(str(project.resolve()).startswith(str(wiki_vault_dir(root).resolve())))
        self.assertFalse((root / "BBC_KNOWLEDGE").exists())

    def test_wikilink_repair_reaches_zero_broken_links(self) -> None:
        root = Path(tempfile.mkdtemp())
        project = WikiCompiler(workspace_root=root).ensure_project("demo")
        (project / "Concepts" / "concept.md").write_text("# Concept\n[[Missing Provider|alias]]\n[[Other#section]]\n", encoding="utf-8")
        resolver = WikilinkResolver(EntityRegistry(project, runtime_root=root))

        resolver.repair_project()

        self.assertEqual(resolver.broken_link_count(), 0)

    def test_long_entity_names_are_deterministically_shortened(self) -> None:
        raw = "extreme pilot phase " + ("very long title " * 30)
        first = normalize_entity_name(raw)
        second = normalize_entity_name(raw)

        self.assertEqual(first, second)
        self.assertLessEqual(len(first), 96)


if __name__ == "__main__":
    unittest.main()
