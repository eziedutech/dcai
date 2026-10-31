from sqlalchemy import create_engine, text

from app.consent.texts import CURRENT
from tests.conftest import auth, register


def add_child(api, tokens, nickname="Kit", age_range="10-12"):
    resp = api.post(
        "/v1/children", json={"nickname": nickname, "age_range": age_range}, headers=auth(tokens)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def consent(api, tokens, child_id, scopes=("percakapan",), action="grant", version=None):
    return api.post(
        "/v1/consents",
        json={
            "child_id": child_id,
            "text_version": version or CURRENT.version,
            "action": action,
            "scopes": list(scopes),
        },
        headers=auth(tokens),
    )


def test_demo_path_register_add_child_consent(api, db_url):
    """Spec day 2 definition of done: a parent registers, adds a child, gives consent."""
    tokens = register(api)
    child = add_child(api, tokens)
    assert child["consent_scopes"] == []

    resp = consent(api, tokens, child["id"], scopes=["percakapan", "keyboard"])
    assert resp.status_code == 201
    record = resp.json()
    assert record["text_version"] == CURRENT.version
    assert record["age_range"] == "10-12"

    listed = api.get("/v1/children", headers=auth(tokens)).json()
    assert listed[0]["consent_scopes"] == ["keyboard", "percakapan"]

    # Read back from the source, not from the response.
    with create_engine(db_url).connect() as conn:
        rows = conn.execute(text("SELECT action, text_version FROM consent_record")).all()
        actions = conn.execute(text("SELECT action FROM audit_log ORDER BY created_at")).all()
    assert rows == [("grant", CURRENT.version)]
    assert [a for (a,) in actions] == ["guardian_registered", "child_added", "consent_grant"]


def test_revoke_is_a_new_record(api):
    tokens = register(api)
    child = add_child(api, tokens)
    consent(api, tokens, child["id"], scopes=["percakapan", "keyboard"])
    consent(api, tokens, child["id"], scopes=["keyboard"], action="revoke")

    history = api.get(f"/v1/children/{child['id']}/consents", headers=auth(tokens)).json()
    listed = api.get("/v1/children", headers=auth(tokens)).json()

    assert [h["action"] for h in history] == ["grant", "revoke"]
    assert listed[0]["consent_scopes"] == ["percakapan"]


def test_consent_requires_current_text_version(api):
    tokens = register(api)
    child = add_child(api, tokens)
    assert consent(api, tokens, child["id"], version="1999-01-01.1").status_code == 422


def test_consent_text_is_public(api):
    resp = api.get("/v1/consents/text")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == CURRENT.version
    assert set(body["scopes"]) == {
        "percakapan",
        "keyboard",
        "gambar",
        "domain",
        "waktu",
        "layar",
        "sekolah",
    }
    # Voice was removed: it is not offered and its paragraph is gone from the text.
    assert "suara" not in body["scopes"]
    assert "Suara:" not in body["id"] and "- Voice:" not in body["en"]
    # The school scope (proposal 0004) is offered, with its aggregate-only paragraph.
    assert "sekolah" in body["scopes"]
    assert "Sekolah (opsional)" in body["id"] and "School (optional)" in body["en"]
    for word in ("memonitor", "memantau", "mengawasi", "memata-matai", "spyware"):
        assert word not in body["id"].lower()
    # The phone-wide text says what a child always sees and what never leaves the phone.
    assert "notifikasi tetap" in body["id"] and "tidak pernah dikirim" in body["id"]


def test_old_text_version_can_be_revoked_but_not_granted(api):
    from app.consent.texts import V1

    tokens = register(api)
    child = add_child(api, tokens)
    assert consent(api, tokens, child["id"], version=V1.version).status_code == 409
    granted = consent(api, tokens, child["id"], scopes=["percakapan", "gambar"])
    assert granted.status_code == 201
    revoked = consent(
        api, tokens, child["id"], scopes=["gambar"], action="revoke", version=V1.version
    )
    assert revoked.status_code == 201
    listed = api.get("/v1/children", headers=auth(tokens)).json()
    assert listed[0]["consent_scopes"] == ["percakapan"]


def test_current_text_matches_the_build_for_images_and_text_sources():
    """The build reads screen text across any app (accessibility, proposal 0002), the dcAI
    keyboard and chat notifications, and judges images on the phone without sending them.
    V2 had promised to send some images at a small size; CURRENT does not."""
    from app.consent.texts import V2

    assert CURRENT.version != V2.version
    for body in (CURRENT.id, CURRENT.en):
        assert "ukuran kecil" not in body and "small size" not in body
    assert "gambar dinilai di ponsel dan tidak pernah dikirim" in CURRENT.id
    assert "images are judged on the phone and never sent" in CURRENT.en
    # Screen reading across apps is named again, with its transparency promise.
    assert "teks yang tampil di layar aplikasi apa pun" in CURRENT.id
    assert "text shown on screen in any app" in CURRENT.en
    assert "tangkapan layar tidak pernah dikirim" in CURRENT.id
    assert "screenshot is never sent" in CURRENT.en


def test_guardian_cannot_touch_another_guardians_child(api):
    alice = register(api, email="a@example.com")
    bob = register(api, email="b@example.com")
    child = add_child(api, alice)

    assert api.get("/v1/children", headers=auth(bob)).json() == []
    assert consent(api, bob, child["id"]).status_code == 404
    assert api.get(f"/v1/children/{child['id']}/consents", headers=auth(bob)).status_code == 404
    assert api.delete(f"/v1/children/{child['id']}/data", headers=auth(bob)).status_code == 404
    # Still there for its own guardian.
    assert len(api.get("/v1/children", headers=auth(alice)).json()) == 1


def test_delete_child_data_cascades_and_is_audited(api, db_url):
    tokens = register(api)
    child = add_child(api, tokens)
    consent(api, tokens, child["id"])
    with create_engine(db_url).begin() as conn:
        conn.execute(
            text(
                "INSERT INTO conversation (id, child_id, channel, started_at) "
                "VALUES ('c0000000000000000000000000000001', :cid, 'dm', '2026-10-26 00:00:00')"
            ),
            {"cid": child["id"].replace("-", "")},
        )
        conn.execute(
            text(
                "INSERT INTO event (id, child_id, kind, level, created_at) VALUES "
                "('e0000000000000000000000000000001', :cid, 'risiko_naik', 'perhatian', "
                "'2026-10-26 00:00:00')"
            ),
            {"cid": child["id"].replace("-", "")},
        )

    resp = api.delete(f"/v1/children/{child['id']}/data", headers=auth(tokens))

    assert resp.status_code == 204
    with create_engine(db_url).connect() as conn:
        for table in ("child_profile", "consent_record", "conversation", "event"):
            assert conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one() == 0, table
        audit = conn.execute(
            text("SELECT target FROM audit_log WHERE action = 'child_data_deleted'")
        ).scalar_one()
    assert audit == child["id"]
    assert api.get("/v1/children", headers=auth(tokens)).json() == []


def test_rename_child(api):
    tokens = register(api)
    child = add_child(api, tokens, nickname="Anak 1")
    resp = api.patch(
        f"/v1/children/{child['id']}", json={"nickname": "Bintang"}, headers=auth(tokens)
    )
    assert resp.status_code == 200 and resp.json()["nickname"] == "Bintang"
    assert api.get("/v1/children", headers=auth(tokens)).json()[0]["nickname"] == "Bintang"
    # Another guardian cannot rename this child.
    other = register(api, email="lain@example.com")
    assert (
        api.patch(
            f"/v1/children/{child['id']}", json={"nickname": "X"}, headers=auth(other)
        ).status_code
        == 404
    )


def test_clear_history_keeps_child_consent_and_phones(api, db_url):
    import uuid as _uuid

    from app.db.base import session_factory
    from app.db.models import Conversation, Event, ImageSignal, Insight, RiskAssessment

    tokens = register(api)
    child = add_child(api, tokens)
    consent(api, tokens, child["id"])
    cid = _uuid.UUID(child["id"])

    with session_factory(db_url)() as db:
        conv = Conversation(child_id=cid, channel="dm")
        db.add(conv)
        db.flush()
        ra = RiskAssessment(
            conversation_id=conv.id,
            score=60,
            level="waspada",
            patterns=[],
            trajectory="stabil",
            rationale="x",
            confidence="sedang",
            model_version="rules",
        )
        db.add(ra)
        db.flush()
        db.add(Insight(assessment_id=ra.id, child_nudge="hati-hati", parent_insight={}))
        db.add(Event(child_id=cid, kind="risiko_naik", level="waspada"))
        db.add(
            ImageSignal(
                child_id=cid,
                trigger="kirim",
                category="teks_pribadi",
                action="dikaburkan",
                score=10,
                model_version="rules",
            )
        )
        db.commit()

    resp = api.delete(f"/v1/children/{child['id']}/history", headers=auth(tokens))
    assert resp.status_code == 204

    with create_engine(db_url).connect() as conn:
        # History is gone, including the rows that cascade from a conversation.
        for table in ("conversation", "risk_assessment", "insight", "event", "image_signal"):
            assert conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one() == 0, table
        # The child and its consent stay.
        assert conn.execute(text("SELECT COUNT(*) FROM child_profile")).scalar_one() == 1
        assert conn.execute(text("SELECT COUNT(*) FROM consent_record")).scalar_one() >= 1
        audit = conn.execute(
            text("SELECT target FROM audit_log WHERE action = 'child_history_cleared'")
        ).scalar_one()
    assert audit == child["id"]

    listed = api.get("/v1/children", headers=auth(tokens)).json()
    assert listed[0]["id"] == child["id"] and "percakapan" in listed[0]["consent_scopes"]
