"""Time online: policy, daily totals, late-night signals, time requests and the family AI."""

from datetime import date, timedelta

from sqlalchemy import create_engine, inspect, text

from app.db.models import Event
from app.llm.base import LLMResult, TransientLLMError
from tests.conftest import auth
from tests.test_devices import paired
from tests.test_risk_pipeline import USAGE

SENTINEL = "Raka-SENTINEL-0812-3456-7890"
SCOPES = ("percakapan", "waktu")


class FamilyMuse:
    """Answers the family AI purposes with fixed, valid output; records what it was sent."""

    def __init__(self, fail: bool = False, recommendation: str = "sebagian"):
        self.fail = fail
        self.recommendation = recommendation
        self.payloads: list[tuple[str, str]] = []

    async def complete_json(self, *, purpose, system, user, schema, **kw):
        self.payloads.append((purpose, user))
        if self.fail:
            raise TransientLLMError("HTTP 503", status=503)
        data = {
            "time_advice": {
                "summary_for_parent": "Anak meminta waktu untuk tugas kelompok.",
                "recommendation": self.recommendation,
                "suggested_minutes": 90,
                "rationale": "Masih ada waktu sebelum jam tidur.",
            },
            "digest": {
                "headline": "Minggu yang cukup seimbang",
                "summary": "Waktu online stabil, dan ada satu malam lewat jam tidur.",
                "highlights": ["Video paling banyak dipakai.", "Satu permintaan tambahan waktu."],
                "conversation_starters": [
                    "Video apa yang paling seru minggu ini?",
                    "Apa yang bikin susah berhenti main malam itu?",
                    "Mau pilih jam istirahat bareng?",
                ],
                "suggestion": "Sepakati satu malam tanpa ponsel bersama keluarga.",
            },
            "suggest_limits": {
                "daily_limit_school": 140,
                "daily_limit_weekend": 200,
                "video": 50,
                "game": 50,
                "sosial": 40,
                "bedtime_school_start": "21:15",
                "bedtime_weekend_start": "22:15",
                "session_limit_minutes": 35,
                "rationale": "Turun sedikit dari kebiasaan sekarang, supaya mudah dijalani.",
            },
        }[purpose]
        return LLMResult(value=schema.model_validate(data), usage=USAGE, attempts=(USAGE,))


def setup(api, muse=None):
    tokens, child, dev, body = paired(api, scopes=SCOPES)
    api.app.state.muse = muse or FamilyMuse()
    return tokens, child, dev, body


def usage(api, dev, day=None, bedtime=0, minutes=None):
    return api.post(
        "/v1/device/usage",
        json={
            "days": [
                {
                    "day": (day or date.today()).isoformat(),
                    "minutes": minutes or {"video": 70, "game": 30, "sosial": 20, "lain": 10},
                    "bedtime_minutes": bedtime,
                    "longest_session": 45,
                    "session_limits": 1,
                }
            ]
        },
        headers=dev,
    )


# ---------------------------------------------------------------- policy and config


def test_default_policy_follows_age_and_reaches_the_phone(api):
    tokens, child, _dev, body = setup(api)
    got = api.get(f"/v1/children/{child['id']}/screen-policy", headers=auth(tokens)).json()
    assert got["is_default"] is True
    # The test child is 10-12.
    assert got["policy"]["daily_limit_school"] == 120
    assert body["config"]["screen_policy"]["daily_limit_school"] == 120


def test_saved_policy_is_validated_and_sent_to_the_phone(api):
    tokens, child, dev, _ = setup(api)
    policy = api.get(f"/v1/children/{child['id']}/screen-policy", headers=auth(tokens)).json()
    policy["policy"]["daily_limit_school"] = 90
    policy["policy"]["always_allowed"] = ["com.example.study"]
    put = api.put(
        f"/v1/children/{child['id']}/screen-policy", json=policy["policy"], headers=auth(tokens)
    )
    assert put.status_code == 200 and put.json()["is_default"] is False
    assert (
        api.get("/v1/device/config", headers=dev).json()["screen_policy"]["daily_limit_school"]
        == 90
    )
    bad = {**policy["policy"], "session": {"nudge_minutes": 50, "limit_minutes": 40}}
    assert (
        api.put(
            f"/v1/children/{child['id']}/screen-policy", json=bad, headers=auth(tokens)
        ).status_code
        == 422
    )


def test_no_policy_on_the_phone_without_the_scope(api):
    _t, _c, dev, body = paired(api, scopes=("percakapan",))
    assert body["config"]["screen_policy"] is None
    assert usage(api, dev).status_code == 403


