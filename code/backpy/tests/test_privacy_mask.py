import json
from pathlib import Path

import pytest

from app.privacy.mask import Kind, find, luhn_ok, mask

CASES = json.loads(
    (Path(__file__).resolve().parents[3] / "data" / "privacy" / "pii_cases.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["text"][:40] for c in CASES])
def test_shared_cases(case):
    found = find(case["text"], tuple(case.get("known_names", ())))
    assert sorted({f.kind.value for f in found}) == sorted(set(case["expect"]))


def test_mask_replaces_values_with_markers():
    m = mask("hai Kit, wa aku 0812-0000-1234 atau kit@example.com", known_names=("Kit",))
    assert m.text == "hai [NAMA], wa aku [TELEPON] atau [EMAIL]"
    assert m.kinds == {Kind.NAMA, Kind.TELEPON, Kind.EMAIL}


def test_masked_text_has_no_original_value():
    raw = "rumahku Jl. Kenanga Fiktif No. 12, RT 03, kartu 4000 0000 0000 0002"
    m = mask(raw)
    for value in ("Kenanga", "4000 0000", "No. 12"):
        assert value not in m.text
    assert m.text.count("[ALAMAT]") == 1 and m.text.count("[KARTU]") == 1


def test_findings_hold_no_value():
    f = find("0812-0000-1234")[0]
    assert set(vars(f)) == {"kind", "start", "end"}


def test_text_without_data_is_unchanged():
    raw = "besok main bola jam 4 ya, bawa air minum"
    assert mask(raw).text == raw


def test_luhn():
    assert luhn_ok("4000000000000002")
    assert not luhn_ok("4000000000000001")
