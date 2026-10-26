"""Rule floor and the per-message pipeline, with fake model clients."""

from typing import ClassVar

import pytest

from app.llm import LLMResult, TransientLLMError, Usage
from app.risk.floor import Seen, rule_floor
from app.risk.pipeline import ConversationAnalyzer
from app.risk.schemas import Level, RiskAssessment
from app.risk.stage1 import Stage1Output

USAGE = Usage("fake", "fake-muse", 100, 0, 10, 5, 0.0)


class KeywordScreening:
    """Stage 1 stand-in: labels from keywords in the masked text."""

    RULES: ClassVar[dict[str, str]] = {
        "rahasia": "meminta_kerahasiaan",
        "pindah": "pindah_kanal",
        "foto": "meminta_data_pribadi",
        "koin": "menawarkan_hadiah",
        "sedih": "menyakiti_diri",
    }

    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on
        self.seen_text: list[str] = []

    async def complete_json(self, *, user, **kw):
        self.seen_text.append(user)
        if self.fail_on and self.fail_on in user:
            raise TransientLLMError("HTTP 503", status=503)
        labels = [lab for word, lab in self.RULES.items() if word in user]
        out = Stage1Output(labels=labels, signal=60 if labels else 0)
        return LLMResult(value=out, usage=USAGE, attempts=(USAGE,))


def assessment(score: int, rationale: str = "Ada pola pendekatan yang perlu dibicarakan."):
    from app.risk.schemas import level_for

    return RiskAssessment.model_validate(
        {
            "risk_score": score,
            "level": level_for(score).value,
            "patterns_observed": [],
            "trajectory": {"status": "meningkat", "reason": "Pola bertambah."},
            "rationale_for_parent": rationale,
            "confidence": "sedang",
        }
    )


class ScriptedReasoning:
    def __init__(self, scores: list[int] | None = None, fail: bool = False):
        self.scores = list(scores or [])
        self.fail = fail
        self.calls = 0

    async def complete_json(self, **kw):
        self.calls += 1
        if self.fail:
            raise TransientLLMError("HTTP 503", status=503)
        score = self.scores.pop(0) if self.scores else 40
        return LLMResult(value=assessment(score), usage=USAGE, attempts=(USAGE,))


def analyzer(screening=None, reasoning=None, contact_known=False):
    return ConversationAnalyzer(
        screening=screening or KeywordScreening(),
        reasoning=reasoning or ScriptedReasoning(),
        contact_known=contact_known,
        channel="game_chat",
        age_range="11-13",
        known_names=("Kit",),
    )


# Rule floor


def seen_with(contact=(), child=(), unavailable=0) -> Seen:
    s = Seen()
    s.add("contact", frozenset(contact), True)
    s.add("child", frozenset(child), True)
    s.unavailable = unavailable
    return s


@pytest.mark.parametrize(
    ("contact", "child", "known", "unavailable", "level"),
    [
        ((), (), False, 0, Level.AMAN),
        (("meminta_data_pribadi",), (), False, 0, Level.WASPADA),
        (("meminta_data_pribadi",), (), True, 0, Level.AMAN),
        (("meminta_kerahasiaan", "pindah_kanal"), (), True, 0, Level.MENDESAK),
        (("menekan_mengancam",), (), False, 0, Level.WASPADA),
        (("menekan_mengancam",), (), True, 0, Level.PERHATIAN),
        (("membangun_kedekatan", "menawarkan_hadiah"), (), False, 0, Level.PERHATIAN),
        (("membangun_kedekatan",), (), False, 0, Level.AMAN),
        ((), ("berbagi_data_pribadi",), True, 0, Level.PERHATIAN),
        ((), ("menyakiti_diri",), True, 0, Level.PERHATIAN),
        ((), (), True, 1, Level.PERHATIAN),
    ],
)
def test_rule_floor(contact, child, known, unavailable, level):
    floor = rule_floor(seen_with(contact, child, unavailable), contact_known=known)
    assert floor.level == level


def test_distress_sets_support_flag():
    assert rule_floor(seen_with(child=("menyakiti_diri",)), True).support_needed
    assert not rule_floor(seen_with(child=("perundungan",)), True).support_needed


# Pipeline


async def test_ordinary_chat_never_calls_the_reasoning_model():
    reasoning = ScriptedReasoning()
    a = analyzer(reasoning=reasoning)
    for text in ("halo", "main yuk", "oke jam 4"):
        step = await a.add("contact", text)
    assert reasoning.calls == 0
    assert step.level == Level.AMAN and step.score == 0
    assert step.analysis_available


async def test_score_rises_step_by_step_and_never_falls():
    # Model scores go down later; the final score must not.
    a = analyzer(reasoning=ScriptedReasoning([35, 50, 20, 10]))
    levels = []
    for text in ("halo", "aku kasih koin", "ini rahasia ya", "makasih", "dah"):
        levels.append((await a.add("contact", text)).score)
    assert levels == sorted(levels)
    assert levels[0] == 0 and levels[-1] >= 50


async def test_floor_overrides_a_lower_model_score_and_explains_itself():
    a = analyzer(reasoning=ScriptedReasoning([20, 20]))
    await a.add("contact", "ini rahasia ya")
    step = await a.add("contact", "pindah ke aplikasi lain")
    assert step.level == Level.MENDESAK
    assert step.source == "rules"
    assert "merahasiakan" in step.rationale


async def test_model_outage_falls_back_to_floor_with_low_confidence():
    a = analyzer(reasoning=ScriptedReasoning(fail=True))
    step = await a.add("contact", "kirim foto kamu")
    assert step.level == Level.WASPADA
    assert step.model_version == "rules"
    assert not step.analysis_available
    assert step.confidence == "rendah"


async def test_stage1_outage_shows_perhatian_not_aman():
    a = analyzer(screening=KeywordScreening(fail_on="halo"))
    step = await a.add("contact", "halo")
    assert step.level == Level.PERHATIAN
    assert "tidak tersedia" in step.rationale


async def test_known_names_are_masked_before_any_model():
    screening = KeywordScreening()
    a = analyzer(screening=screening)
    await a.add("contact", "Kit, nomormu 0812-0000-1234?")
    assert "Kit" not in screening.seen_text[0]
    assert "0812" not in screening.seen_text[0]


async def test_message_index_keeps_counting_past_the_window():
    a = analyzer()
    for i in range(14):
        step = await a.add("contact", f"pesan {i}")
    assert step.index == 14
    assert len(a.window) == 10


def test_parent_text_with_a_marker_is_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        assessment(40, rationale="Kontak menyebut [NAMA] berulang kali.")
