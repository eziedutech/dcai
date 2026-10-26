"""A single HTTP call to an OpenAI-compatible /chat/completions endpoint.

Plain httpx instead of a vendor SDK: every provider here speaks the same wire format,
and owning the request lets us classify failures (transient or permanent) exactly.
"""

import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Endpoint
from app.llm.base import PermanentLLMError, TransientLLMError

_TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


@dataclass(frozen=True)
class RawCompletion:
    content: str | None
    tokens_in: int
    tokens_cached: int
    tokens_out: int
    latency_ms: int
    # Thinking tokens are part of tokens_out and of max_tokens; logged to explain cost.
    tokens_reasoning: int = 0
    finish_reason: str | None = None


def response_format(endpoint: Endpoint, schema_name: str, schema: dict[str, Any]) -> dict | None:
    if endpoint.json_mode == "json_schema":
        return {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": schema, "strict": True},
        }
    if endpoint.json_mode == "json_object":
        return {"type": "json_object"}
    return None


async def call_chat(
    http: httpx.AsyncClient,
    endpoint: Endpoint,
    messages: list[dict[str, str]],
    *,
    max_tokens: int,
    fmt: dict | None,
    timeout: float,
) -> RawCompletion:
    body: dict[str, Any] = {
        "model": endpoint.model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if fmt is not None:
        body["response_format"] = fmt
    if endpoint.reasoning_effort:
        body["reasoning_effort"] = endpoint.reasoning_effort

    started = time.perf_counter()
    try:
        resp = await http.post(
            f"{endpoint.base_url}/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {endpoint.api_key}"},
            timeout=timeout,
        )
    except httpx.TimeoutException as exc:
        raise TransientLLMError(f"timeout after {timeout}s") from exc
    except httpx.TransportError as exc:
        raise TransientLLMError(f"connection failed: {type(exc).__name__}") from exc
    latency_ms = int((time.perf_counter() - started) * 1000)

    if resp.status_code in _TRANSIENT_STATUS:
        raise TransientLLMError(
            f"HTTP {resp.status_code}",
            status=resp.status_code,
            retry_after=_retry_after(resp.headers.get("retry-after")),
        )
    if resp.status_code >= 400:
        raise PermanentLLMError(f"HTTP {resp.status_code}: {_error_summary(resp)}")

    try:
        data = resp.json()
        choice = data["choices"][0]
        content = choice["message"].get("content")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise TransientLLMError("response is not a chat completion") from exc

    usage = data.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    out_details = usage.get("completion_tokens_details") or {}
    return RawCompletion(
        content=content,
        tokens_in=int(usage.get("prompt_tokens") or 0),
        tokens_cached=int(details.get("cached_tokens") or 0),
        tokens_out=int(usage.get("completion_tokens") or 0),
        latency_ms=latency_ms,
        tokens_reasoning=int(out_details.get("reasoning_tokens") or 0),
        finish_reason=choice.get("finish_reason"),
    )


def estimate_cost(endpoint: Endpoint, tokens_in: int, tokens_cached: int, tokens_out: int):
    """USD cost from configured prices, or None when a price is unknown (never guessed)."""
    if endpoint.price_in_per_mtok is None or endpoint.price_out_per_mtok is None:
        return None
    cached_price = endpoint.price_cached_per_mtok
    if cached_price is None:
        cached_price = endpoint.price_in_per_mtok
    uncached = max(tokens_in - tokens_cached, 0)
    return (
        uncached * endpoint.price_in_per_mtok
        + tokens_cached * cached_price
        + tokens_out * endpoint.price_out_per_mtok
    ) / 1_000_000


def _retry_after(raw: str | None) -> float | None:
    try:
        return max(float(raw), 0.0) if raw else None
    except ValueError:
        return None


def _error_summary(resp: httpx.Response) -> str:
    """Error type and code only. Provider messages can echo request content, so they are
    not kept: an exception message may end up in a log."""
    try:
        err = resp.json().get("error")
    except ValueError:
        return resp.reason_phrase
    if not isinstance(err, dict):
        return resp.reason_phrase
    parts = [str(err[k])[:60] for k in ("type", "code") if err.get(k)]
    return " ".join(parts) or resp.reason_phrase
