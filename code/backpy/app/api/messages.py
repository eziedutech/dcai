"""POST /v1/messages/analyze: one message in, an assessment out. Used by the simulator
and the demo; the child's phone uses /v1/device/messages, through the same queue.

Text lives only in memory for the conversation window and is never stored. What is stored:
the conversation (id, channel), one risk_assessment row per update and events. Analysis
runs only while the guardian's consent for "percakapan" is active.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, StringConstraints

from app.analysis.service import ConsentWithdrawn, ConversationGone, Job, Result, worker
from app.api.deps import DbDep, GuardianDep, owned_child
from app.consent.service import has_consent
from app.consent.texts import Scope
from app.db.models import Conversation
from app.scenarios.schema import Channel

router = APIRouter(tags=["analysis"])


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

    db.commit()  # the worker reads the conversation in its own session
    fut = worker(request.app.state).submit(
        Job(
            conversation_id=conversation.id,
            child_id=child.id,
            language=guardian.language,
            contact_known=body.contact_known,
            channel=body.channel.value,
            sender=body.sender,
            text=body.text,
            contact_name=body.contact_name,
        ),
        wait=True,
    )
    assert fut is not None
    try:
        result = await fut
    except ConsentWithdrawn as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent withdrawn") from exc
    except ConversationGone as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found") from exc
    return analyze_out(result)


def analyze_out(result: Result) -> AnalyzeOut:
    step = result.step
    coach_out = None
    if result.coach is not None:
        out = result.coach.output
        coach_out = CoachOut(
            situation=result.coach.situation.value,
            source=result.coach.source,
            child_nudge=out.child_nudge,
            parent_insight=out.parent_insight.model_dump(),
            micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
            help_channels=list(result.coach.help_channels),
        )
    return AnalyzeOut(
        conversation_id=str(result.conversation_id),
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
