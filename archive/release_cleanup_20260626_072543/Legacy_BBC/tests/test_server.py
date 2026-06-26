# tests/test_server.py
import pytest
import os

try:
    from fastapi.testclient import TestClient
    from bbc_core.http_server import app
    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

pytestmark = pytest.mark.skipif(not HAS_SERVER_DEPS, reason="FastAPI or TestClient dependencies are missing")

def test_health_check(monkeypatch, tmp_path):
    # Setup dummy project root env var to avoid using global root
    monkeypatch.setenv("BBC_PROJECT_ROOT", str(tmp_path))
    
    # Create empty log folder structure under tmp_path to prevent logging errors
    os.makedirs(os.path.join(tmp_path, ".bbc", "logs"), exist_ok=True)
    
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "bbc_api"
        assert "status" in data
