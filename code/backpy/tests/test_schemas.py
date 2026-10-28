import pytest
from pydantic import ValidationError

from app.guide.schemas import GuideOutput
from app.risk.schemas import Level, RiskAssessment, level_for


def risk(**over):
    base = {
        "risk_score": 65,
        "level": "waspada",
        "patterns_observed": ["meminta_kerahasiaan", "pindah_kanal"],
        "trajectory": {"status": "meningkat", "reason": "Ajakan pindah kanal muncul."},
        "rationale_for_parent": "Ada permintaan merahasiakan obrolan dan ajakan pindah aplikasi.",
        "confidence": "sedang",
    }
    base.update(over)
    return base


def guide(**over):
    base = {
        "child_nudge": "Obrolan ini tidak perlu dirahasiakan. Ceritakan ke orang tuamu.",
        "parent_insight": {
            "what_we_see": "Pola permintaan kerahasiaan dari kontak yang baru dikenal.",
            "why_it_matters": "Kerahasiaan sering menjadi langkah awal pendekatan yang berisiko.",
            "conversation_starters": [
                "Siapa teman baru di game?",
                "Apa yang seru?",
                "Ada yang bikin bingung?",
            ],
            "do": ["Dengarkan dulu tanpa menghakimi."],
            "dont": ["Jangan langsung menyita ponsel."],
        },
        "micro_lesson": None,
    }
    base.update(over)
    return base


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0, Level.AMAN),
        (29, Level.AMAN),
        (30, Level.PERHATIAN),
        (59, Level.PERHATIAN),
        (60, Level.WASPADA),
        (84, Level.WASPADA),
        (85, Level.MENDESAK),
        (100, Level.MENDESAK),
    ],
)
def test_level_bands(score, level):
    assert level_for(score) == level


def test_valid_assessment():
    assert RiskAssessment.model_validate(risk()).level == Level.WASPADA


@pytest.mark.parametrize(
    "over",
    [
        {"risk_score": 101},
        {"level": "perhatian"},  # does not match 65
        {"patterns_observed": ["pindah_kanal", "pindah_kanal"]},
        {"patterns_observed": ["daftar_kalimat"]},
        {"confidence": "pasti"},
        {"rationale_for_parent": "x" * 401},
        {"extra_field": 1},
    ],
)
def test_invalid_assessment(over):
    with pytest.raises(ValidationError):
        RiskAssessment.model_validate(risk(**over))


def test_emdash_cleaned_from_model_text():
    dash = "\u2014"
    r = RiskAssessment.model_validate(
        risk(rationale_for_parent=f"Pola naik {dash} perlu dibicarakan.")
    )
    assert dash not in r.rationale_for_parent
    assert r.rationale_for_parent == "Pola naik, perlu dibicarakan."


def test_surveillance_wording_rejected():
    with pytest.raises(ValidationError):
        RiskAssessment.model_validate(risk(rationale_for_parent="Terus memonitor anak."))


def test_valid_guidance():
    out = GuideOutput.model_validate(guide())
    assert out.micro_lesson is None
    assert len(out.parent_insight.conversation_starters) == 3


@pytest.mark.parametrize(
    "nudge",
    [
        "Satu. Dua. Tiga.",
        "Hubungi 0812 3456 7890 sekarang.",
        "Buka https://contoh.test untuk bantuan.",
        "Lihat bantuan.com ya.",
    ],
)
def test_invalid_child_nudge(nudge):
    with pytest.raises(ValidationError):
        GuideOutput.model_validate(guide(child_nudge=nudge))


def test_three_starters_exactly():
    data = guide()
    data["parent_insight"]["conversation_starters"] = ["a?", "b?"]
    with pytest.raises(ValidationError):
        GuideOutput.model_validate(data)


def test_micro_lesson_is_required_but_nullable():
    data = guide()
    del data["micro_lesson"]
    with pytest.raises(ValidationError):
        GuideOutput.model_validate(data)
    data["micro_lesson"] = {
        "title": "Rahasia yang baik",
        "body": "Rahasia yang membuatmu tidak nyaman boleh diceritakan.",
    }
    assert GuideOutput.model_validate(data).micro_lesson is not None


def test_schemas_export_json_schema():
    for model in (RiskAssessment, GuideOutput):
        schema = model.model_json_schema()
        assert schema["additionalProperties"] is False


@pytest.mark.parametrize(
    ("raw", "clean_text"),
    [
        ("akhir akhir ini dia hati hati", "akhir-akhir ini dia hati-hati"),
        ("Kata kata itu", "Kata-kata itu"),
        ("hati-hati sudah benar", "hati-hati sudah benar"),
        ("kata kita", "kata kita"),
    ],
)
def test_reduplication_hyphen_restored(raw, clean_text):
    from app.text import clean

    assert clean(raw) == clean_text
