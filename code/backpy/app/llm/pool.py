"""A pool of endpoints behind one LLMClient.

Calls rotate across endpoints so no single provider carries all the load. A transient
failure moves to the next endpoint; an endpoint that answered 429 rests until its
Retry-After passes. Invalid JSON gets exactly one repair attempt, then LLMOutputInvalid,
and the caller falls back to its safe value. Logs carry metadata only, never text.
"""

import asyncio
import itertools
import json
import logging
import re
import time
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Endpoint
from app.llm.base import (
    LLMOutputInvalid,
    LLMResult,
    NoEndpointConfigured,
    PermanentLLMError,
    TransientLLMError,
    Usage,
)
from app.llm.endpoint import RawCompletion, call_chat, estimate_cost, response_format

log = logging.getLogger("dcai.llm")

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)
_DEFAULT_COOLDOWN_S = 10.0
_BACKOFF_BASE_S = 0.5


class PooledClient:
    family = "pool"

    def __init__(
        self,
        endpoints: list[Endpoint],
        *,
        http: httpx.AsyncClient | None = None,
        timeout: float = 20.0,
        max_transient_retries: int = 2,
        sleep=asyncio.sleep,
    ):
        self.endpoints = list(endpoints)
        self._http = http or httpx.AsyncClient()
        self._timeout = timeout
        self._max_retries = max_transient_retries
        self._sleep = sleep
        self._rotation = itertools.count()
        self._resting_until: dict[str, float] = {}

    def describe(self) -> list[dict[str, str]]:
        """Configured endpoints for health checks. No keys."""
        return [{"endpoint": e.name, "model": e.model} for e in self.endpoints]

    async def complete_json[T: BaseModel](
        self,
        *,
        purpose: str,
        system: str,
        user: str,
        schema: type[T],
        max_tokens: int = 800,
        timeout: float | None = None,
    ) -> LLMResult[T]:
        """timeout overrides the pool default for this call (long outputs need longer)."""
        if not self.endpoints:
            raise NoEndpointConfigured(f"no {self.family} endpoint configured")

        json_schema = schema.model_json_schema()
        messages = [
            {"role": "system", "content": json_system(system, schema)},
            {"role": "user", "content": user},
        ]
        attempts: list[Usage] = []

        endpoint, raw = await self._call_with_failover(
            purpose, messages, max_tokens, schema.__name__, json_schema, attempts, timeout
        )
        value, problem = _parse(raw.content, schema)
        if value is not None:
            return LLMResult(value=value, usage=attempts[-1], attempts=tuple(attempts))
        if raw.finish_reason == "length":
            # The budget, not the model, cut the answer. A repair with the same budget only
            # repeats the cut, so the caller hears about it at once.
            log.error(
                "llm_invalid_output purpose=%s endpoint=%s problem=truncated max_tokens=%d "
                "tokens_reasoning=%d action=give_up",
                purpose,
                endpoint.name,
                max_tokens,
                raw.tokens_reasoning,
            )
            raise LLMOutputInvalid(f"{purpose}: output truncated at max_tokens={max_tokens}")

        # One repair attempt on the same endpoint. The problem summary names fields and
        # error types only, never values.
        log.warning(
            "llm_invalid_output purpose=%s endpoint=%s problem=%s action=repair_once",
            purpose,
            endpoint.name,
            problem,
        )
        repair = [
            *messages,
            {"role": "assistant", "content": raw.content or ""},
            {
                "role": "user",
                "content": f"That output was invalid ({problem}). "
                "Reply again with ONLY the corrected JSON object.",
            },
        ]
        raw2 = await self._call_once(
            purpose, endpoint, repair, max_tokens, schema.__name__, json_schema, attempts, timeout
        )
        value, problem = _parse(raw2.content, schema)
        if value is not None:
            return LLMResult(value=value, usage=attempts[-1], attempts=tuple(attempts))
        log.error(
            "llm_invalid_output purpose=%s endpoint=%s problem=%s action=give_up",
            purpose,
            endpoint.name,
            problem,
        )
        raise LLMOutputInvalid(f"{purpose}: invalid output after one repair ({problem})")

    async def chat_tools(
        self,
        *,
        purpose: str,
        messages: list[dict[str, Any]],
        tools: list[dict],
        max_tokens: int = 1500,
        timeout: float | None = None,
    ) -> tuple[RawCompletion, Usage]:
        """One Chat Completions turn with function tools, with the same rotation, failover
        and metadata-only logging. The caller runs the tool loop and validates both the
        arguments and the final text: neither is trusted as it comes."""
        if not self.endpoints:
            raise NoEndpointConfigured(f"no {self.family} endpoint configured")
        attempts: list[Usage] = []
        _, raw = await self._call_with_failover(
            purpose, messages, max_tokens, None, None, attempts, timeout, tools
        )
        return raw, attempts[-1]

    async def _call_with_failover(
        self,
        purpose,
        messages,
        max_tokens,
        name,
        json_schema,
        attempts,
        timeout=None,
        tools=None,
    ) -> tuple[Endpoint, RawCompletion]:
        order = self._rotation_order()
        last: TransientLLMError | None = None
        for attempt in range(self._max_retries + 1):
            endpoint = order[attempt % len(order)]
            if attempt > 0 and len(order) == 1:
                delay = (
                    last.retry_after
                    if last and last.retry_after is not None
                    else _BACKOFF_BASE_S * 2 ** (attempt - 1)
                )
                log.info(
                    "llm_retry purpose=%s endpoint=%s attempt=%d delay_s=%.2f",
                    purpose,
                    endpoint.name,
                    attempt + 1,
                    delay,
                )
                await self._sleep(delay)
            elif attempt > 0:
                log.info(
                    "llm_failover purpose=%s endpoint=%s attempt=%d",
                    purpose,
                    endpoint.name,
                    attempt + 1,
                )
            try:
                raw = await self._call_once(
                    purpose,
                    endpoint,
                    messages,
                    max_tokens,
                    name,
                    json_schema,
                    attempts,
                    timeout,
                    tools,
                )
                return endpoint, raw
            except TransientLLMError as exc:
                last = exc
                if exc.status == 429:
                    self._resting_until[endpoint.name] = time.monotonic() + (
                        exc.retry_after or _DEFAULT_COOLDOWN_S
                    )
        assert last is not None
        raise last

    async def _call_once(
        self,
        purpose,
        endpoint,
        messages,
        max_tokens,
        name,
        json_schema,
        attempts,
        timeout=None,
        tools=None,
    ) -> RawCompletion:
        try:
            raw = await call_chat(
                self._http,
                endpoint,
                messages,
                max_tokens=max_tokens,
                fmt=None if json_schema is None else response_format(endpoint, name, json_schema),
                timeout=timeout or self._timeout,
                tools=tools,
            )
        except (TransientLLMError, PermanentLLMError) as exc:
            log.warning(
                "llm_call purpose=%s endpoint=%s model=%s status=error error=%s",
                purpose,
                endpoint.name,
                endpoint.model,
                exc,
            )
            raise
        cost = estimate_cost(endpoint, raw.tokens_in, raw.tokens_cached, raw.tokens_out)
        usage = Usage(
            endpoint.name,
            endpoint.model,
            raw.tokens_in,
            raw.tokens_cached,
            raw.tokens_out,
            raw.latency_ms,
            cost,
            raw.tokens_reasoning,
        )
        attempts.append(usage)
        log.info(
            "llm_call purpose=%s endpoint=%s model=%s status=ok tokens_in=%d tokens_cached=%d "
            "tokens_out=%d tokens_reasoning=%d finish=%s latency_ms=%d cost_usd=%s",
            purpose,
            endpoint.name,
            endpoint.model,
            raw.tokens_in,
            raw.tokens_cached,
            raw.tokens_out,
            raw.tokens_reasoning,
            raw.finish_reason,
            raw.latency_ms,
            "unknown" if cost is None else f"{cost:.6f}",
        )
        return raw

    def _rotation_order(self) -> list[Endpoint]:
        start = next(self._rotation) % len(self.endpoints)
        rotated = self.endpoints[start:] + self.endpoints[:start]
        now = time.monotonic()
        awake = [e for e in rotated if self._resting_until.get(e.name, 0.0) <= now]
        # If every endpoint is resting, still try them: a refusal beats silent waiting.
        return awake or rotated

    async def aclose(self) -> None:
        await self._http.aclose()


def json_system(system: str, schema: type[BaseModel]) -> str:
    """The system prompt as the model receives it: the task, then the JSON instruction and
    schema. Distillation builds its training data with this, so a fine-tuned model is
    trained on exactly what it sees in production."""
    json_schema = schema.model_json_schema()
    return (
        f"{system}\n\nRespond with ONLY one JSON object that matches this JSON Schema. "
        f"No prose, no code fences.\n{json.dumps(json_schema, separators=(',', ':'))}"
    )


def _parse[T: BaseModel](content: str | None, schema: type[T]) -> tuple[T | None, str]:
    if not content:
        return None, "empty content"
    text = content.strip()
    if m := _FENCE.match(text):
        text = m.group(1)
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError:
        return None, "not JSON"
    try:
        return schema.model_validate(data), ""
    except ValidationError as exc:
        problems = [
            f"{'.'.join(str(p) for p in e['loc']) or 'root'}:{e['type']}"
            for e in exc.errors(include_input=False, include_url=False)
        ]
        return None, ",".join(problems[:6])
