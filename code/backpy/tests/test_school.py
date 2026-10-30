"""School module endpoints (proposal 0004): staff auth, classes, and the aggregate
overview with k-anonymity. The overview must never reveal a child's level or identity, and
a small class shows no numbers."""

import uuid

from app.db.base import session_factory
from app.db.models import (
    ChildProfile,
    ClassMembership,
    Conversation,
    Event,
    Guardian,
    RiskAssessment,
)

_SCORE = {"aman": 0, "perhatian": 30, "waspada": 60, "mendesak": 85}


def register(api, email="bk@example.com", school="SMP Harapan"):
    r = api.post(
        "/v1/school/register",
        json={
            "email": email,
            "password": "kata-sandi-panjang",
            "name": "Bu Sari",
            "school_name": school,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def sauth(tok):
    return {"Authorization": f"Bearer {tok['access_token']}"}


def make_class(api, tok, name="7A"):
    r = api.post("/v1/school/classes", json={"name": name}, headers=sauth(tok))
    assert r.status_code == 201, r.text
    return r.json()


def seed(db_url, classroom_id, levels, support_idx=()):
    with session_factory(db_url)() as db:
        g = Guardian(email=f"{uuid.uuid4().hex}@ex.test", name="G", password_hash="h")
        db.add(g)
        db.flush()
        for i, lvl in enumerate(levels):
            c = ChildProfile(guardian_id=g.id, nickname=f"A{i}", age_range="11-13")
            db.add(c)
            db.flush()
            conv = Conversation(child_id=c.id, channel="dm")
            db.add(conv)
            db.flush()
            db.add(
                RiskAssessment(
                    conversation_id=conv.id,
                    score=_SCORE[lvl],
                    level=lvl,
                    patterns=[],
                    trajectory="stabil",
                    rationale="x",
                    confidence="sedang",
                    model_version="rules",
                )
            )
            if i in support_idx:
                db.add(Event(child_id=c.id, kind="dukungan_dibutuhkan", level=lvl))
            db.add(ClassMembership(classroom_id=uuid.UUID(classroom_id), child_id=c.id))
        db.commit()


def test_register_login_and_me(api):
    tok = register(api)
    assert tok["staff"]["role"] == "kepala" and tok["staff"]["school_id"]
    login = api.post(
        "/v1/school/login", json={"email": "bk@example.com", "password": "kata-sandi-panjang"}
    )
    assert login.status_code == 200
    me = api.get("/v1/school/me", headers=sauth(login.json()))
    assert me.status_code == 200 and me.json()["email"] == "bk@example.com"


def test_a_guardian_token_cannot_reach_staff_endpoints(api):
    from tests.conftest import auth
    from tests.conftest import register as guardian_register

    g = guardian_register(api)
    assert api.get("/v1/school/me", headers=auth(g)).status_code == 401


def test_create_and_list_classes(api):
    tok = register(api)
    created = make_class(api, tok, "7A")
    assert created["join_code"] and created["members"] == 0
    listed = api.get("/v1/school/classes", headers=sauth(tok)).json()
    assert [c["name"] for c in listed] == ["7A"]
    assert "join_code" not in listed[0] or listed[0]["join_code"] is None  # not listed again


def test_small_class_is_suppressed(api, db_url):
    tok = register(api)
    room = make_class(api, tok)
    seed(db_url, room["id"], ["aman", "waspada", "mendesak"])  # 3 < k=5
    ov = api.get(f"/v1/school/classes/{room['id']}/overview", headers=sauth(tok)).json()
    assert ov["total"] == 3 and ov["suppressed"] is True
    assert ov["by_level"] is None and ov["support"] is None


def test_counts_show_at_k_support_at_support_k(api, db_url):
    tok = register(api)
    room = make_class(api, tok)
    # 10 children so the support count also shows; 2 flagged for support.
    levels = ["aman"] * 6 + ["perhatian", "waspada", "mendesak", "mendesak"]
    seed(db_url, room["id"], levels, support_idx=(8, 9))
    ov = api.get(f"/v1/school/classes/{room['id']}/overview", headers=sauth(tok)).json()
    assert ov["suppressed"] is False and ov["total"] == 10
    assert ov["by_level"] == {"aman": 6, "perhatian": 1, "waspada": 1, "mendesak": 2}
    assert ov["support"] == 2


def test_another_school_cannot_see_the_class(api):
    tok = register(api)
    room = make_class(api, tok)
    other = register(api, email="lain@example.com", school="SMP Lain")
    resp = api.get(f"/v1/school/classes/{room['id']}/overview", headers=sauth(other))
    assert resp.status_code == 404
