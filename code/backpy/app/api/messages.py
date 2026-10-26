"""POST /v1/messages/analyze: one message in, an assessment out.

Text lives only in memory for the conversation window and is never stored. What is stored:
the conversation (id, channel), one risk_assessment row per update and events. Analysis
runs only while the guardian's consent for "percakapan" is active.
"""

import uuid
from collections import OrderedDict
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import func, select

from app.api.deps import DbDep, GuardianDep, owned_child
from app.coach.coach import coach
from app.consent.service import has_consent
from app.consent.texts import Scope
from app.db.models import Conversation, Event, Insight, RiskAssessment
from app.risk.pipeline import ConversationAnalyzer
from app.risk.schemas import Level
from app.scenarios.schema import Channel

router = APIRouter(tags=["analysis"])

MAX_CONVERSATIONS_IN_MEMORY = 500


class AnalyzeIn(BaseModel):
    child_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    channel: Channel
    contact_known: bool
    sender: Literal["child", "contact"]
    text: Annotated[str, StringConstraints(min_length=1, max_length=1000)]
    # Used only to mask this name before any model sees the text; never stored.
    contact_name: Annotated[str, StringConstraints(max_length=40)] | None = None


class CoachOut(BaseModel):
    situation: str
    source: str  # model | template
    child_nudge: str
    parent_insight: dict
    micro_lesson: dict | None
    help_channels: list[str]


class AnalyzeOut(BaseModel):
    conversation_id: str
    message_index: int
    risk_score: int
    level: str
    raised: bool
    patterns_observed: list[str]
    trajectory: str
    trajectory_reason: str
    rationale_for_parent: str
    confidence: str
    # Every assessment is an estimate (spec section 3, principle 5).
    is_estimate: bool = True
    analysis_available: bool
    support_needed: bool
    source: str
    masked_kinds: list[str] = Field(description="kinds of personal data found, no values")
    # Present when this message raised the level to perhatian or above, or first showed
    # distress: the moment the child is guided and the parent informed.
    coach: CoachOut | None = None


class _Analyzers:
    """Conversation windows in memory, oldest dropped first. A restart forgets windows;
    stored levels remain, and a new window starts from the stored score."""

    def __init__(self, cap: int):
        self.cap = cap
        self.items: OrderedDict[uuid.UUID, ConversationAnalyzer] = OrderedDict()

    def get(self, key: uuid.UUID) -> ConversationAnalyzer | None:
        a = self.items.get(key)
        if a is not None:
            self.items.move_to_end(key)
        return a

    def put(self, key: uuid.UUID, analyzer: ConversationAnalyzer) -> None:
        self.items[key] = analyzer
        self.items.move_to_end(key)
        while len(self.items) > self.cap:
            self.items.popitem(last=False)


def _registry(request: Request) -> _Analyzers:
    reg = getattr(request.app.state, "analyzers", None)
    if reg is None:
        reg = request.app.state.analyzers = _Analyzers(MAX_CONVERSATIONS_IN_MEMORY)
    return reg


@router.post("/messages/analyze")
async def analyze(
    body: AnalyzeIn, request: Request, db: DbDep, guardian: GuardianDep
) -> AnalyzeOut:
    child = owned_child(db, guardian, body.child_id)
    if not has_consent(db, child.id, Scope.PERCAKAPAN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent for conversation analysis required")

    if body.conversation_id is None:
        conversation = Conversation(child_id=child.id, channel=body.channel.value)
        db.add(conversation)
        db.flush()
    else:
        conversation = db.get(Conversation, body.conversation_id)
        if conversation is None or conversation.child_id != child.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found")

    registry = _registry(request)
    analyzer = registry.get(conversation.id)
    if analyzer is None:
        names = tuple(n for n in (child.nickname, body.contact_name) if n)
        stored = db.scalar(
            select(func.max(RiskAssessment.score)).where(
                RiskAssessment.conversation_id == conversation.id
            )
        )
        analyzer = ConversationAnalyzer(
            screening=request.app.state.openweights,
            reasoning=request.app.state.muse,
            contact_known=body.contact_known,
            channel=body.channel.value,
            age_range=child.age_range,
            known_names=names,
            base_score=stored or 0,
        )
        registry.put(conversation.id, analyzer)

    step = await analyzer.add(body.sender, body.text)

    first_support = step.support_needed and not any(s.support_needed for s in analyzer.steps[:-1])
    needs_coach = (step.raised and step.level != Level.AMAN) or first_support
    assessment = None
    if step.raised or step.source == "model" or step.index == 1 or needs_coach:
        assessment = RiskAssessment(
            conversation_id=conversation.id,
            score=step.score,
            level=step.level.value,
            patterns=list(step.patterns),
            trajectory=step.trajectory,
            rationale=step.rationale,
            confidence=str(step.confidence),
            model_version=step.model_version,
        )
        db.add(assessment)
        db.flush()
    coach_out = None
    if needs_coach:
        result = await coach(
            request.app.state.muse,
            level=step.level,
            patterns=list(step.patterns),
            contact_labels=set(analyzer.seen.contact),
            child_labels=set(analyzer.seen.child),
            support_needed=step.support_needed,
            age_range=child.age_range,
            language=guardian.language,
        )
        out = result.output
        assert assessment is not None
        db.add(
            Insight(
                assessment_id=assessment.id,
                child_nudge=out.child_nudge,
                parent_insight=out.parent_insight.model_dump(),
                micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
            )
        )
        coach_out = CoachOut(
            situation=result.situation.value,
            source=result.source,
            child_nudge=out.child_nudge,
            parent_insight=out.parent_insight.model_dump(),
            micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
            help_channels=list(result.help_channels),
        )
    if step.raised:
        db.add(Event(child_id=child.id, kind="risiko_naik", level=step.level.value))
    if body.sender == "child" and step.stage1.masked_kinds:
        db.add(Event(child_id=child.id, kind="data_pribadi_dibagikan", level=step.level.value))
    if first_support:
        db.add(Event(child_id=child.id, kind="dukungan_dibutuhkan", level=step.level.value))
    db.commit()

    return AnalyzeOut(
        conversation_id=str(conversation.id),
        message_index=step.index,
        risk_score=step.score,
        level=step.level.value,
        raised=step.raised,
        patterns_observed=list(step.patterns),
        trajectory=step.trajectory,
        trajectory_reason=step.trajectory_reason,
        rationale_for_parent=step.rationale,
        confidence=str(step.confidence),
        analysis_available=step.analysis_available,
        support_needed=step.support_needed,
        source=step.source,
        masked_kinds=sorted(k.value for k in step.stage1.masked_kinds),
        coach=coach_out,
    )
