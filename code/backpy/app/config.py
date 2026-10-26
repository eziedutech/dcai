"""Configuration read from the environment. Values never live in the repo.

Model endpoints are grouped in two pools:

- reasoning: stage 2 risk assessment and Citizenship Coach (Muse Spark)
- screening: stage 1 per-message labels (small open-weights model)

Each pool lists endpoint names, for example REASONING_ENDPOINTS=meta,fw_muse.
An endpoint name N reads N_BASE, N_API_KEY, N_MODEL, N_JSON_MODE, N_REASONING_EFFORT and
N_PRICE_IN_PER_MTOK, N_PRICE_CACHED_PER_MTOK, N_PRICE_OUT_PER_MTOK. When N_PROVIDER
is set (for example fireworks), missing N_BASE and N_API_KEY are read from
FIREWORKS_BASE and FIREWORKS_API_KEY, so one key serves several models.
The name "meta" also accepts the spec names META_API_BASE, META_API_KEY, MUSE_MODEL.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

JsonMode = Literal["json_schema", "json_object", "none"]
Pool = Literal["reasoning", "screening"]

_META_ALIASES = {"BASE": "META_API_BASE", "API_KEY": "META_API_KEY", "MODEL": "MUSE_MODEL"}
_META_DEFAULT_BASE = "https://api.meta.ai/v1"


@dataclass(frozen=True)
class Endpoint:
    """One OpenAI-compatible chat completions endpoint serving one model."""

    name: str
    base_url: str
    api_key: str = field(repr=False)
    model: str
    json_mode: JsonMode = "json_schema"
    # Sent as reasoning_effort when set. Muse Spark is a reasoning model and refuses "none".
    reasoning_effort: str | None = None
    price_in_per_mtok: float | None = None
    price_cached_per_mtok: float | None = None
    price_out_per_mtok: float | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    reasoning_endpoints: str = ""
    screening_endpoints: str = ""

    llm_timeout_seconds: float = 20.0
    llm_max_transient_retries: int = 2

    database_url: str = "sqlite:///./dcai.db"
    # Signs access tokens. Required: the app refuses to issue tokens without it.
    secret_key: str = ""
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    evidence_enc_key: str = ""
    replay_mode: bool = False

    def endpoints(self, pool: Pool) -> list[Endpoint]:
        raw = self.reasoning_endpoints if pool == "reasoning" else self.screening_endpoints
        names = [n.strip() for n in raw.split(",") if n.strip()]
        return [ep for name in names if (ep := endpoint_from_env(name)) is not None]


def endpoint_from_env(name: str) -> Endpoint | None:
    """Build an endpoint from the environment, or None if base, key or model is missing."""
    prefix = name.upper().replace("-", "_")
    provider = os.environ.get(f"{prefix}_PROVIDER", "").upper().replace("-", "_")

    def read(suffix: str) -> str:
        value = os.environ.get(f"{prefix}_{suffix}", "")
        if not value and provider:
            value = os.environ.get(f"{provider}_{suffix}", "")
        if not value and prefix == "META" and suffix in _META_ALIASES:
            value = os.environ.get(_META_ALIASES[suffix], "")
        return value

    base = read("BASE") or (_META_DEFAULT_BASE if prefix == "META" else "")
    key = read("API_KEY")
    model = read("MODEL")
    if not (base and key and model):
        return None
    mode = read("JSON_MODE") or "json_schema"
    if mode not in ("json_schema", "json_object", "none"):
        raise ValueError(f"{prefix}_JSON_MODE must be json_schema, json_object or none")
    return Endpoint(
        name=name,
        base_url=base.rstrip("/"),
        api_key=key,
        model=model,
        json_mode=mode,  # type: ignore[arg-type]
        reasoning_effort=read("REASONING_EFFORT") or None,
        price_in_per_mtok=_to_float(read("PRICE_IN_PER_MTOK")),
        price_cached_per_mtok=_to_float(read("PRICE_CACHED_PER_MTOK")),
        price_out_per_mtok=_to_float(read("PRICE_OUT_PER_MTOK")),
    )


def _to_float(raw: str) -> float | None:
    return float(raw) if raw else None


@lru_cache
def get_settings() -> Settings:
    # One source for both Settings and the per-endpoint variables: .env fills os.environ
    # without overriding values already set by the shell or the container.
    # Tests set DCAI_SKIP_DOTENV so a developer's real keys never leak into a test run.
    if not os.environ.get("DCAI_SKIP_DOTENV"):
        load_dotenv(override=False)
    return Settings()
