from sqlalchemy import create_engine, text

from app.consent.texts import CURRENT
from tests.conftest import auth, register


def add_child(api, tokens, nickname="Kit", age_range="11-13"):
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
    assert record["age_range"] == "11-13"

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
    assert set(body["scopes"]) == {"percakapan", "keyboard"}
    for word in ("memonitor", "memantau", "mengawasi", "memata-matai"):
        assert word not in body["id"].lower()


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
