"""School module endpoints (proposal 0004): staff auth, classes, and the aggregate
overview with k-anonymity. The overview must never reveal a child's level or identity, and
a small class shows no numbers."""

import uuid

from app.consent.texts import CURRENT
from app.db.base import session_factory
from app.db.models import (
    ChildProfile,
    ClassMembership,
    ConsentRecord,
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
    ids = []
    with session_factory(db_url)() as db:
        g = Guardian(email=f"{uuid.uuid4().hex}@ex.test", name="G", password_hash="h")
        db.add(g)
        db.flush()
        for i, lvl in enumerate(levels):
            c = ChildProfile(guardian_id=g.id, nickname=f"A{i}", age_range="11-13")
            db.add(c)
            db.flush()
            ids.append((g.id, c.id))
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
            # Only children whose parent granted the sekolah scope are counted.
            db.add(
                ConsentRecord(
                    guardian_id=g.id,
                    child_id=c.id,
                    text_version=CURRENT.version,
                    action="grant",
                    scopes=["sekolah"],
                    age_range="11-13",
                )
            )
            db.add(ClassMembership(classroom_id=uuid.UUID(classroom_id), child_id=c.id))
        db.commit()
    return ids


def revoke_sekolah(db_url, guardian_id, child_id):
    with session_factory(db_url)() as db:
        db.add(
            ConsentRecord(
                guardian_id=guardian_id,
                child_id=child_id,
                text_version=CURRENT.version,
                action="revoke",
                scopes=["sekolah"],
                age_range="11-13",
            )
        )
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


def test_parent_joins_only_with_the_sekolah_scope(api):
    from tests.conftest import auth
    from tests.conftest import register as guardian_register
    from tests.test_children_consent import add_child, consent

    tok = register(api)
    room = make_class(api, tok)
    g = guardian_register(api)
    child = add_child(api, g)
    body = {"join_code": room["join_code"]}
    # Without the sekolah scope the join is refused.
    assert (
        api.post(f"/v1/children/{child['id']}/class", json=body, headers=auth(g)).status_code == 403
    )
    consent(api, g, child["id"], scopes=["sekolah"])
    joined = api.post(f"/v1/children/{child['id']}/class", json=body, headers=auth(g))
    assert joined.status_code == 201 and joined.json()["joined"] is True
    # Idempotent, and the class now counts one member.
    assert (
        api.post(f"/v1/children/{child['id']}/class", json=body, headers=auth(g)).status_code == 201
    )
    assert api.get("/v1/school/classes", headers=sauth(tok)).json()[0]["members"] == 1
    # A wrong code is a 404; leaving removes the membership.
    bad = api.post(
        f"/v1/children/{child['id']}/class", json={"join_code": "ZZZZZZ"}, headers=auth(g)
    )
    assert bad.status_code == 404
    cid = joined.json()["classroom_id"]
    assert api.delete(f"/v1/children/{child['id']}/class/{cid}", headers=auth(g)).status_code == 204
    assert api.get("/v1/school/classes", headers=sauth(tok)).json()[0]["members"] == 0


def test_revoking_sekolah_drops_a_child_from_the_count(api, db_url):
    tok = register(api)
    room = make_class(api, tok)
    members = seed(db_url, room["id"], ["aman"] * 4 + ["waspada"])  # 5, all consenting
    ov = api.get(f"/v1/school/classes/{room['id']}/overview", headers=sauth(tok)).json()
    assert ov["suppressed"] is False and ov["total"] == 5
    guardian_id, child_id = members[0]
    revoke_sekolah(db_url, guardian_id, child_id)
    ov2 = api.get(f"/v1/school/classes/{room['id']}/overview", headers=sauth(tok)).json()
    assert ov2["total"] == 4 and ov2["suppressed"] is True  # below k again