# ---------------------------------------------------------------- usage


def test_usage_is_upserted_per_day_and_merged(api):
    tokens, child, dev, _ = setup(api)
    assert usage(api, dev).status_code == 204
    assert (
        usage(api, dev, minutes={"video": 80, "game": 30, "sosial": 20, "lain": 10}).status_code
        == 204
    )
    days = api.get(f"/v1/children/{child['id']}/usage?days=7", headers=auth(tokens)).json()
    assert len(days) == 1 and days[0]["minutes"]["video"] == 80 and days[0]["total"] == 140


def test_usage_rejects_app_names_and_old_days(api):
    _t, _c, dev, _ = setup(api)
    bad = {"days": [{"day": date.today().isoformat(), "minutes": {"com.video.app": 10}}]}
    assert api.post("/v1/device/usage", json=bad, headers=dev).status_code == 422
    assert usage(api, dev, day=date.today() - timedelta(days=9)).status_code == 422


def test_late_night_is_an_event_once(api, db_url):
    _t, _child, dev, _ = setup(api)
    usage(api, dev, bedtime=25)
    usage(api, dev, bedtime=40)
    with create_engine(db_url).connect() as conn:
        rows = conn.execute(
            text(
                "SELECT kind, level FROM event WHERE kind LIKE '%malam%' OR kind LIKE 'jam_tidur%'"
            )
        ).all()
    assert rows == [("jam_tidur_terlewati", "perhatian")]


def test_late_night_with_support_is_stronger(api, db_url):
    _t, child, dev, _ = setup(api)
    from app.db.base import session_factory

    with session_factory(db_url)() as db:
        import uuid

        db.add(
            Event(child_id=uuid.UUID(child["id"]), kind="dukungan_dibutuhkan", level="perhatian")
        )
        db.commit()
    usage(api, dev, bedtime=30)
    with create_engine(db_url).connect() as conn:
        kinds = [k for (k,) in conn.execute(text("SELECT kind FROM event"))]
    assert "larut_malam_dan_dukungan" in kinds and "jam_tidur_terlewati" not in kinds


# ---------------------------------------------------------------- time requests


def ask_time(api, dev, reason="buat tugas kelompok", minutes=30):
    return api.post(
        "/v1/device/time-requests?wait=true",
        json={
            "minutes": minutes,
            "reason": reason,
            "context": {
                "used_today": 120,
                "limit_today": 120,
                "category": "video",
                "minutes_to_bedtime": 100,
            },
        },
        headers=dev,
    )


def test_time_request_gets_advice_and_a_decision_reaches_the_phone(api):
    tokens, child, dev, _body = setup(api)
    resp = ask_time(api, dev)
    assert resp.status_code == 201, resp.text
    out = resp.json()
    assert out["status"] == "menunggu" and out["advice"]["recommendation"] == "sebagian"
    # The model's minutes are capped at what the child asked for.
    assert out["advice"]["suggested_minutes"] == 30 and out["advice"]["source"] == "model"
    listed = api.get(f"/v1/children/{child['id']}/time-requests", headers=auth(tokens)).json()
    assert listed[0]["id"] == out["id"]
    decided = api.post(
        f"/v1/time-requests/{out['id']}/decision",
        json={"approve": True, "minutes": 20},
        headers=auth(tokens),
    )
    assert decided.status_code == 200 and decided.json()["granted_minutes"] == 20
    again = api.post(
        f"/v1/time-requests/{out['id']}/decision", json={"approve": False}, headers=auth(tokens)
    )
    assert again.status_code == 409
    mine = api.get("/v1/device/time-requests", headers=dev).json()
    assert mine[0]["status"] == "diizinkan"


def test_time_request_reason_is_masked_before_storage_and_the_model(api, db_url):
    _t, _child, dev, _ = setup(api)
    muse = api.app.state.muse
    resp = ask_time(api, dev, reason=f"aku Kit, chat {SENTINEL} soal tugas")
    assert resp.status_code == 201
    assert "0812" not in resp.text and "Kit" not in resp.json()["reason"]
    assert all("0812" not in user and "Kit," not in user for _p, user in muse.payloads)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for table in inspect(engine).get_table_names():
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                assert "0812-3456-7890" not in str(row), table


def test_time_advice_falls_back_to_a_rule(api):
    _t, _c, dev, _ = setup(api, muse=FamilyMuse(fail=True))
    advice = ask_time(api, dev).json()["advice"]
    assert advice["source"] == "template" and advice["recommendation"] == "izinkan"


