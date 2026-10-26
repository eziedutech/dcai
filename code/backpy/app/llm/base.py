"""The one interface every model call goes through."""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel


class LLMError(Exception):
    """Base for model call failures. Messages never contain prompt or output text."""


class NoEndpointConfigured(LLMError):
    pass


class TransientLLMError(LLMError):
    """Rate limit, timeout, connection failure or 5xx. Worth retrying, within limits."""

    def __init__(
        self, message: str, *, status: int | None = None, retry_after: float | None = None
    ):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


class PermanentLLMError(LLMError):
    """Auth failure, malformed request, unknown model. Retrying only repeats the answer."""


class LLMOutputInvalid(LLMError):
    """The model answered, but not with JSON that passes the schema, even after one repair."""


@dataclass(frozen=True)
class Usage:
    endpoint: str
    model: str
    tokens_in: int
    tokens_cached: int
    tokens_out: int
    latency_ms: int
    cost_usd: float | None
    tokens_reasoning: int = 0


@dataclass(frozen=True)
class LLMResult[T: BaseModel]:
    value: T
    usage: Usage
    # Every attempt, including failed ones, so cost and retries stay visible.
    attempts: tuple[Usage, ...]


class LLMClient(Protocol):
    async def complete_json[T: BaseModel](
        self,
        *,
        purpose: str,
        system: str,
        user: str,
        schema: type[T],
        max_tokens: int = 800,
        timeout: float | None = None,
    ) -> LLMResult[T]: ...
