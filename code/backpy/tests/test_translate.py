"""The Guide's text follows the dashboard language: templates re-rendered, model text
translated once and kept, the original when translation fails."""

import json

from app.db.models import Insight
from app.guide.guide import Situation
from app.guide.templates import template
from app.guide.translate import _Items, guide_text
from app.llm import LLMResult
from app.risk.schemas import Level
from tests.conftest import auth
from tests.test_devices import message, paired
from tests.test_guide import FakeReasoning
from tests.test_risk_pipeline import USAGE


class FakeDb:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def model_insight() -> Insight:
    out = template(Situation.APPROACH, Level.WASPADA, "id")
    return Insight(
        child_nudge=out.child_nudge,
        parent_insight=out.parent_insight.model_dump(),
        micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
        situation="approach",
        source="model",
        language="id",
    )


async def test_model_text_is_translated_once_and_kept():
    ins, db = model_insight(), FakeDb()
    english = template(Situation.APPROACH, Level.WASPADA, "en")
    client = FakeReasoning(english)

    text, lang = await guide_text(client, db, ins, Level.WASPADA, "id", "en")
    again, _ = await guide_text(client, db, ins, Level.WASPADA, "id", "en")

    assert lang == "en" and text["child_nudge"] == english.child_nudge
    assert again == text
    assert len(client.calls) == 1 and db.commits == 1
    sent = json.loads(client.calls[0]["user"])
    assert set(sent) == {"target_language", "child_nudge", "parent_insight", "micro_lesson"}


async def test_failed_translation_keeps_the_original():
    ins = model_insight()
    failing = FakeReasoning(fail=True)
    text, lang = await guide_text(failing, FakeDb(), ins, Level.WASPADA, "id", "en")
    assert lang == "id" and text["child_nudge"] == ins.child_nudge
    assert ins.translations is None


async def test_same_language_needs_no_call():
    client = FakeReasoning()
    _, lang = await guide_text(client, FakeDb(), model_insight(), Level.WASPADA, "id", "id")
    assert lang == "id" and client.calls == []


def test_overview_in_the_display_language(api):
    tokens, child, dev, _ = paired(api)
    message(api, dev, "halo")
    message(api, dev, "kirim foto kamu")
    url = f"/v1/children/{child['id']}/overview"
    english = template(Situation.APPROACH, Level.WASPADA, "en")
    translator = FakeReasoning(english)
    api.app.state.muse = translator

    own = api.get(url, headers=auth(tokens)).json()["latest_insight"]
    en = api.get(f"{url}?lang=en", headers=auth(tokens)).json()["latest_insight"]
    again = api.get(f"{url}?lang=en", headers=auth(tokens)).json()["latest_insight"]

    assert own["language"] == "id" and en["language"] == "en"
    assert en["child_nudge"] == english.child_nudge
    assert en["parent_insight"] == english.parent_insight.model_dump()
    assert again == en and len(translator.calls) == 1  # kept with the insight
    assert api.get(f"{url}?lang=fr", headers=auth(tokens)).status_code == 422


class EchoTranslator:
    """Answers a rationale batch with each id and an English text."""

    def __init__(self):
        self.calls = []

    async def complete_json(self, **kw):
        self.calls.append(kw)
        items = json.loads(kw["user"])["items"]
        value = _Items(
            items=[{"id": i["id"], "text": "A stranger is building closeness."} for i in items]
        )
        return LLMResult(value=value, usage=USAGE, attempts=(USAGE,))


def test_conversation_rationales_translated_in_one_call(api):
    tokens, child, dev, _ = paired(api)
    message(api, dev, "halo")
    message(api, dev, "kirim foto kamu")
    url = f"/v1/children/{child['id']}/conversations"
    translator = EchoTranslator()
    api.app.state.muse = translator

    own = api.get(url, headers=auth(tokens)).json()
    en = api.get(f"{url}?lang=en", headers=auth(tokens)).json()
    again = api.get(f"{url}?lang=en", headers=auth(tokens)).json()

    assert own[0]["rationale_for_parent"] != "A stranger is building closeness."
    assert en[0]["rationale_for_parent"] == "A stranger is building closeness."
    assert again == en and len(translator.calls) == 1
