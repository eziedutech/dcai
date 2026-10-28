import json

import pytest
from pydantic import ValidationError

from app.guide.channels import load_channels
from app.guide.guide import SYSTEM, Situation, guide, help_channels, situation
from app.guide.schemas import GuideOutput
from app.guide.templates import template
from app.llm import LLMResult, TransientLLMError, Usage
from app.risk.schemas import Level

USAGE = Usage("fake", "fake-muse", 100, 0, 10, 5, 0.0)


@pytest.mark.parametrize("sit", list(Situation))
@pytest.mark.parametrize("level", list(Level))
@pytest.mark.parametrize("language", ["id", "en"])
def test_every_template_passes_the_model_schema(sit, level, language):
    out = template(sit, level, language)
    assert len(out.parent_insight.conversation_starters) == 3
    assert (out.micro_lesson is None) == (level == Level.AMAN)


def test_dangerous_invite_situation_fits_the_db_column_and_has_guidance():
    from app.db.models import Insight

    width = Insight.__table__.c.situation.type.length
    assert all(len(s.value) <= width for s in Situation)
    assert f'Situation "{Situation.DANGEROUS_INVITE.value}"' in SYSTEM


@pytest.mark.parametrize("language", ["id", "en"])
def test_dangerous_invite_template_is_its_own_text(language):
    own = template(Situation.DANGEROUS_INVITE, Level.WASPADA, language)
    general = template(Situation.GENERAL, Level.WASPADA, language)
    assert own.child_nudge != general.child_nudge
    assert own.micro_lesson is not None
    assert help_channels(Level.WASPADA, Situation.DANGEROUS_INVITE, language)
    assert help_channels(Level.PERHATIAN, Situation.DANGEROUS_INVITE, language) == ()


def test_urgent_template_tells_parent_to_keep_evidence_and_not_confront():
    out = template(Situation.APPROACH, Level.MENDESAK, "id")
    assert "bukti" in out.parent_insight.do[0]
    assert "langsung" in out.parent_insight.dont[0]


@pytest.mark.parametrize(
    ("contact", "child", "support", "expected"),
    [
        ({"meminta_kerahasiaan"}, set(), False, Situation.APPROACH),
        ({"perundungan"}, set(), False, Situation.BULLIED),
        (set(), {"perundungan"}, False, Situation.BULLYING),
        (set(), {"berbagi_data_pribadi"}, False, Situation.SHARED_DATA),
        ({"meminta_kerahasiaan"}, {"menyakiti_diri"}, True, Situation.DISTRESS),
        ({"ajakan_berbahaya"}, set(), False, Situation.DANGEROUS_INVITE),
        (set(), {"ajakan_berbahaya"}, False, Situation.DANGEROUS_INVITE),
        ({"ajakan_berbahaya", "perundungan"}, set(), False, Situation.DANGEROUS_INVITE),
        (set(), {"ajakan_berbahaya", "kata_kasar"}, False, Situation.DANGEROUS_INVITE),
        ({"ajakan_berbahaya", "pindah_kanal"}, set(), False, Situation.APPROACH),
        ({"ajakan_berbahaya"}, {"menyakiti_diri"}, True, Situation.DISTRESS),
        (set(), set(), False, Situation.GENERAL),
    ],
)
def test_situation(contact, child, support, expected):
    assert situation(contact, child, support) == expected


@pytest.mark.parametrize(
    "nudge",
    ["Ini salahmu sendiri.", "Kamu ceroboh banget.", "That was your fault."],
)
def test_blaming_nudge_rejected(nudge):
    data = template(Situation.GENERAL, Level.PERHATIAN, "id").model_dump()
    data["child_nudge"] = nudge
    with pytest.raises(ValidationError):
        GuideOutput.model_validate(data)


def test_comforting_negation_allowed():
    data = template(Situation.GENERAL, Level.PERHATIAN, "id").model_dump()
    for nudge in ("Itu bukan salahmu.", "It is not your fault."):
        data["child_nudge"] = nudge
        GuideOutput.model_validate(data)


@pytest.mark.parametrize(
    "line", ["Sita ponselnya seminggu.", "Hukum anak agar jera.", "Punish them."]
)
def test_punishment_advice_rejected_in_do_list(line):
    data = template(Situation.GENERAL, Level.PERHATIAN, "id").model_dump()
    data["parent_insight"]["do"] = [line]
    with pytest.raises(ValidationError):
        GuideOutput.model_validate(data)


class FakeReasoning:
    def __init__(self, output=None, fail=False):
        self.output, self.fail, self.calls = output, fail, []

    async def complete_json(self, **kw):
        self.calls.append(kw)
        if self.fail:
            raise TransientLLMError("HTTP 503", status=503)
        return LLMResult(value=self.output, usage=USAGE, attempts=(USAGE,))


async def run_guide(client, level=Level.WASPADA, support=False, language="id"):
    return await guide(
        client,
        level=level,
        patterns=["meminta_kerahasiaan"],
        contact_labels={"meminta_kerahasiaan"},
        child_labels={"menyakiti_diri"} if support else set(),
        support_needed=support,
        age_range="11-13",
        language=language,
    )


async def test_model_output_used_and_payload_has_no_text():
    model_out = template(Situation.APPROACH, Level.WASPADA, "id")
    client = FakeReasoning(model_out)
    result = await run_guide(client)
    assert result.source == "model"
    payload = json.loads(client.calls[0]["user"])
    assert set(payload) == {"level", "situation", "patterns", "child_age_range", "language"}


async def test_outage_falls_back_to_template_with_all_three_outputs():
    result = await run_guide(FakeReasoning(fail=True), support=True)
    assert result.source == "template"
    assert result.situation == Situation.DISTRESS
    assert result.output.child_nudge and result.output.parent_insight and result.output.micro_lesson


async def test_channels_attached_by_code_only_when_needed():
    low = await run_guide(FakeReasoning(fail=True), level=Level.PERHATIAN)
    high = await run_guide(FakeReasoning(fail=True), level=Level.MENDESAK)
    distress = await run_guide(FakeReasoning(fail=True), level=Level.PERHATIAN, support=True)
    assert low.help_channels == ()
    assert high.help_channels and distress.help_channels
    assert any("Laporkan" in x for x in high.help_channels)
    assert not any("Laporkan" in x for x in distress.help_channels)


def test_unverified_channels_are_never_loaded(tmp_path):
    path = tmp_path / "channels.json"
    path.write_text(
        json.dumps(
            {
                "general": {"id": ["Cerita ke orang dewasa."]},
                "verified": [
                    {"name": "A", "contact": "1", "purpose": "x", "verified": False},
                    {"name": "B", "contact": "2", "purpose": "y", "verified": True},
                    {
                        "name": "C",
                        "contact": "3",
                        "purpose": "z",
                        "verified": True,
                        "verified_by": "owner",
                        "verified_on": "2026-10-27",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    channels = load_channels.__wrapped__(path)
    assert [c.name for c in channels.verified] == ["C"]


async def test_english_output_mixed_with_indonesian_falls_back_to_template():
    mixed = template(Situation.APPROACH, Level.WASPADA, "en").model_dump()
    mixed["child_nudge"] = "Hey kamu, stop replying and tell an adult."
    result = await run_guide(FakeReasoning(GuideOutput.model_validate(mixed)), language="en")
    assert result.source == "template"
    assert "kamu" not in result.output.child_nudge
