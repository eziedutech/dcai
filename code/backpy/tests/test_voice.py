"""The device voice route: a WAV is transcribed, the transcript is masked and assessed
like any message, and neither the audio nor the transcript reaches the database or a log."""

import logging

from sqlalchemy import create_engine, inspect, text

from app.voice.transcribe import Transcript
from tests.test_devices import THREAD, paired
from tests.test_risk_pipeline import KeywordScreening, ScriptedReasoning

SENTINEL = "SENTINEL-SUARA-ANAK-3b9f"


class FakeVoice:
    """Stands in for Muse Voice: returns scripted transcripts, records what it was given."""

    def __init__(self, text: str, fail: bool = False):
        self.text = text
        self.fail = fail
        self.calls = 0

    async def transcribe(self, audio_wav: bytes, *, timeout: float = 60.0) -> Transcript:
        self.calls += 1
        if self.fail:
            from app.voice.transcribe import VoiceUnavailable

            raise VoiceUnavailable("boom")
        return Transcript(text=self.text, audio_seconds=3.0, cost_usd=0.00015)


def setup(api, scopes=("percakapan", "suara"), transcript="halo"):
    _t, _c, dev, _b = paired(api, scopes=scopes)
    api.app.state.openweights = KeywordScreening()
    api.app.state.muse = ScriptedReasoning([40, 70])
    api.app.state.analyzers = None
    api.app.state.worker = None
    api.app.state.voice = FakeVoice(transcript)
    return dev


def post_voice(api, dev, audio=b"RIFFfake-wav-bytes", **form):
    data = {
        "thread_key": THREAD,
        "app": "com.example.gamechat",
        "channel": "game_chat",
        "contact_known": "false",
        "sender": "contact",
    }
    data.update(form)
    return api.post(
        "/v1/device/voice?wait=true",
        data=data,
        files={"audio": ("note.wav", audio, "audio/wav")},
        headers=dev,
    )


def test_voice_needs_suara_consent(api):
    dev = setup(api, scopes=("percakapan",))
    assert post_voice(api, dev).status_code == 403


def test_voice_note_is_transcribed_masked_and_assessed(api, db_url):
    dev = setup(api, transcript="kirim foto kamu, pindah ke aplikasi lain")
    resp = post_voice(api, dev)
    assert resp.status_code == 200, resp.text
    out = resp.json()
    assert out["queued"] is False and out["level"] == "waspada" and out["raised"] is True
    assert api.app.state.voice.calls == 1
    with create_engine(db_url).connect() as conn:
        apps = {a for (a,) in conn.execute(text("SELECT app FROM conversation"))}
        assessments = conn.execute(text("SELECT COUNT(*) FROM risk_assessment")).scalar_one()
    assert apps == {"com.example.gamechat"} and assessments >= 1


def test_silent_note_is_accepted_without_assessment(api, db_url):
    dev = setup(api, transcript="   ")
    out = post_voice(api, dev).json()
    assert out["queued"] is True and out.get("level") is None
    with create_engine(db_url).connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM risk_assessment")).scalar_one() == 0


def test_transcription_failure_is_502(api):
    dev = setup(api)
    api.app.state.voice = FakeVoice("x", fail=True)
    assert post_voice(api, dev).status_code == 502


def test_voice_unconfigured_is_503(api):
    dev = setup(api)
    api.app.state.voice = None
    assert post_voice(api, dev).status_code == 503


def test_no_audio_or_transcript_in_db_or_logs(api, db_url, caplog):
    caplog.set_level(logging.DEBUG)
    dev = setup(api, transcript=f"rahasia {SENTINEL} 0812-0000-1234")
    resp = post_voice(api, dev, audio=f"RIFF{SENTINEL}".encode())
    assert resp.status_code == 200
    assert SENTINEL not in resp.text and "0812" not in resp.text
    assert SENTINEL not in caplog.text and "0812" not in caplog.text
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for table in inspect(engine).get_table_names():
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                assert SENTINEL not in str(row) and "0812-0000-1234" not in str(row), table


def test_too_large_is_413(api):
    dev = setup(api)
    from app.api.devices import VOICE_MAX_BYTES

    assert post_voice(api, dev, audio=b"x" * (VOICE_MAX_BYTES + 1)).status_code == 413
