"""Personal data detection and masking, by deterministic rules only (no model, no network).

Runs before any text reaches a model. The same rules and the same test cases
(data/privacy/pii_cases.json) are meant for the keyboard, so detection behaves the same on
the device and on the server.

Recognised: phone numbers (Indonesian mobile and +international), email addresses, card
numbers (13 to 19 digits that pass the Luhn check) and card expiry dates, street
addresses (Jl./Jalan with a house number or RT/RW), school names (SD, SMP, SMA and
similar, with the class when given), @handles, and names: names the system already knows
(the child's nickname, the contact's display name) and names introduced with "namaku",
"my name is" and similar.

Not recognised, by design of a rule-based method: names that are neither known nor
introduced, a class without a school ("kelas 4"), and places described in words
("rumahku di belakang masjid").
These are stated in the README, not hidden.
"""

import re
from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    TELEPON = "TELEPON"
    EMAIL = "EMAIL"
    KARTU = "KARTU"
    ALAMAT = "ALAMAT"
    AKUN = "AKUN"
    NAMA = "NAMA"
    SEKOLAH = "SEKOLAH"


@dataclass(frozen=True)
class Finding:
    """Where personal data was found. Holds no copy of the value, so it is safe to log."""

    kind: Kind
    start: int
    end: int


@dataclass(frozen=True)
class Masked:
    text: str
    findings: tuple[Finding, ...]

    @property
    def kinds(self) -> set[Kind]:
        return {f.kind for f in self.findings}


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
# 13 to 19 digits, optionally grouped by spaces or dashes; confirmed with Luhn below.
_CARD = re.compile(r"(?<![\d])(?:\d[ -]?){12,18}\d(?![\d])")
# Indonesian mobile: 08xx or +62 8xx / 62 8xx, 9 to 13 digits after the prefix, separators
# allowed. Then any +country number with at least 8 digits.
_PHONE_ID = re.compile(r"(?<![\d+])(?:\+62|62|0)[ -]?8\d(?:[ .-]?\d){7,10}(?![\d])")
_PHONE_INTL = re.compile(r"(?<![\w+])\+\d{1,3}(?:[ .-]?\d){8,12}(?![\d])")
_CARD_EXPIRY = re.compile(
    r"\b(?:exp(?:iry|ired)?|berlaku(?: s\.?d\.?| sampai)?)\.?:?\s*\d{2}\s*/\s*\d{2,4}\b", re.I
)
# School type + name (one to three words, an optional number), then an optional class.
_SCHOOL = re.compile(
    r"\b(?:SD|SMP|SMA|SMK|MI|MTs|MA|SLB)N?\s+(?:Negeri\s+|Swasta\s+|IT\s+)?"
    r"(?:[A-Z][\w'-]*|\d{1,3})(?:\s+(?:[A-Z][\w'-]*|\d{1,3})){0,3}"
    r"(?:\s*,?\s*(?:kelas|class)\s+\d{1,2}\s?[A-Za-z]?\b)?"
)
_HANDLE = re.compile(r"(?<![\w@])@[A-Za-z0-9_.]{3,30}\b")
# "Jl." / "Jln." / "Jalan" + up to four words, then a house number or RT/RW. A bare
# "jalan" is common as a verb ("jalan bareng"), so it needs the number or RT/RW to count.
_STREET = re.compile(
    r"\b(?:jl\.?|jln\.?|jalan)\s+(?:[A-Za-z][\w'.]*\s*){1,4}?"
    r"(?:,?\s*(?:no\.?|nomor)\s*\d+[A-Za-z]?|,?\s*rt\.?\s*\d{1,3}(?:\s*/\s*rw\.?\s*\d{1,3})?)"
    r"(?:\s*,?\s*rt\.?\s*\d{1,3}(?:\s*/\s*rw\.?\s*\d{1,3})?)?",
    re.IGNORECASE,
)
_STREET_SHORT = re.compile(r"\b(?:jl|jln)\.?\s+[A-Za-z][\w'.]*(?:\s+[A-Z][\w'.]*){0,3}", re.I)
_RT_RW = re.compile(r"\brt\.?\s*\d{1,3}\s*/?\s*rw\.?\s*\d{1,3}\b", re.IGNORECASE)
_NAME_INTRO = re.compile(
    r"\b(?:nama\s?(?:ku|aku|saya|gue|gw)|my name is|panggil\s+(?:aku|saja|aja))"
    r"\s+(?:adalah\s+|itu\s+)?([A-Za-z][a-z]{1,20})\b",
    re.IGNORECASE,
)
_NOT_NAMES = {"aja", "saja", "dong", "deh", "kok", "sih", "itu", "apa", "siapa", "is", "the"}


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def find(text: str, known_names: tuple[str, ...] = ()) -> list[Finding]:
    spans: list[Finding] = []

    def add(kind: Kind, start: int, end: int) -> None:
        if not any(start < f.end and f.start < end for f in spans):
            spans.append(Finding(kind, start, end))

    for m in _EMAIL.finditer(text):
        add(Kind.EMAIL, m.start(), m.end())
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits) and not _PHONE_ID.fullmatch(m.group(0)):
            add(Kind.KARTU, m.start(), m.end())
    for m in _CARD_EXPIRY.finditer(text):
        add(Kind.KARTU, m.start(), m.end())
    for pattern in (_PHONE_ID, _PHONE_INTL):
        for m in pattern.finditer(text):
            add(Kind.TELEPON, m.start(), m.end())
    for pattern in (_STREET, _STREET_SHORT, _RT_RW):
        for m in pattern.finditer(text):
            add(Kind.ALAMAT, m.start(), m.end())
    for m in _SCHOOL.finditer(text):
        add(Kind.SEKOLAH, m.start(), m.end())
    for m in _HANDLE.finditer(text):
        add(Kind.AKUN, m.start(), m.end())
    for m in _NAME_INTRO.finditer(text):
        if m.group(1).lower() not in _NOT_NAMES:
            add(Kind.NAMA, m.start(1), m.end(1))
    for name in known_names:
        if len(name) < 2:
            continue
        for m in re.finditer(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.IGNORECASE):
            add(Kind.NAMA, m.start(), m.end())
    return sorted(spans, key=lambda f: f.start)


def mask(text: str, known_names: tuple[str, ...] = ()) -> Masked:
    findings = find(text, known_names)
    out, pos = [], 0
    for f in findings:
        out.append(text[pos : f.start])
        out.append(f"[{f.kind.value}]")
        pos = f.end
    out.append(text[pos:])
    return Masked(text="".join(out), findings=tuple(findings))
