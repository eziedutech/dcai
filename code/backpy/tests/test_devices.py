"""The child's phone: pairing, device tokens, configuration, service state, flagged
messages, image labels and confirmed false detections, all through the real API."""

import time
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, inspect, text

from tests.conftest import auth, register
from tests.test_children_consent import add_child, consent
from tests.test_risk_pipeline import KeywordScreening, ScriptedReasoning

SENTINEL = "SENTINEL-LAYAR-ANAK-7f30"
THREAD = "thread-key-0123456789abcdef"


def setup(api, scopes=("percakapan", "gambar")):
    tokens = register(api)
    child = add_child(api, tokens, nickname="Kit")
    if scopes:
        assert consent(api, tokens, child["id"], scopes=list(scopes)).status_code == 201
    api.app.state.openweights = KeywordScreening()
    api.app.state.muse = ScriptedReasoning([40, 70])
    api.app.state.analyzers = None
    return tokens, child


def pairing_code(api, tokens, child):
    resp = api.post(f"/v1/children/{child['id']}/pairing-codes", headers=auth(tokens))
    assert resp.status_code == 201, resp.text
    return resp.json()["code"]


def pair(api, code, name="Ponsel Kit"):
    return api.post(
        "/v1/device/pair",
        json={"code": code, "device_name": name, "platform": "android", "app_version": "0.1.0"},
    )


def paired(api, scopes=("percakapan", "gambar")):
    tokens, child = setup(api, scopes)
    resp = pair(api, pairing_code(api, tokens, child))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return tokens, child, {"Authorization": f"Bearer {body['device_token']}"}, body


def message(api, dev, text_, sender="contact", wait=True, thread=THREAD):
    return api.post(
        "/v1/device/messages" + ("?wait=true" if wait else ""),
        json={
            "thread_key": thread,
            "app": "com.example.gamechat",
            "channel": "game_chat",
            "contact_known": False,
            "sender": sender,
            "text": text_,
        },
        headers=dev,
    )


# ------------------------------------------------------------------ pairing


def test_pairing_needs_consent_first(api):
    tokens, child = setup(api, scopes=())
    resp = api.post(f"/v1/children/{child['id']}/pairing-codes", headers=auth(tokens))
    assert resp.status_code == 409


def test_pair_returns_token_once_and_config(api, db_url):
    tokens, child, _dev, body = paired(api)
    assert body["device_token"].startswith("dcd_")
    cfg = body["config"]
    assert cfg["scopes"] == ["gambar", "percakapan"]
    assert cfg["age_range"] == "10-12" and cfg["child_nickname"] == "Kit"
    assert cfg["consent_version"]

    with create_engine(db_url).connect() as conn:
        stored = conn.execute(text("SELECT token_hash FROM device")).scalar_one()
        audit = [a for (a,) in conn.execute(text("SELECT action FROM audit_log"))]
    assert body["device_token"] not in stored and len(stored) == 64
    assert "pairing_code_created" in audit and "device_paired" in audit

    devices = api.get(f"/v1/children/{child['id']}/devices", headers=auth(tokens)).json()
    assert [d["name"] for d in devices] == ["Ponsel Kit"]
    assert devices[0]["revoked"] is False


def test_pairing_code_is_single_use_and_forgiving_to_type(api):
    tokens, child = setup(api)
    code = pairing_code(api, tokens, child)
    assert len(code) == 9 and code[4] == "-"
    assert pair(api, code.replace("-", "").lower()).status_code == 201
    assert pair(api, code).status_code == 400  # used
    assert pair(api, "ABCD-EFGH").status_code == 400  # unknown, same answer


def test_expired_pairing_code_is_refused(api, db_url):
    tokens, child = setup(api)
    code = pairing_code(api, tokens, child)
    with create_engine(db_url).begin() as conn:
        conn.execute(text("UPDATE pairing_code SET expires_at = :t"), {"t": "2020-01-01 00:00:00"})
    assert pair(api, code).status_code == 400


# ------------------------------------------------------------------ device auth


