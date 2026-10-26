import os

os.environ["DCAI_SKIP_DOTENV"] = "1"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.config import Endpoint, get_settings

BACKPY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_SECRET = "test-only-" + "x" * 40  # not a real secret


def make_endpoint(name: str = "ep1", **kw) -> Endpoint:
    defaults = {
        "base_url": f"https://{name}.example.test/v1",
        "api_key": f"key-{name}",
        "model": f"model-{name}",
        "price_in_per_mtok": 1.25,
        "price_cached_per_mtok": 0.15,
        "price_out_per_mtok": 4.25,
    }
    defaults.update(kw)
    return Endpoint(name=name, **defaults)


def chat_response(content: str | None, tokens_in=100, tokens_out=20, cached=0) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "prompt_tokens_details": {"cached_tokens": cached},
        },
    }


class SleepRecorder:
    def __init__(self):
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


@pytest.fixture
def sleeper() -> SleepRecorder:
    return SleepRecorder()


def migrate(url: str) -> None:
    cfg = Config(os.path.join(BACKPY, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKPY, "migrations"))
    cfg.attributes["url"] = url
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


PG_URL = os.environ.get("DCAI_TEST_PG_URL", "")


@pytest.fixture(params=["sqlite", "postgres"])
def db_url(request, tmp_path) -> str:
    """Every database test runs on SQLite, and on PostgreSQL when DCAI_TEST_PG_URL is set.
    The PostgreSQL database is wiped before each test, so point it at a throwaway one."""
    if request.param == "sqlite":
        url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    else:
        if not PG_URL:
            pytest.skip("DCAI_TEST_PG_URL not set")
        from sqlalchemy import text

        from app.db.base import make_engine

        url = PG_URL
        engine = make_engine(url)
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        engine.dispose()
    migrate(url)
    return url


@pytest.fixture
def api(db_url, monkeypatch):
    from app.main import app

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("REASONING_ENDPOINTS", "")
    monkeypatch.setenv("SCREENING_ENDPOINTS", "")
    get_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def register(api, email="ibu@example.com", password="kata-sandi-panjang", name="Ibu Sari"):
    resp = api.post("/v1/auth/register", json={"email": email, "password": password, "name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth(tokens) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
