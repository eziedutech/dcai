"""POST /v1/messages/analyze end to end with fake models: consent gate, rising level,
events, and the privacy claim that no message text reaches the database or the response."""

from sqlalchemy import create_engine, inspect, text

from tests.conftest import auth, register
from tests.test_children_consent import add_child, consent
from tests.test_risk_pipeline import KeywordScreening, ScriptedReasoning

SENTINEL = "SENTINEL-TEKS-ANAK-91c2"


def setup(api, scopes=("percakapan",)):
    tokens = register(api)
    child = add_child(api, tokens, nickname="Kit")
    if scopes:
        consent(api, tokens, child["id"], scopes=list(scopes))
    api.app.state.openweights = KeywordScreening()
    api.app.state.muse = ScriptedReasoning([40, 70])
    api.app.state.analyzers = None
    return tokens, child


def send(api, tokens, child, text_, conversation_id=None, sender="contact"):
    body = {
        "child_id": child["id"],
        "channel": "game_chat",
        "contact_known": False,
        "sender": sender,
        "text": text_,
    }
    if conversation_id:
        body["conversation_id"] = conversation_id
    return api.post("/v1/messages/analyze", json=body, headers=auth(tokens))


def test_analysis_needs_consent(api):
    tokens, child = setup(api, scopes=())
    assert send(api, tokens, child, "halo").status_code == 403
    consent(api, tokens, child["id"], scopes=["keyboard"])
    assert send(api, tokens, child, "halo").status_code == 403


def test_level_rises_and_events_are_recorded(api, db_url):
    tokens, child = setup(api)
    first = send(api, tokens, child, "halo, main yuk").json()
    cid = first["conversation_id"]
    second = send(api, tokens, child, "aku kasih koin", cid).json()
    third = send(api, tokens, child, "tapi rahasia ya, pindah ke aplikasi lain", cid).json()

    assert [first["level"], third["level"]] == ["aman", "mendesak"]
    assert first["risk_score"] <= second["risk_score"] <= third["risk_score"]
    assert third["is_estimate"] is True
    assert third["message_index"] == 3
    with create_engine(db_url).connect() as conn:
        kinds = [k for (k,) in conn.execute(text("SELECT kind FROM event ORDER BY created_at"))]
        rows = conn.execute(text("SELECT COUNT(*) FROM risk_assessment")).scalar_one()
    assert kinds.count("risiko_naik") == 2
    assert rows >= 3


def test_child_sharing_data_is_an_event_without_the_value(api, db_url):
    tokens, child = setup(api)
    out = send(api, tokens, child, "nomorku 0812-0000-1234", sender="child").json()
    assert out["masked_kinds"] == ["TELEPON"]
    with create_engine(db_url).connect() as conn:
        kinds = {k for (k,) in conn.execute(text("SELECT kind FROM event"))}
    assert "data_pribadi_dibagikan" in kinds


def test_no_message_text_in_database_or_response(api, db_url):
    tokens, child = setup(api)
    cid = None
    for msg in (f"halo {SENTINEL}", f"rahasia ya {SENTINEL}", f"pindah {SENTINEL} 0812-0000-1234"):
        resp = send(api, tokens, child, msg, cid)
        assert resp.status_code == 200
        assert SENTINEL not in resp.text and "0812" not in resp.text
        cid = resp.json()["conversation_id"]

    engine = create_engine(db_url)
    insp = inspect(engine)
    with engine.connect() as conn:
        for table in insp.get_table_names():
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                for value in row:
                    assert SENTINEL not in str(value), table
                    assert "0812-0000-1234" not in str(value), table


def test_another_guardians_conversation_is_not_found(api):
    tokens, child = setup(api)
    cid = send(api, tokens, child, "halo").json()["conversation_id"]
    other = register(api, email="lain@example.com")
    other_child = add_child(api, other)
    consent(api, other, other_child["id"])
    assert send(api, other, other_child, "halo", cid).status_code == 404


def test_window_rebuilt_after_restart_keeps_the_score(api):
    tokens, child = setup(api)
    cid = send(api, tokens, child, "rahasia ya, pindah ke aplikasi lain").json()
    assert cid["level"] == "mendesak"
    api.app.state.analyzers = None  # what a restart does to the in-memory windows
    after = send(api, tokens, child, "halo", cid["conversation_id"]).json()
    assert after["level"] == "mendesak"
