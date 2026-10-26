import copy
import json

import pytest
from pydantic import ValidationError

from app.scenarios.schema import Scenario
from app.scenarios.validate import DEFAULT_DIR, content_problems, load


def test_dataset_is_valid():
    scenarios, errors = load(DEFAULT_DIR)
    assert errors == []
    assert len(scenarios) >= 50
    assert all(s.synthetic for s in scenarios)


@pytest.fixture
def sample() -> dict:
    path = next(DEFAULT_DIR.glob("pendekatan_berisiko/*.json"))
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(synthetic=False),
        lambda d: d.update(expected_final_level="aman"),
        lambda d: d.update(risk_starts_at=None),
        lambda d: d.update(contact_role="guru"),
        lambda d: d.update(expects_support_response=True),
        lambda d: d.update(messages=d["messages"][:3]),
        lambda d: d.update(id="wajar-001"),
        lambda d: d["messages"][0].update(labels=["bukan_label"]),
    ],
)
def test_schema_rejects_inconsistent_scenarios(sample, change):
    data = copy.deepcopy(sample)
    change(data)
    with pytest.raises(ValidationError):
        Scenario.model_validate(data)


def test_content_rules(sample):
    dash = "\u2014"
    data = copy.deepcopy(sample)
    data["messages"][0]["text"] = f"halo {dash} ini aku, emailku kit@gmail.com"
    data["messages"][1]["text"] = "kamu seksi"
    problems = content_problems(Scenario.model_validate(data))
    assert any("dash" in p for p in problems)
    assert any("email" in p for p in problems)
    assert any("explicit" in p for p in problems)


def test_split_is_locked_and_matches_dataset():
    from app.scenarios.split import main

    assert main(["--check"]) == 0