def test_device_endpoints_need_a_device_token(api):
    tokens, _child, dev, _ = paired(api)
    assert api.get("/v1/device/config").status_code == 401
    # A guardian's access token is not a device token.
    assert api.get("/v1/device/config", headers=auth(tokens)).status_code == 401
    assert (
        api.get("/v1/device/config", headers={"Authorization": "Bearer dcd_x"}).status_code == 401
    )
    assert api.get("/v1/device/config", headers=dev).status_code == 200


def test_revoked_device_is_locked_out_and_told(api):
    tokens, _child, dev, body = paired(api)
    assert api.delete(f"/v1/devices/{body['device_id']}", headers=auth(tokens)).status_code == 204
    assert api.get("/v1/device/config", headers=dev).status_code == 401
    bus = api.app.state.broker
    events = [e.event for e in bus.since(f"device:{body['device_id']}", "old-0")]
    assert events[-1] == "revoked"


def test_another_guardian_cannot_see_or_revoke_the_device(api):
    _tokens, child, dev, body = paired(api)
    other = register(api, email="lain@example.com")
    assert api.delete(f"/v1/devices/{body['device_id']}", headers=auth(other)).status_code == 404
    assert api.get(f"/v1/children/{child['id']}/devices", headers=auth(other)).status_code == 404
    assert api.get("/v1/device/config", headers=dev).status_code == 200


def test_erasing_the_child_ends_the_device(api, db_url):
    tokens, child, dev, _body = paired(api)
    assert api.delete(f"/v1/children/{child['id']}/data", headers=auth(tokens)).status_code == 204
    assert api.get("/v1/device/config", headers=dev).status_code == 401
    with create_engine(db_url).connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM device")).scalar_one() == 0


# ------------------------------------------------------------------ config and services


def test_withdrawn_scope_reaches_the_phone(api):
    tokens, child, dev, body = paired(api)
    resp = consent(api, tokens, child["id"], scopes=["gambar"], action="revoke")
    assert resp.status_code == 201
    assert api.get("/v1/device/config", headers=dev).json()["scopes"] == ["percakapan"]
    live = api.app.state.broker.since(f"device:{body['device_id']}", "old-0")
    assert live[-1].event == "config" and live[-1].data["scopes"] == ["percakapan"]


def test_screen_reading_scope_reaches_the_phone(api):
    tokens, child, dev, _body = paired(api)
    resp = consent(api, tokens, child["id"], scopes=["layar"])
    assert resp.status_code == 201
    assert "layar" in api.get("/v1/device/config", headers=dev).json()["scopes"]


def test_service_switched_off_is_an_event_for_the_parent(api, db_url):
    tokens, child, dev, _ = paired(api)
    beat = {"app_version": "0.1.0", "services": {"accessibility": True, "notification": True}}
    assert api.post("/v1/device/heartbeat", json=beat, headers=dev).status_code == 200
    beat["services"] = {"accessibility": False}
    api.post("/v1/device/heartbeat", json=beat, headers=dev)
    beat["services"] = {"accessibility": True}
    api.post("/v1/device/heartbeat", json=beat, headers=dev)

    with create_engine(db_url).connect() as conn:
        kinds = [k for (k,) in conn.execute(text("SELECT kind FROM event ORDER BY created_at"))]
    assert kinds == ["perlindungan_dimatikan", "perlindungan_aktif"]
    devices = api.get(f"/v1/children/{child['id']}/devices", headers=auth(tokens)).json()
    assert devices[0]["services"] == {"accessibility": True, "notification": True}
    live = api.app.state.broker.since(f"child:{child['id']}", "old-0")
    assert [e.data["kind"] for e in live if e.event == "event"] == kinds


# ------------------------------------------------------------------ messages


def test_messages_need_conversation_consent(api):
    _tokens, _child, dev, _ = paired(api, scopes=("gambar",))
    assert message(api, dev, "halo").status_code == 403


