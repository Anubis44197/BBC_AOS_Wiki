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
