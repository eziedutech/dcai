import pytest

from app.config import Settings, endpoint_from_env


def test_endpoint_reads_shared_provider_key(monkeypatch):
    monkeypatch.setenv("FIREWORKS_BASE", "https://api.fireworks.example/v1/")
    monkeypatch.setenv("FIREWORKS_API_KEY", "fw-key")
    monkeypatch.setenv("FW_MUSE_PROVIDER", "fireworks")
    monkeypatch.setenv("FW_MUSE_MODEL", "muse-model-id")
    monkeypatch.setenv("FW_MUSE_PRICE_IN_PER_MTOK", "1.25")

    ep = endpoint_from_env("fw_muse")

    assert ep is not None
    assert ep.base_url == "https://api.fireworks.example/v1"
    assert ep.api_key == "fw-key"
    assert ep.model == "muse-model-id"
    assert ep.price_in_per_mtok == 1.25
    assert ep.price_out_per_mtok is None
    assert "fw-key" not in repr(ep)


def test_meta_accepts_spec_variable_names(monkeypatch):
    monkeypatch.setenv("META_API_KEY", "meta-key")
    monkeypatch.setenv("MUSE_MODEL", "muse-from-models-list")

    ep = endpoint_from_env("meta")

    assert ep is not None
    assert ep.base_url == "https://api.meta.ai/v1"
    assert ep.model == "muse-from-models-list"


def test_incomplete_endpoint_is_skipped(monkeypatch):
    monkeypatch.setenv("HALF_BASE", "https://half.example/v1")
    monkeypatch.setenv("HALF_API_KEY", "k")
    monkeypatch.setenv("REASONING_ENDPOINTS", "half, missing")

    assert endpoint_from_env("half") is None
    assert Settings().endpoints("reasoning") == []


def test_bad_json_mode_is_refused(monkeypatch):
    for k, v in {
        "X_BASE": "https://x/v1",
        "X_API_KEY": "k",
        "X_MODEL": "m",
        "X_JSON_MODE": "yaml",
    }.items():
        monkeypatch.setenv(k, v)
    with pytest.raises(ValueError, match="JSON_MODE"):
        endpoint_from_env("x")


def test_pools_are_separate(monkeypatch):
    for name in ("A", "B"):
        monkeypatch.setenv(f"{name}_BASE", f"https://{name}/v1")
        monkeypatch.setenv(f"{name}_API_KEY", "k")
        monkeypatch.setenv(f"{name}_MODEL", f"m{name}")
    monkeypatch.setenv("REASONING_ENDPOINTS", "a,b")
    monkeypatch.setenv("SCREENING_ENDPOINTS", "b")

    s = Settings()

    assert [e.name for e in s.endpoints("reasoning")] == ["a", "b"]
    assert [e.name for e in s.endpoints("screening")] == ["b"]
