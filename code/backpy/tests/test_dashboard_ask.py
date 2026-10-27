"""Dashboard read endpoints and Ask dcAI with a scripted tool-calling model."""

import json
import logging

from app.llm import TransientLLMError
from app.llm.endpoint import RawCompletion
from tests.conftest import auth, register
from tests.test_children_consent import add_child
from tests.test_devices import message, paired
from tests.test_risk_pipeline import USAGE

SENTINEL = "SENTINEL-TANYA-ORTU-55ab"


# ------------------------------------------------------------------ dashboard


def test_overview_after_activity_on_the_phone(api):
    tokens, child, dev, _ = paired(api)
    api.post(
        "/v1/device/heartbeat",
        json={"app_version": "0.1.0", "services": {"accessibility": True, "notification": True}},
        headers=dev,
    )
    message(api, dev, "halo")
    message(api, dev, "kirim foto kamu")
    api.post(
        "/v1/device/images",
        json={
            "trigger": "percakapan",
            "sender": "contact",
            "category": "seksual",
            "action": "dikaburkan",
            "score": 90,
            "model_version": "test",
        },
        headers=dev,
    )
    ov = api.get(f"/v1/children/{child['id']}/overview", headers=auth(tokens)).json()
    assert ov["level"] == "waspada"
    assert ov["conversations_active"] == 1 and ov["conversations_needing_attention"] == 1
    assert ov["events_by_kind"] == {"gambar_sensitif": 1, "risiko_naik": 1}
    assert ov["sensitive_images_blurred"] == 1
    assert ov["devices"][0]["protection_on"] is True
    latest = ov["latest_insight"]
    assert latest["situation"] == "approach" and latest["source"] in ("model", "template")
    assert latest["child_nudge"] and latest["app"] == "com.example.gamechat"
    assert latest["help_channels"]  # waspada: verified channels from configuration


def test_conversations_events_insights(api):
    tokens, child, dev, _ = paired(api)
    message(api, dev, f"halo {SENTINEL}")
    message(api, dev, f"kirim foto kamu {SENTINEL}")
    h = auth(tokens)
    convs = api.get(f"/v1/children/{child['id']}/conversations", headers=h)
    events = api.get(f"/v1/children/{child['id']}/events?days=7", headers=h)
    insights = api.get(f"/v1/children/{child['id']}/insights", headers=h)
    for resp in (convs, events, insights):
        assert resp.status_code == 200 and SENTINEL not in resp.text
    assert [c["level"] for c in convs.json()] == ["waspada"]
    assert [e["kind"] for e in events.json()] == ["risiko_naik"]
    assert len(insights.json()) == 1
    assert api.get(f"/v1/children/{child['id']}/events?days=0", headers=h).status_code == 422


def test_protection_off_shows_on_the_dashboard(api):
    tokens, child, dev, _ = paired(api)
    beat = {"app_version": "0.1.0", "services": {"accessibility": False, "notification": True}}
    api.post("/v1/device/heartbeat", json=beat, headers=dev)
    rows = api.get(f"/v1/children/{child['id']}/protection", headers=auth(tokens)).json()
    assert rows[0]["protection_on"] is False


def test_dashboard_is_for_own_children_only(api):
    _tokens, child, _, _ = paired(api)
    other = register(api, email="lain@example.com")
    for path in ("overview", "conversations", "events", "insights", "protection"):
        assert api.get(f"/v1/children/{child['id']}/{path}", headers=auth(other)).status_code == 404


def test_guardian_changes_language(api):
    tokens = register(api)
    resp = api.patch("/v1/auth/me", json={"language": "en"}, headers=auth(tokens))
    assert resp.status_code == 200 and resp.json()["language"] == "en"
    assert (
        api.patch("/v1/auth/me", json={"language": "fr"}, headers=auth(tokens)).status_code == 422
    )


# ------------------------------------------------------------------ Ask dcAI