def test_advice_template_respects_bedtime():
    from app.family.ai import advice_template

    assert advice_template({"minutes": 30, "minutes_to_bedtime": 0}, "id").recommendation == "tunda"
    part = advice_template({"minutes": 30, "minutes_to_bedtime": 10}, "id")
    assert part.recommendation == "sebagian" and part.suggested_minutes == 10
    assert (
        advice_template({"minutes": 30, "minutes_to_bedtime": 120}, "en").recommendation
        == "izinkan"
    )


def test_another_guardian_cannot_decide(api):
    _tokens, _child, dev, _ = setup(api)
    req = ask_time(api, dev).json()
    from tests.conftest import register

    other = register(api, email="lain@example.com")
    assert (
        api.post(
            f"/v1/time-requests/{req['id']}/decision", json={"approve": True}, headers=auth(other)
        ).status_code
        == 404
    )


# ---------------------------------------------------------------- digest and suggestion


def test_digest_reads_aggregates_only(api):
    tokens, child, dev, _ = setup(api)
    usage(api, dev, bedtime=20)
    ask_time(api, dev, reason=f"tolong {SENTINEL}")
    resp = api.post(f"/v1/children/{child['id']}/digest", headers=auth(tokens))
    assert resp.status_code == 201 and resp.json()["source"] == "model"
    _purpose, user = next(p for p in api.app.state.muse.payloads if p[0] == "digest")
    assert "SENTINEL" not in user and "Kit" not in user and "reason" not in user
    assert '"bedtime_minutes": 20' in user
    # Within the hour the same digest is returned.
    again = api.post(f"/v1/children/{child['id']}/digest", headers=auth(tokens)).json()
    assert again["created_at"] == resp.json()["created_at"]
    assert api.get(f"/v1/children/{child['id']}/digest", headers=auth(tokens)).json()["output"][
        "headline"
    ]


def test_digest_template_when_the_model_is_down(api):
    tokens, child, dev, _ = setup(api, muse=FamilyMuse(fail=True))
    usage(api, dev)
    out = api.post(f"/v1/children/{child['id']}/digest", headers=auth(tokens)).json()
    assert out["source"] == "template" and len(out["output"]["conversation_starters"]) == 3


def test_suggested_limits_are_a_proposal(api):
    tokens, child, dev, _ = setup(api)
    usage(api, dev)
    resp = api.post(
        f"/v1/children/{child['id']}/screen-policy/suggestion", headers=auth(tokens)
    ).json()
    assert resp["source"] == "model" and resp["policy"]["daily_limit_school"] == 140
    assert resp["policy"]["session"]["limit_minutes"] == 35
    assert resp["policy"]["session"]["nudge_minutes"] < 35
    # Nothing saved until the parent decides.
    got = api.get(f"/v1/children/{child['id']}/screen-policy", headers=auth(tokens)).json()
    assert got["is_default"] is True


def test_suggested_limits_fall_back_to_age_defaults(api):
    tokens, child, _dev, _ = setup(api, muse=FamilyMuse(fail=True))
    resp = api.post(
        f"/v1/children/{child['id']}/screen-policy/suggestion", headers=auth(tokens)
    ).json()
    assert resp["source"] == "template" and resp["policy"]["daily_limit_school"] == 120


def test_family_ai_rejects_punishment_and_links():
    import pytest
    from pydantic import ValidationError

    from app.family.ai import Digest

    base = {
        "headline": "Ringkasan",
        "summary": "Minggu yang tenang.",
        "highlights": ["a", "b"],
        "conversation_starters": ["x", "y", "z"],
        "suggestion": "Sita ponselnya seminggu.",
    }
    with pytest.raises(ValidationError):
        Digest.model_validate(base)
    with pytest.raises(ValidationError):
        Digest.model_validate({**base, "suggestion": "Baca di www.contoh.com"})


def test_erasing_the_child_erases_time_data(api, db_url):
    tokens, child, dev, _ = setup(api)
    usage(api, dev)
    ask_time(api, dev)
    api.post(f"/v1/children/{child['id']}/digest", headers=auth(tokens))
    assert api.delete(f"/v1/children/{child['id']}/data", headers=auth(tokens)).status_code == 204
    with create_engine(db_url).connect() as conn:
        for table in ("usage_day", "time_request", "family_digest", "screen_policy"):
            assert conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one() == 0, table
