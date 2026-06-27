import tempfile
import unittest
from pathlib import Path

from bbc_aos.core.impact_analysis import LayeredImpactAnalyzer


class TestDeepBlastRadiusHardeningProduction(unittest.TestCase):
    def _workspace(self) -> Path:
        root = Path(tempfile.mkdtemp())
        files = {
            "article_search.py": "from mevzuat_client import MevzuatClient\n",
            "mevzuat_client.py": "from mevzuat_models import SearchRequest\n",
            "mevzuat_mcp_server.py": "from article_search import search\n",
            "mevzuat_models.py": "class SearchRequest: pass\n",
            "bedesten_client.py": "class BedestenClient: pass\n",
            "bedesten_models.py": "class BedestenModel: pass\n",
            "semantic_search/processor.py": "from semantic_search.cache import Cache\n",
            "semantic_search/cache.py": "class Cache: pass\n",
            "semantic_search/embedder.py": "class Embedder: pass\n",
            "semantic_search/vector_store.py": "class VectorStore: pass\n",
            "semantic_search/__init__.py": "",
            "app.py": "from mevzuat_mcp_server import app\n",
            "tests/test_article_search.py": "def test_search(): pass\n",
            "tests/test_legal_providers.py": "def test_providers(): pass\n",
            "README.md": "legal search provider cache telemetry\n",
            "requirements.txt": "redis\nopentelemetry-api\n",
            "pyproject.toml": "[project]\n",
            "fastmcp.json": "{}\n",
            "docs/api.md": "search_all_courts yargitay danistay kvkk kik bddk\n",
            "docs/security.md": "timeouts url validation\n",
            "config/providers.yaml": "providers: []\n",
            "schemas/search.json": "{}\n",
            "deployment/fly.toml": "app='demo'\n",
        }
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    def _context(self, root: Path) -> dict:
        code_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*.py"))
        return {
            "project_skeleton": {"root": str(root), "file_count": len(code_files), "hierarchy": code_files},
            "code_structure": [{"path": path, "stats": {"lines": 10, "code_lines": 8}} for path in code_files],
            "dependency_graph": {
                "article_search.py": {"depends_on": ["mevzuat_client.py"], "depended_by": ["mevzuat_mcp_server.py"]},
                "mevzuat_client.py": {"depends_on": ["mevzuat_models.py"], "depended_by": ["article_search.py"]},
                "mevzuat_mcp_server.py": {"depends_on": ["article_search.py"], "depended_by": ["app.py"]},
            },
            "symbol_analysis": {"critical_symbols": []},
        }

    def test_unified_legal_search_expands_to_large_blast_radius(self) -> None:
        root = self._workspace()
        result = LayeredImpactAnalyzer(self._context(root)).analyze(
            "Unified Legal Search API search_all_courts aggregates Yargitay Danistay AYM KVKK KIK BDDK",
            target_file="article_search.py",
        )

        self.assertGreaterEqual(result["affected_file_count"], 20)
        self.assertIn(result["blast_radius_class"], {"LARGE", "MASSIVE"})
        self.assertGreaterEqual(result["blast_radius_score"], 70)
        self.assertIn("article_search.py", result["change_impact_matrix"]["PRIMARY"])
        self.assertTrue(result["change_impact_matrix"]["DIRECT"])
        self.assertTrue(result["change_impact_matrix"]["TRANSITIVE"])

    def test_cache_and_telemetry_include_shared_infrastructure(self) -> None:
        root = self._workspace()
        result = LayeredImpactAnalyzer(self._context(root)).analyze(
            "Caching Layer and OpenTelemetry instrumentation for all search tools",
            target_file="semantic_search/cache.py",
        )

        affected = set(result["affected_files"])
        self.assertIn("requirements.txt", affected)
        self.assertIn("pyproject.toml", affected)
        self.assertIn("semantic_search/cache.py", affected)
        self.assertGreaterEqual(result["affected_file_count"], 20)


if __name__ == "__main__":
    unittest.main()