def test_noise_apps_are_not_conversations(api, db_url):
    _tokens, _child, dev, _ = paired(api)
    resp = api.post(
        "/v1/device/messages?wait=true",
        json={
            "thread_key": THREAD,
            "app": "com.android.systemui",
            "channel": "game_chat",
            "contact_known": False,
            "sender": "contact",
            "text": "halo apa kabar semuanya",
        },
        headers=dev,
    )
    assert resp.status_code == 202, resp.text
    assert resp.json()["conversation_id"] == "" and resp.json()["queued"] is False
    with create_engine(db_url).connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM conversation")).scalar_one() == 0


def test_message_from_phone_is_analysed_per_thread(api, db_url):
    _tokens, _child, dev, _ = paired(api)
    first = message(api, dev, "halo, main yuk").json()
    second = message(api, dev, "kirim foto kamu").json()
    assert first["conversation_id"] == second["conversation_id"]
    assert [first["message_index"], second["message_index"]] == [1, 2]
    assert second["raised"] is True and second["level"] == "waspada"
    assert second["nudge"]["child_nudge"]
    other = message(api, dev, "halo", thread="another-thread-key-0001").json()
    assert other["conversation_id"] != first["conversation_id"]

    with create_engine(db_url).connect() as conn:
        apps = {a for (a,) in conn.execute(text("SELECT app FROM conversation"))}
    assert apps == {"com.example.gamechat"}


def test_phone_never_receives_parent_insight(api):
    _tokens, child, dev, body = paired(api)
    resp = message(api, dev, "kirim foto kamu")
    assert "parent_insight" not in resp.text and "rationale" not in resp.text
    phone = api.app.state.broker.since(f"device:{body['device_id']}", "old-0")
    assert [e.event for e in phone] == ["level", "nudge"]
    # The level carries a reviewed template at once; the model's nudge follows.
    assert phone[0].data["nudge"]["source"] == "template"
    assert phone[0].data["nudge"]["child_nudge"] and phone[0].data["nudge"]["help_channels"]
    for e in phone:
        assert "parent_insight" not in e.data and "rationale_for_parent" not in e.data
    guardian = api.app.state.broker.since(f"child:{child['id']}", "old-0")
    assert {"event", "assessment", "insight"} <= {e.event for e in guardian}


def test_no_screen_text_in_database_response_logs_or_live_updates(api, db_url, caplog):
    import logging

    caplog.set_level(logging.DEBUG)
    _tokens, child, dev, body = paired(api)
    api.app.state.openweights = KeywordScreening(fail_on="pindah")  # the failure path logs
    for msg in (f"halo {SENTINEL}", f"rahasia ya {SENTINEL}", f"pindah {SENTINEL} 0812-0000-1234"):
        resp = message(api, dev, msg)
        assert resp.status_code == 200
        assert SENTINEL not in resp.text and "0812" not in resp.text

    assert any(r.name.startswith("dcai") for r in caplog.records)  # something was logged
    assert SENTINEL not in caplog.text and "0812" not in caplog.text
    bus = api.app.state.broker
    for key in (f"device:{body['device_id']}", f"child:{child['id']}"):
        for e in bus.since(key, "old-0"):
            assert SENTINEL not in e.encode(bus.boot) and "0812" not in e.encode(bus.boot)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for table in inspect(engine).get_table_names():
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                assert SENTINEL not in str(row) and "0812-0000-1234" not in str(row), table


def test_message_without_wait_is_queued_and_analysed_in_background(api, db_url):
    _tokens, _child, dev, _ = paired(api)
    resp = message(api, dev, "kirim foto kamu", wait=False)
    assert resp.status_code == 202
    assert resp.json()["queued"] is True and resp.json()["level"] is None
    engine = create_engine(db_url)
    deadline = time.monotonic() + 5
    count = 0
    while time.monotonic() < deadline:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM insight")).scalar_one()
        if count:
            break
        time.sleep(0.05)
    assert count == 1


def test_too_many_messages_from_one_phone(api):
    from app.ratelimit import RateLimiter

    _tokens, _child, dev, _ = paired(api)
    api.app.state.device_limiter = RateLimiter(per_minute=2)
    assert message(api, dev, "halo").status_code == 200
    assert message(api, dev, "halo").status_code == 200
    resp = message(api, dev, "halo")
    assert resp.status_code == 429 and resp.headers["retry-after"] == "60"


