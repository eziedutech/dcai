from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_health_lists_endpoints_without_keys(monkeypatch):
    monkeypatch.setenv("REASONING_ENDPOINTS", "fw_muse")
    monkeypatch.setenv("FW_MUSE_BASE", "https://fw.example/v1")
    monkeypatch.setenv("FW_MUSE_API_KEY", "very-secret-key")
    monkeypatch.setenv("FW_MUSE_MODEL", "muse-id")
    monkeypatch.setenv("SCREENING_ENDPOINTS", "")
    get_settings.cache_clear()
    try:
        with TestClient(app) as c:
            resp = c.get("/v1/health")
    finally:
        get_settings.cache_clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["models"]["reasoning"] == [{"endpoint": "fw_muse", "model": "muse-id"}]
    assert body["models"]["screening"] == []
    assert "very-secret-key" not in resp.text
