"""Model access. The rest of the app depends on LLMClient only, never on a provider."""

import httpx

from app.config import Settings
from app.llm.base import (
    LLMClient,
    LLMError,
    LLMOutputInvalid,
    LLMResult,
    NoEndpointConfigured,
    PermanentLLMError,
    TransientLLMError,
    Usage,
)
from app.llm.pool import PooledClient


class MuseClient(PooledClient):
    """Muse Spark for stage 2 and the Citizenship Guide. Endpoints may be the Meta Model
    API and other hosts of the same model; calls are spread across them."""

    family = "reasoning"


class OpenWeightsClient(PooledClient):
    """Small open-weights model (Llama class) for stage 1 screening, spread across hosts."""

    family = "screening"


def build_clients(
    settings: Settings, http: httpx.AsyncClient | None = None
) -> tuple[MuseClient, OpenWeightsClient]:
    http = http or httpx.AsyncClient()
    common = {
        "http": http,
        "timeout": settings.llm_timeout_seconds,
        "max_transient_retries": settings.llm_max_transient_retries,
    }
    return (
        MuseClient(settings.endpoints("reasoning"), **common),
        OpenWeightsClient(settings.endpoints("screening"), **common),
    )


__all__ = [
    "LLMClient",
    "LLMError",
    "LLMOutputInvalid",
    "LLMResult",
    "MuseClient",
    "NoEndpointConfigured",
    "OpenWeightsClient",
    "PermanentLLMError",
    "PooledClient",
    "TransientLLMError",
    "Usage",
    "build_clients",
]