@pytest.mark.parametrize(
    "bad",
    [
        {"thread_key": "short"},
        {"app": "not a package"},
        {"text": ""},
        {"extra": 1},
    ],
)
def test_message_input_is_validated(api, bad):
    _tokens, _child, dev, _ = paired(api)
    body = {
        "thread_key": THREAD,
        "app": "com.example.gamechat",
        "channel": "game_chat",
        "contact_known": False,
        "sender": "contact",
        "text": "halo",
    }
    body.update(bad)
    assert api.post("/v1/device/messages", json=body, headers=dev).status_code == 422


# ------------------------------------------------------------------ images and feedback


def image(api, dev, **over):
    body = {
        "trigger": "percakapan",
        "sender": "contact",
        "category": "seksual",
        "action": "dikaburkan",
        "score": 93,
        "model_version": "nsfw-tflite-test",
    }
    body.update(over)
    return api.post("/v1/device/images", json=body, headers=dev)


def test_image_labels_need_image_consent(api):
    _tokens, _child, dev, _ = paired(api, scopes=("percakapan",))
    assert image(api, dev).status_code == 403


@pytest.mark.parametrize(
    ("over", "event"),
    [
        ({}, "gambar_sensitif"),
        ({"trigger": "situs", "sender": None}, "gambar_sensitif"),
        (
            {"trigger": "dibagikan", "sender": "child", "category": "teks_pribadi"},
            "gambar_data_pribadi",
        ),
        ({"category": "wajah", "action": "ditinjau"}, None),
        ({"category": "aman", "action": "dibiarkan"}, None),
    ],
)
def test_image_label_is_stored_and_becomes_an_event(api, db_url, over, event):
    _tokens, _child, dev, _ = paired(api)
    resp = image(api, dev, **over)
    assert resp.status_code == 201, resp.text
    assert resp.json()["event"] == event
    with create_engine(db_url).connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM image_signal")).scalar_one() == 1
        kinds = [k for (k,) in conn.execute(text("SELECT kind FROM event"))]
    assert kinds == ([event] if event else [])


def test_image_label_links_to_its_conversation(api, db_url):
    _tokens, _child, dev, _ = paired(api)
    cid = message(api, dev, "halo").json()["conversation_id"]
    image(api, dev, thread_key=THREAD)
    with create_engine(db_url).connect() as conn:
        linked = conn.execute(text("SELECT conversation_id FROM image_signal")).scalar_one()
    assert str(linked).replace("-", "") == cid.replace("-", "")


def test_false_detection_is_stored_without_child_or_device(api, db_url):
    _tokens, _child, dev, _ = paired(api)
    body = {
        "kind": "gambar",
        "category": "seksual",
        "score": 87,
        "model_version": "nsfw-tflite-test",
        "verdict": "salah_deteksi",
        "confirmed_by_guardian": True,
    }
    assert api.post("/v1/device/detection-feedback", json=body, headers=dev).status_code == 204
    unconfirmed = {**body, "confirmed_by_guardian": False}
    assert (
        api.post("/v1/device/detection-feedback", json=unconfirmed, headers=dev).status_code == 422
    )
    engine = create_engine(db_url)
    cols = {c["name"] for c in inspect(engine).get_columns("detection_feedback")}
    assert not cols & {"child_id", "device_id", "guardian_id", "conversation_id"}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT score FROM detection_feedback")).scalar_one() == 85


def test_pairing_code_lifetime_comes_from_settings(api, monkeypatch):
    from datetime import datetime

    from app.db.base import utcnow

    tokens, child = setup(api)
    resp = api.post(f"/v1/children/{child['id']}/pairing-codes", headers=auth(tokens)).json()
    left = datetime.fromisoformat(resp["expires_at"]) - utcnow()
    assert timedelta(minutes=9) < left <= timedelta(minutes=10)
