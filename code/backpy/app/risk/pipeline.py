"""One conversation, message by message: mask and label (stage 1), rule floor, then
Muse Spark (stage 2) when the window shows a signal.

The final score is the highest of the previous score, the rule floor and the model score.
It never goes down within a conversation. The spec allows a decrease after a message that
clearly calms the situation; this MVP does not decrease at all, a deliberate choice: a
missed escalation costs more than a level that stays up until a parent has looked.

The window of masked messages lives in memory only and is never written to the database.
"""

from dataclasses import dataclass, field

from app.llm import LLMClient
from app.risk.floor import Floor, Seen, rule_floor
from app.risk.schemas import Confidence, Level, Pattern, level_for
from app.risk.stage1 import Stage1Result, label_message
from app.risk.stage2 import WINDOW, WindowMessage, assess

# Stage 2 runs when any message in the window carries a label or this much signal.
SIGNAL_TRIGGER = 30

_RULE_RATIONALE = {
    "secrecy_and_channel_move": (
        "Ada permintaan merahasiakan obrolan bersama ajakan pindah ke kanal lain. "
        "Kombinasi ini perlu segera dibicarakan dengan anak."
    ),
    "unknown_contact_asks_personal_data": (
        "Kontak yang belum dikenal meminta data pribadi atau foto. "
        "Sebaiknya didampingi sebelum anak membalas lebih jauh."
    ),
    "unknown_contact_pressure": "Kontak yang belum dikenal memberi tekanan atau ancaman.",
    "unknown_contact_two_approach_patterns": (
        "Kontak yang belum dikenal menunjukkan beberapa pola pendekatan sekaligus."
    ),
    "threat": "Ada kalimat bernada ancaman dalam obrolan.",
    "bullying": "Ada tanda perundungan dalam obrolan.",
    "child_shared_personal_data": "Anak membagikan data pribadi dalam obrolan.",
    "child_distress": (
        "Anak menyampaikan perasaan berat. Dukungan dan percakapan yang hangat lebih "
        "penting daripada menilai."
    ),
    "analysis_unavailable": (
        "Analisis AI tidak tersedia untuk sebagian pesan, jadi level ini adalah batas aman "
        "dari aturan, bukan hasil penilaian lengkap."
    ),
}
_CALM = "Belum terlihat pola yang perlu diperhatikan."


@dataclass(frozen=True)
class Step:
    index: int
    stage1: Stage1Result
    floor: Floor
    score: int
    level: Level
    raised: bool  # the level went up on this message
    patterns: tuple[str, ...]
    trajectory: str
    trajectory_reason: str
    rationale: str
    confidence: Confidence
    source: str  # model | rules | carried
    model_version: str
    stage2_called: bool
    analysis_available: bool
    support_needed: bool


@dataclass
class ConversationAnalyzer:
    screening: LLMClient
    reasoning: LLMClient
    contact_known: bool
    channel: str
    age_range: str
    known_names: tuple[str, ...] = ()
    # Highest stored score when a window is rebuilt (after a restart), so it cannot drop.
    base_score: int = 0
    seen: Seen = field(default_factory=Seen)
    window: list[WindowMessage] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)

    @property
    def score(self) -> int:
        return self.steps[-1].score if self.steps else 0

    async def add(self, sender: str, text: str) -> Step:
        index = len(self.steps) + 1
        s1 = await label_message(self.screening, sender, text, self.known_names)  # type: ignore[arg-type]
        self.seen.add(sender, s1.labels, s1.status == "ok")
        self.window.append(
            WindowMessage(
                index, sender, tuple(sorted(map(str, s1.labels))), s1.signal, s1.masked_text
            )
        )
        self.window = self.window[-WINDOW:]
        floor = rule_floor(self.seen, self.contact_known)
        prev = self.steps[-1] if self.steps else None
        prev_score = prev.score if prev else self.base_score
        prev_level = prev.level if prev else level_for(self.base_score)

        triggered = any(m.labels or (m.signal or 0) >= SIGNAL_TRIGGER for m in self.window)
        model = None
        model_version = "rules"
        if triggered:
            s2 = await assess(
                self.reasoning,
                self.window,
                contact_known=self.contact_known,
                channel=self.channel,
                age_range=self.age_range,
            )
            model = s2.assessment
            if model is not None and s2.model:
                model_version = s2.model

        model_score = model.risk_score if model else 0
        score = max(prev_score, floor.score, model_score)
        level = level_for(score)
        raised = level != prev_level and score > prev_score
        analysis_available = s1.status == "ok" and (not triggered or model is not None)

        if model is not None:
            patterns = tuple(str(p) for p in model.patterns_observed)
            rationale = model.rationale_for_parent
            confidence = model.confidence
            trajectory, reason = model.trajectory.status.value, model.trajectory.reason
            source = "model"
            if level_for(model_score) != level:
                # The floor or an earlier step holds the level above the model's view, so
                # the explanation comes from whatever set that level.
                rationale = self._floor_text(floor) or (prev.rationale if prev else rationale)
                source = "rules"
        elif triggered or floor.score > 0:
            patterns = tuple(sorted(str(p) for p in self.seen.contact if p in set(Pattern)))
            rationale = self._floor_text(floor) or (prev.rationale if prev else _CALM)
            confidence = Confidence.RENDAH if not analysis_available else Confidence.SEDANG
            trajectory = "meningkat" if raised else "stabil"
            reason = "Level naik karena aturan keselamatan." if raised else "Belum ada perubahan."
            source = "rules"
        elif prev is not None:
            patterns, rationale, confidence = prev.patterns, prev.rationale, prev.confidence
            trajectory, reason, source = "stabil", "Belum ada perubahan.", "carried"
            model_version = prev.model_version
        else:
            patterns, rationale, confidence = (), _CALM, Confidence.SEDANG
            trajectory, reason, source = "stabil", "Belum ada perubahan.", "rules"

        step = Step(
            index=index,
            stage1=s1,
            floor=floor,
            score=score,
            level=level,
            raised=raised,
            patterns=patterns,
            trajectory=trajectory,
            trajectory_reason=reason,
            rationale=rationale,
            confidence=confidence,
            source=source,
            model_version=model_version,
            stage2_called=triggered,
            analysis_available=analysis_available,
            support_needed=floor.support_needed,
        )
        self.steps.append(step)
        return step

    @staticmethod
    def _floor_text(floor: Floor) -> str | None:
        """Rule text for the strongest rule that set the floor."""
        for reason in _PRIORITY:
            if reason in floor.reasons:
                return _RULE_RATIONALE[reason]
        return None


_PRIORITY = (
    "secrecy_and_channel_move",
    "unknown_contact_asks_personal_data",
    "unknown_contact_pressure",
    "child_distress",
    "threat",
    "bullying",
    "unknown_contact_two_approach_patterns",
    "child_shared_personal_data",
    "analysis_unavailable",
)
