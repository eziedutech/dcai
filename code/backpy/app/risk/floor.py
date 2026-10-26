"""Rule floor under the model score (spec section 8.1).

Deterministic and computed from stage 1 labels over the whole conversation so far. The
final score is the highest of the model score, this floor and the previous score. The
model may raise the level above the floor, never below it.
"""

from dataclasses import dataclass, field

from app.risk.schemas import Level, Pattern, level_for
from app.scenarios.schema import ChildLabel

# Lowest score of each level band, so a floor lands exactly on the level it names.
FLOOR_SCORE = {Level.AMAN: 0, Level.PERHATIAN: 30, Level.WASPADA: 60, Level.MENDESAK: 85}


@dataclass
class Seen:
    """What the conversation has shown so far. Labels only, never text."""

    contact: set[str] = field(default_factory=set)  # labels on the contact's messages
    child: set[str] = field(default_factory=set)  # labels on the child's messages
    contact_counts: dict[str, int] = field(default_factory=dict)
    unavailable: int = 0

    def add(self, sender: str, labels: frozenset, available: bool) -> None:
        target = self.contact if sender == "contact" else self.child
        target.update(str(lab) for lab in labels)
        if sender == "contact":
            for lab in labels:
                self.contact_counts[str(lab)] = self.contact_counts.get(str(lab), 0) + 1
        if not available:
            self.unavailable += 1


@dataclass(frozen=True)
class Floor:
    score: int
    level: Level
    reasons: tuple[str, ...]  # rule ids, for logs and the parent view; no text
    support_needed: bool


def rule_floor(seen: Seen, contact_known: bool) -> Floor:
    level = Level.AMAN
    reasons: list[str] = []

    def at_least(lv: Level, reason: str) -> None:
        nonlocal level
        reasons.append(reason)
        if FLOOR_SCORE[lv] > FLOOR_SCORE[level]:
            level = lv

    c = seen.contact
    if not contact_known and Pattern.MEMINTA_DATA_PRIBADI in c:
        at_least(Level.WASPADA, "unknown_contact_asks_personal_data")
    if Pattern.MEMINTA_KERAHASIAAN in c and Pattern.PINDAH_KANAL in c:
        at_least(Level.MENDESAK, "secrecy_and_channel_move")
    if not contact_known and Pattern.MENEKAN_MENGANCAM in c:
        at_least(Level.WASPADA, "unknown_contact_pressure")
    if not contact_known and len(c & _APPROACH) >= 2:
        at_least(Level.PERHATIAN, "unknown_contact_two_approach_patterns")
    if Pattern.MENEKAN_MENGANCAM in c or Pattern.MENEKAN_MENGANCAM in seen.child:
        at_least(Level.PERHATIAN, "threat")
    if ChildLabel.PERUNDUNGAN in c or ChildLabel.PERUNDUNGAN in seen.child:
        at_least(Level.PERHATIAN, "bullying")
    if ChildLabel.BERBAGI_DATA_PRIBADI in seen.child:
        at_least(Level.PERHATIAN, "child_shared_personal_data")
    support = ChildLabel.MENYAKITI_DIRI in seen.child
    if support:
        at_least(Level.PERHATIAN, "child_distress")
    if seen.unavailable:
        # Spec: when labels fail, show perhatian with "analysis unavailable", never aman.
        at_least(Level.PERHATIAN, "analysis_unavailable")
    score = FLOOR_SCORE[level]
    assert level_for(score) == level
    return Floor(score=score, level=level, reasons=tuple(reasons), support_needed=support)


_APPROACH = {
    Pattern.MEMBANGUN_KEDEKATAN,
    Pattern.MEMINTA_KERAHASIAAN,
    Pattern.PINDAH_KANAL,
    Pattern.MEMINTA_DATA_PRIBADI,
    Pattern.MENAWARKAN_HADIAH,
    Pattern.MENGUJI_BATAS,
}