def call(name, args, cid="call_1"):
    return {
        "id": cid,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def raw(content=None, tool_calls=()):
    return RawCompletion(
        content, 10, 0, 5, 100, 0, "tool_calls" if tool_calls else "stop", tuple(tool_calls)
    )


class ScriptedTools:
    """Plays a list of turns and records what it was sent."""

    def __init__(self, turns, fail=False):
        self.turns = list(turns)
        self.fail = fail
        self.sent: list[list[dict]] = []

    async def chat_tools(self, *, messages, tools, **kw):
        self.sent.append(json.loads(json.dumps(messages)))
        if self.fail:
            raise TransientLLMError("HTTP 503", status=503)
        return self.turns.pop(0), USAGE


def ask(api, tokens, question, history=()):
    return api.post(
        "/v1/ask", json={"question": question, "history": list(history)}, headers=auth(tokens)
    )


def test_ask_uses_tools_with_aliases_and_answers_with_names(api):
    tokens, child, dev, _ = paired(api)
    message(api, dev, "kirim foto kamu")
    model = ScriptedTools(
        [
            raw(tool_calls=[call("list_children", {})]),
            raw(
                tool_calls=[
                    call("get_overview", {"child": "Anak A", "days": 7}, "c2"),
                    call("list_insights", {"child": "Anak A"}, "c3"),
                ]
            ),
            raw("Anak A sedang di level waspada. Ajak bicara dengan tenang hari ini."),
        ]
    )
    api.app.state.muse = model
    resp = ask(api, tokens, "Bagaimana kabar Kit minggu ini?")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"] == "model" and body["is_estimate"] is True
    assert body["tools_used"] == ["list_children", "get_overview", "list_insights"]
    assert body["answer"].startswith("Kit sedang di level waspada")

    sent = json.dumps(model.sent)
    assert "Kit" not in sent  # neither the question nor any tool result carried the name
    assert child["id"] not in sent
    assert "Bagaimana kabar Anak A minggu ini?" in sent
    last = model.sent[-1]
    tool_msgs = [m for m in last if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_msgs] == ["call_1", "c2", "c3"]
    overview = json.loads(tool_msgs[1]["content"])
    assert overview["child"] == "Anak A" and overview["level"] == "waspada"


def test_ask_invalid_tool_arguments_are_answered_not_run(api):
    tokens, *_ = paired(api)
    model = ScriptedTools(
        [
            raw(tool_calls=[call("get_overview", {"child": "Kit"})]),
            raw(tool_calls=[call("delete_everything", {}, "c2")]),
            raw("Saya hanya bisa membantu dengan insight dcAI."),
        ]
    )
    api.app.state.muse = model
    body = ask(api, tokens, "hapus semua").json()
    assert body["source"] == "model"
    results = [json.loads(m["content"]) for m in model.sent[-1] if m["role"] == "tool"]
    assert results[0]["error"] == "invalid arguments"
    assert results[1]["error"] == "unknown tool delete_everything"


def test_ask_unknown_alias_is_an_error_result(api):
    tokens, *_ = paired(api)
    model = ScriptedTools(
        [raw(tool_calls=[call("list_events", {"child": "Anak Z"})]), raw("Tidak ada data.")]
    )
    api.app.state.muse = model
    ask(api, tokens, "Anak Z?")
    result = json.loads(model.sent[-1][-1]["content"])
    assert result["error"] == "unknown child Anak Z" and result["children"] == ["Anak A"]


def test_ask_answer_with_a_link_or_number_falls_back(api):
    tokens, *_ = paired(api)
    for bad in ("Hubungi 0812 3456 7890 sekarang.", "Lihat https://contoh.test ya."):
        api.app.state.muse = ScriptedTools([raw(bad)])
        api.app.state.ask_limiter = None
        body = ask(api, tokens, "apa yang harus saya lakukan?").json()
        assert body["source"] == "fallback"
        assert "Kit" in body["answer"] and "0812" not in body["answer"]


def test_ask_answer_may_mention_dates_and_times(api):
    tokens, *_ = paired(api)
    api.app.state.muse = ScriptedTools(
        [raw("Kejadian tercatat 2026-10-27T10:15:00Z, pukul 10.15.")]
    )
    assert ask(api, tokens, "kapan?").json()["source"] == "model"


def test_ask_model_down_or_endless_tools_gives_the_fixed_summary(api):
    tokens, *_ = paired(api)
    api.app.state.muse = ScriptedTools([], fail=True)
    body = ask(api, tokens, "ringkas?").json()
    assert body["source"] == "fallback" and body["answer"].startswith("Tanya dcAI sedang")

    api.app.state.muse = ScriptedTools([raw(tool_calls=[call("how_dcai_works", {})])] * 10)
    body = ask(api, tokens, "ringkas?").json()
    assert body["source"] == "fallback" and len(body["tools_used"]) == 5


def test_ask_without_children(api):
    tokens = register(api)
    api.app.state.muse = ScriptedTools([], fail=True)
    assert ask(api, tokens, "halo").json()["answer"] == "Belum ada anak yang ditambahkan."


def test_ask_history_is_aliased_and_limited(api):
    tokens, *_ = paired(api)
    model = ScriptedTools([raw("Baik.")])
    api.app.state.muse = model
    history = [
        {"role": "user", "content": "Kit kenapa?"},
        {"role": "assistant", "content": "Kit aman."},
    ]
    ask(api, tokens, "lalu?", history)
    assert "Kit" not in json.dumps(model.sent)
    too_long = [{"role": "user", "content": "x"}] * 9
    assert ask(api, tokens, "lalu?", too_long).status_code == 422


def test_ask_rate_limit_and_no_question_in_logs(api, caplog):
    caplog.set_level(logging.DEBUG)
    tokens, *_ = paired(api)
    api.app.state.ask_limiter = None
    api.app.state.muse = ScriptedTools([raw("Baik.")] * 10)
    for _ in range(6):
        assert ask(api, tokens, f"pertanyaan {SENTINEL}").status_code == 200
    assert ask(api, tokens, "lagi").status_code == 429
    assert SENTINEL not in caplog.text
    assert "ask_answered" in caplog.text


def test_second_child_gets_the_next_alias(api):
    tokens, *_ = paired(api)
    add_child(api, tokens, nickname="Nara", age_range="16-17")
    model = ScriptedTools([raw(tool_calls=[call("list_children", {})]), raw("Anak B baik.")])
    api.app.state.muse = model
    body = ask(api, tokens, "Nara?").json()
    assert body["answer"] == "Nara baik."
    children = json.loads(model.sent[-1][-1]["content"])
    assert [c["child"] for c in children] == ["Anak A", "Anak B"]
