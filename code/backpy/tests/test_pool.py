import json

import httpx
import pytest
import respx
from pydantic import BaseModel, ConfigDict

from app.llm import (
    LLMOutputInvalid,
    MuseClient,
    NoEndpointConfigured,
    PermanentLLMError,
    TransientLLMError,
)
from tests.conftest import chat_response, make_endpoint


class Echo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    n: int


GOOD = json.dumps({"answer": "ok", "n": 1})


def client(endpoints, sleeper, retries=2):
    return MuseClient(
        endpoints, http=httpx.AsyncClient(), max_transient_retries=retries, sleep=sleeper
    )


async def ask(c):
    return await c.complete_json(purpose="test", system="sys", user="usr", schema=Echo)


@respx.mock
async def test_valid_output_parsed_with_usage_and_cost(sleeper):
    ep = make_endpoint()
    route = respx.post(f"{ep.base_url}/chat/completions").respond(
        json=chat_response(GOOD, tokens_in=1_000_000, tokens_out=1_000_000, cached=400_000)
    )

    result = await ask(client([ep], sleeper))

    assert result.value == Echo(answer="ok", n=1)
    assert result.usage.tokens_cached == 400_000
    # 600k uncached at 1.25 + 400k cached at 0.15 + 1M out at 4.25
    assert result.usage.cost_usd == pytest.approx(0.75 + 0.06 + 4.25)
    body = json.loads(route.calls[0].request.content)
    assert body["model"] == ep.model
    assert body["response_format"]["type"] == "json_schema"
    assert route.calls[0].request.headers["authorization"] == f"Bearer {ep.api_key}"


@respx.mock
async def test_code_fence_is_accepted(sleeper):
    ep = make_endpoint(json_mode="none")
    route = respx.post(f"{ep.base_url}/chat/completions").respond(
        json=chat_response(f"```json\n{GOOD}\n```")
    )

    result = await ask(client([ep], sleeper))

    assert result.value.n == 1
    assert "response_format" not in json.loads(route.calls[0].request.content)


@respx.mock
async def test_unknown_price_gives_unknown_cost(sleeper):
    ep = make_endpoint(price_in_per_mtok=None)
    respx.post(f"{ep.base_url}/chat/completions").respond(json=chat_response(GOOD))

    result = await ask(client([ep], sleeper))

    assert result.usage.cost_usd is None


@respx.mock
async def test_invalid_output_repaired_once(sleeper):
    ep = make_endpoint()
    route = respx.post(f"{ep.base_url}/chat/completions").mock(
        side_effect=[
            httpx.Response(200, json=chat_response('{"answer": "ok"}')),
            httpx.Response(200, json=chat_response(GOOD)),
        ]
    )

    result = await ask(client([ep], sleeper))

    assert result.value.n == 1
    assert len(result.attempts) == 2
    repair = json.loads(route.calls[1].request.content)["messages"]
    assert repair[-1]["role"] == "user"
    assert "n:missing" in repair[-1]["content"]


@respx.mock
async def test_invalid_twice_raises(sleeper):
    ep = make_endpoint()
    route = respx.post(f"{ep.base_url}/chat/completions").respond(json=chat_response("nope"))

    with pytest.raises(LLMOutputInvalid):
        await ask(client([ep], sleeper))
    assert route.call_count == 2


@respx.mock
async def test_429_fails_over_and_rests_endpoint(sleeper):
    a, b = make_endpoint("a"), make_endpoint("b")
    ra = respx.post(f"{a.base_url}/chat/completions").respond(429, headers={"retry-after": "30"})
    rb = respx.post(f"{b.base_url}/chat/completions").respond(json=chat_response(GOOD))
    c = client([a, b], sleeper)

    first = await ask(c)  # rotation starts at a, falls over to b
    second = await ask(c)  # rotation starts at b
    third = await ask(c)  # would start at a, but a is resting

    assert [r.usage.endpoint for r in (first, second, third)] == ["b", "b", "b"]
    assert ra.call_count == 1
    assert rb.call_count == 3
    assert sleeper.delays == []  # failover to another endpoint does not wait


@respx.mock
async def test_round_robin_spreads_load(sleeper):
    eps = [make_endpoint(n) for n in ("a", "b", "c")]
    routes = [
        respx.post(f"{e.base_url}/chat/completions").respond(json=chat_response(GOOD)) for e in eps
    ]
    c = client(eps, sleeper)

    for _ in range(6):
        await ask(c)

    assert [r.call_count for r in routes] == [2, 2, 2]


@respx.mock
async def test_single_endpoint_retries_bounded_with_backoff(sleeper):
    ep = make_endpoint()
    route = respx.post(f"{ep.base_url}/chat/completions").respond(503)

    with pytest.raises(TransientLLMError):
        await ask(client([ep], sleeper, retries=2))

    assert route.call_count == 3
    assert sleeper.delays == [0.5, 1.0]


@respx.mock
async def test_timeout_is_transient(sleeper):
    ep = make_endpoint()
    respx.post(f"{ep.base_url}/chat/completions").mock(
        side_effect=[
            httpx.ReadTimeout("slow"),
            httpx.Response(200, json=chat_response(GOOD)),
        ]
    )

    result = await ask(client([ep], sleeper))

    assert result.value.n == 1
    assert sleeper.delays == [0.5]


@respx.mock
async def test_permanent_error_is_not_retried(sleeper):
    a, b = make_endpoint("a"), make_endpoint("b")
    ra = respx.post(f"{a.base_url}/chat/completions").respond(
        401, json={"error": {"type": "auth", "code": "invalid_key", "message": "secret echo"}}
    )
    rb = respx.post(f"{b.base_url}/chat/completions").respond(json=chat_response(GOOD))

    with pytest.raises(PermanentLLMError) as exc:
        await ask(client([a, b], sleeper))

    assert "invalid_key" in str(exc.value)
    assert "secret echo" not in str(exc.value)
    assert ra.call_count == 1
    assert rb.call_count == 0


async def test_no_endpoints(sleeper):
    with pytest.raises(NoEndpointConfigured):
        await ask(client([], sleeper))


@respx.mock
async def test_truncated_output_is_not_repaired(sleeper):
    ep = make_endpoint()
    resp = chat_response(None, tokens_out=200)
    resp["choices"][0]["finish_reason"] = "length"
    resp["usage"]["completion_tokens_details"] = {"reasoning_tokens": 200}
    route = respx.post(f"{ep.base_url}/chat/completions").respond(json=resp)

    with pytest.raises(LLMOutputInvalid, match="truncated"):
        await ask(client([ep], sleeper))
    assert route.call_count == 1


@respx.mock
async def test_reasoning_effort_sent_and_reasoning_tokens_kept(sleeper):
    ep = make_endpoint(reasoning_effort="low")
    resp = chat_response(GOOD, tokens_out=150)
    resp["usage"]["completion_tokens_details"] = {"reasoning_tokens": 116}
    route = respx.post(f"{ep.base_url}/chat/completions").respond(json=resp)

    result = await ask(client([ep], sleeper))

    assert json.loads(route.calls[0].request.content)["reasoning_effort"] == "low"
    assert result.usage.tokens_reasoning == 116


@respx.mock
async def test_reasoning_effort_omitted_by_default(sleeper):
    ep = make_endpoint()
    route = respx.post(f"{ep.base_url}/chat/completions").respond(json=chat_response(GOOD))

    await ask(client([ep], sleeper))

    assert "reasoning_effort" not in json.loads(route.calls[0].request.content)
