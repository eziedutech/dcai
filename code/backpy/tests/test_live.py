"""Live updates (SSE with Last-Event-ID replay) and the per-conversation queue that merges
stage 2 calls for messages arriving together."""

import asyncio
from types import SimpleNamespace

import pytest

from app.live.broker import Broker, sse_stream
from tests.conftest import auth
from tests.test_devices import message, paired
from tests.test_risk_pipeline import KeywordScreening, ScriptedReasoning, analyzer


async def collect(gen, limit=50):
    out = []
    async for chunk in gen:
        out.append(chunk)
        if len(out) >= limit:
            break
    return out


async def test_stream_replays_missed_events_then_closes():
    bus = Broker()
    first = bus.publish("k", "a", {"n": 1})
    bus.publish("k", "b", {"n": 2})
    bus.publish("other", "x", {})
    chunks = await collect(
        sse_stream(bus, "k", f"{bus.boot}-{first.seq}", heartbeat=0.05, max_seconds=0.12)
    )
    events = [c for c in chunks if c.startswith("id:")]
    assert len(events) == 1 and "event: b" in events[0] and '"n":2' in events[0]
    assert any(c.startswith(": ping") for c in chunks)
    assert bus.subscriber_count("k") == 0  # unsubscribed on close


async def test_stream_delivers_live_events_once():
    bus = Broker()

    async def later():
        await asyncio.sleep(0.03)
        bus.publish("k", "nudge", {"level": "waspada"})

    task = asyncio.create_task(later())
    chunks = await collect(sse_stream(bus, "k", None, heartbeat=1, max_seconds=0.15))
    await task
    assert [c for c in chunks if "event: nudge" in c] != []
    assert sum("event: nudge" in c for c in chunks) == 1


def test_id_from_before_a_restart_gets_the_whole_buffer():
    bus = Broker()
    bus.publish("k", "a", {})
    bus.publish("k", "b", {})
    assert [e.event for e in bus.since("k", "deadbeef-1")] == ["a", "b"]
    assert bus.since("k", None) == []


def test_buffer_is_bounded():
    bus = Broker(buffer=3)
    for i in range(10):
        bus.publish("k", "e", {"i": i})
    assert [e.data["i"] for e in bus.since("k", "old-0")] == [7, 8, 9]


def test_device_stream_endpoint_replays_after_reconnect(api):
    _tokens, _child, dev, _body = paired(api)
    message(api, dev, "kirim foto kamu")
    api.app.state.settings.sse_max_seconds = 0.2
    resp = api.get("/v1/device/stream", headers={**dev, "Last-Event-ID": "old-0"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "event: nudge" in resp.text and "event: level" in resp.text
    assert "parent_insight" not in resp.text


def test_guardian_stream_is_for_own_children_only(api):
    from tests.conftest import register

    tokens, child, dev, _ = paired(api)
    message(api, dev, "kirim foto kamu")
    api.app.state.settings.sse_max_seconds = 0.2
    resp = api.get(
        f"/v1/children/{child['id']}/stream", headers={**auth(tokens), "Last-Event-ID": "old-0"}
    )
    assert resp.status_code == 200 and "event: insight" in resp.text
    other = register(api, email="lain@example.com")
    assert api.get(f"/v1/children/{child['id']}/stream", headers=auth(other)).status_code == 404
    assert api.get("/v1/device/stream").status_code == 401


# ------------------------------------------------------------------ queue


async def test_deferred_stage2_runs_once_with_the_evidence():
    reasoning = ScriptedReasoning([70])
    a = analyzer(reasoning=reasoning)
    s1 = await a.add("contact", "rahasia ya", assess=False)
    assert s1.stage2_called is False and a.pending_evidence is True
    s2 = await a.add("contact", "oke", assess=True)
    assert s2.stage2_called is True and reasoning.calls == 1
    assert a.pending_evidence is False


@pytest.fixture
def state(tmp_path):
    from tests.conftest import migrate

    url = f"sqlite:///{(tmp_path / 'q.db').as_posix()}"
    migrate(url)
    return SimpleNamespace(
        settings=SimpleNamespace(database_url=url),
        openweights=KeywordScreening(),
        muse=ScriptedReasoning([70, 70, 70]),
        analyzers=None,
        broker=None,
        worker=None,
    )


def _child_with_consent(url):
    import uuid

    from app.consent.texts import CURRENT
    from app.db.base import session_factory
    from app.db.models import ChildProfile, ConsentRecord, Conversation, Guardian

    with session_factory(url)() as db:
        g = Guardian(email=f"{uuid.uuid4().hex}@example.com", name="G", password_hash="h")
        db.add(g)
        db.flush()
        c = ChildProfile(guardian_id=g.id, nickname="Kit", age_range="13-15")
        db.add(c)
        db.flush()
        db.add(
            ConsentRecord(
                guardian_id=g.id,
                child_id=c.id,
                text_version=CURRENT.version,
                action="grant",
                scopes=["percakapan"],
                age_range="13-15",
            )
        )
        conv = Conversation(child_id=c.id, channel="dm")
        db.add(conv)
        db.commit()
        return c.id, conv.id


async def test_messages_arriving_together_share_one_stage2_call(state):
    from app.analysis.service import Job, worker

    child_id, conv_id = _child_with_consent(state.settings.database_url)
    w = worker(state)

    def job(t):
        return Job(conv_id, child_id, "id", False, "dm", "contact", t)

    futures = [w.submit(job(t), wait=True) for t in ("rahasia ya", "pindah ke app lain", "oke?")]
    results = await asyncio.gather(*futures)
    assert [r.step.index for r in results] == [1, 2, 3]
    assert [r.step.stage2_called for r in results] == [False, False, True]
    assert state.muse.calls == 1
    assert results[-1].step.level.value == "mendesak"
    # The second message already raised the level, but its Coach would be out of date by
    # the time it ran: one Coach call, for the final level, on the last message.
    assert results[1].step.raised and results[1].coach is None
    assert results[-1].coach is not None and state.muse.coach_calls == 1
    assert not w.busy()


async def test_a_failed_message_does_not_stop_the_queue(state):
    from app.analysis.service import ConversationGone, Job, worker

    child_id, conv_id = _child_with_consent(state.settings.database_url)
    import uuid

    w = worker(state)
    bad = w.submit(Job(uuid.uuid4(), child_id, "id", False, "dm", "contact", "halo"), wait=True)
    good = w.submit(Job(conv_id, child_id, "id", False, "dm", "contact", "halo"), wait=True)
    with pytest.raises(ConversationGone):
        await bad
    assert (await good).step.index == 1


async def test_consent_withdrawn_while_queued_drops_the_message(state):
    from app.analysis.service import ConsentWithdrawn, Job, worker
    from app.consent.texts import CURRENT
    from app.db.base import session_factory
    from app.db.models import ChildProfile, ConsentRecord

    child_id, conv_id = _child_with_consent(state.settings.database_url)
    with session_factory(state.settings.database_url)() as db:
        child = db.get(ChildProfile, child_id)
        db.add(
            ConsentRecord(
                guardian_id=child.guardian_id,
                child_id=child_id,
                text_version=CURRENT.version,
                action="revoke",
                scopes=["percakapan"],
                age_range="13-15",
            )
        )
        db.commit()
    fut = worker(state).submit(Job(conv_id, child_id, "id", False, "dm", "contact", "x"), wait=True)
    with pytest.raises(ConsentWithdrawn):
        await fut
    assert state.openweights.seen_text == []  # never reached a model
