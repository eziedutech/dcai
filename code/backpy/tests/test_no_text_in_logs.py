"""Message text must never reach a log (spec section 10, rule 5).

Every path through the model client runs with a sentinel in the prompt and in the model
output, with all loggers at DEBUG (httpx included), and the captured log is searched.
"""

import json
import logging

import httpx
import pytest
import respx
from pydantic import BaseModel

from app.llm import LLMError, OpenWeightsClient
from tests.conftest import chat_response, make_endpoint

SENTINEL = "SENTINEL-PESAN-ANAK-7f3a"


class Out(BaseModel):
    label: str


def _assert_clean(caplog):
    for record in caplog.records:
        assert SENTINEL not in record.getMessage(), record.getMessage()
        if record.exc_info:
            assert SENTINEL not in str(record.exc_info[1])


async def _run(caplog, sleeper, *responses):
    ep = make_endpoint()
    respx.post(f"{ep.base_url}/chat/completions").mock(side_effect=list(responses))
    c = OpenWeightsClient([ep], http=httpx.AsyncClient(), max_transient_retries=1, sleep=sleeper)
    caplog.set_level(logging.DEBUG)
    try:
        await c.complete_json(
            purpose="screen", system=f"sys {SENTINEL}", user=f"pesan: {SENTINEL}", schema=Out
        )
    except LLMError as exc:
        assert SENTINEL not in str(exc)
    _assert_clean(caplog)


@respx.mock
async def test_success_path(caplog, sleeper):
    await _run(
        caplog, sleeper, httpx.Response(200, json=chat_response(json.dumps({"label": SENTINEL})))
    )


@respx.mock
async def test_invalid_output_path(caplog, sleeper):
    bad = json.dumps({"label": 5, "extra": SENTINEL})
    await _run(
        caplog,
        sleeper,
        httpx.Response(200, json=chat_response(bad)),
        httpx.Response(200, json=chat_response(f"not json {SENTINEL}")),
    )


@respx.mock
@pytest.mark.parametrize("status", [400, 429, 500])
async def test_error_paths_with_echoing_provider(caplog, sleeper, status):
    echo = {"error": {"type": "bad", "message": f"you sent {SENTINEL}"}}
    await _run(
        caplog, sleeper, httpx.Response(status, json=echo), httpx.Response(status, json=echo)
    )
