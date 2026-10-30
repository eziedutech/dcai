"""Message analysis shared by the simulator endpoint and the child's phone.

Every message goes through one queue per conversation, in order. The worker labels each
message (stage 1), runs stage 2 only for the last message waiting in that queue, stores
the assessment, runs the Guide once per escalation to perhatian or above (whether the
level rose on this message or earlier via the rule floor), records events and publishes
live updates. Text lives only in the job and the in-memory window; it is never written to
the database, a log or a live update.
"""

import asyncio
import logging
import uuid
from collections import OrderedDict, deque
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.consent.service import has_consent
from app.consent.texts import Scope
from app.db.base import session_factory
from app.db.models import ChildProfile, Conversation, Event, Insight, RiskAssessment
from app.guide.guide import GuideResult, guide, instant
from app.live.broker import Broker, child_key, device_key
from app.risk.pipeline import ConversationAnalyzer, Step
from app.risk.schemas import Level

log = logging.getLogger("dcai.analysis")

MAX_CONVERSATIONS_IN_MEMORY = 500
# A burst never postpones the considered assessment (stage 2 + Guide) longer than this many
# messages: under a steady flood the queue never empties, so without a cap assess would stay
# False forever and the level would go out with no insight and no nudge.
MAX_DEFERRED_MESSAGES = 8


class ConsentWithdrawn(Exception):
    """Consent for conversation analysis ended while the message waited in the queue."""


class ConversationGone(Exception):
    """The conversation or child was erased while the message waited in the queue."""


@dataclass
class Job:
    conversation_id: uuid.UUID
    child_id: uuid.UUID
    language: str
    contact_known: bool
    channel: str
    sender: str
    text: str = field(repr=False)
    # Used only to mask this name before any model sees the text; never stored.
    contact_name: str | None = field(default=None, repr=False)
    device_id: uuid.UUID | None = None


@dataclass(frozen=True)
class Result:
    conversation_id: uuid.UUID
    step: Step
    guide: GuideResult | None
    events: tuple[str, ...]


class Analyzers:
    """Conversation windows in memory, oldest dropped first. A restart forgets windows;
    stored levels remain, and a new window starts from the stored score."""

    def __init__(self, cap: int = MAX_CONVERSATIONS_IN_MEMORY):
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


def state_item(state, name: str, factory):
    """A per-app object on app.state, created on first use. Tests reset one by setting it
    to None (for analyzers, that is what a restart does)."""
    item = getattr(state, name, None)
    if item is None:
        item = factory()
        setattr(state, name, item)
    return item


def broker(state) -> Broker:
    return state_item(state, "broker", Broker)


def worker(state) -> Worker:
    return state_item(state, "worker", lambda: Worker(state))


class Worker:
    def __init__(self, state):
        self.state = state
        self._queues: dict[uuid.UUID, deque[tuple[Job, asyncio.Future | None]]] = {}
        self._tasks: dict[uuid.UUID, asyncio.Task] = {}

    def submit(self, job: Job, *, wait: bool) -> asyncio.Future | None:
        """Queue a message. With wait, the returned future resolves to its Result."""
        fut = asyncio.get_running_loop().create_future() if wait else None
        self._queues.setdefault(job.conversation_id, deque()).append((job, fut))
        if job.conversation_id not in self._tasks:
            self._tasks[job.conversation_id] = asyncio.create_task(self._drain(job.conversation_id))
        return fut

    def busy(self) -> bool:
        return bool(self._tasks)

    async def idle(self) -> None:
        while self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _drain(self, cid: uuid.UUID) -> None:
        queue = self._queues[cid]
        deferred = 0
        try:
            while queue:
                job, fut = queue.popleft()
                # Assess on the last queued message, or once the cap is reached so a flood
                # can never postpone stage 2 and the Guide indefinitely.
                assess = not queue or deferred >= MAX_DEFERRED_MESSAGES
                try:
                    result = await process(self.state, job, assess=assess)
                except Exception as exc:  # one failed message must not stop the queue
                    log.warning("analysis_failed error=%s", type(exc).__name__)
                    if fut is not None and not fut.done():
                        fut.set_exception(exc)
                    continue
                deferred = 0 if assess else deferred + 1
                if fut is not None and not fut.done():
                    fut.set_result(result)
        finally:
            for _, fut in queue:
                if fut is not None and not fut.done():
                    fut.cancel()
            self._queues.pop(cid, None)
            self._tasks.pop(cid, None)


def _analyzer(state, db: Session, conversation: Conversation, child: ChildProfile, job: Job):
    registry: Analyzers = state_item(state, "analyzers", Analyzers)
    analyzer = registry.get(conversation.id)
    if analyzer is None:
        names = tuple(n for n in (child.nickname, job.contact_name) if n)
        stored = db.scalar(
            select(func.max(RiskAssessment.score)).where(
                RiskAssessment.conversation_id == conversation.id
            )
        )
        analyzer = ConversationAnalyzer(
            screening=state.openweights,
            reasoning=state.muse,
            contact_known=job.contact_known,
            channel=job.channel,
            age_range=child.age_range,
            known_names=names,
            base_score=stored or 0,
        )
        registry.put(conversation.id, analyzer)
    return analyzer


def _has_insight_for_level(db: Session, conversation_id: uuid.UUID, level: Level) -> bool:
    """Whether this conversation already has an insight stored at this level band. The score
    only rises, so each band is reached once; this makes the Guide fire exactly once per
    escalation even when stage 2 never ran, and survives a restart (the truth is the row)."""
    return (
        db.scalar(
            select(Insight.id)
            .join(RiskAssessment, Insight.assessment_id == RiskAssessment.id)
            .where(RiskAssessment.conversation_id == conversation_id)
            .where(RiskAssessment.level == level.value)
            .limit(1)
        )
        is not None
    )


async def process(state, job: Job, *, assess: bool = True) -> Result:
    """Analyse one message. The level goes out as soon as it is known; the Guide follows.

    With assess=False more messages of this conversation are waiting: stage 2 and the Guide
    are left to the last of them (the analyzer's guide_due carries the debt across drain
    cycles), so a level that is already out of date is never guided."""
    bus = broker(state)
    with session_factory(state.settings.database_url)() as db:
        child = db.get(ChildProfile, job.child_id)
        conversation = db.get(Conversation, job.conversation_id)
        if child is None or conversation is None:
            raise ConversationGone
        # Checked again here: consent may end while the message waits.
        if not has_consent(db, child.id, Scope.PERCAKAPAN):
            raise ConsentWithdrawn
        analyzer = _analyzer(state, db, conversation, child, job)
        step = await analyzer.add(job.sender, job.text, assess=assess)
        thread_key, app_name = conversation.thread_key, conversation.app

        first_support = step.support_needed and not any(
            s.support_needed for s in analyzer.steps[:-1]
        )
        # A considered (stage 2) assessment at perhatian or above must guide even when the
        # level did not rise on this exact step. Under a burst the level often reaches risk
        # via an earlier message (stage 1 + rule floor), so by the time stage 2 runs,
        # step.raised is already False; the raise-only trigger then skipped the Guide.
        considered_risk = step.source == "model" and step.level != Level.AMAN
        # Safety net: as long as the level is at perhatian or above and no insight has been
        # stored for that band yet, guide it, whatever raised/source/assess say. This is what
        # guarantees one insight + nudge per escalation: a level reached via the rule floor
        # (no stage 2, raised already False on the message that carries it) used to leave the
        # dashboard with a level but no insight and the child with no nudge.
        need_insight = step.level != Level.AMAN and not _has_insight_for_level(
            db, conversation.id, step.level
        )
        due = (
            analyzer.guide_due
            or (step.raised and step.level != Level.AMAN)
            or considered_risk
            or first_support
            or need_insight
        )
        run_guide = due and assess
        # Log the decision at INFO only when it is interesting (the Guide runs, or the level
        # is not aman); the calm, per-message common case goes to DEBUG so the log stays small.
        emit = log.info if (run_guide or step.level != Level.AMAN) else log.debug
        emit(
            "guide_decision cid=%s level=%s source=%s raised=%s assess=%s guide_due=%s "
            "considered_risk=%s first_support=%s need_insight=%s run_guide=%s",
            conversation.id,
            step.level.value,
            step.source,
            step.raised,
            assess,
            analyzer.guide_due,
            considered_risk,
            first_support,
            need_insight,
            run_guide,
        )
        # The debt is paid when the Guide runs, kept when it is deferred to a later message.
        analyzer.guide_due = due and not assess
        assessment = None
        if step.raised or step.source == "model" or step.index == 1 or run_guide:
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
        events = []
        if step.raised:
            events.append("risiko_naik")
        if job.sender == "child" and step.stage1.masked_kinds:
            events.append("data_pribadi_dibagikan")
        if first_support:
            events.append("dukungan_dibutuhkan")
        for kind in events:
            db.add(Event(child_id=child.id, kind=kind, level=step.level.value))
        db.commit()
        quick = None
        if job.device_id is not None and (
            (step.raised and step.level != Level.AMAN)
            or considered_risk
            or first_support
            or run_guide
        ):
            quick = instant(
                level=step.level,
                contact_labels=set(analyzer.seen.contact),
                child_labels=set(analyzer.seen.child),
                support_needed=step.support_needed,
                language=job.language,
            )
        _publish_step(
            bus,
            job,
            step,
            conversation.id,
            events,
            assessment is not None,
            thread_key,
            app_name,
            quick,
        )

        guide_result = None
        if run_guide:
            guide_result = await guide(
                state.muse,
                level=step.level,
                patterns=list(step.patterns),
                contact_labels=set(analyzer.seen.contact),
                child_labels=set(analyzer.seen.child),
                support_needed=step.support_needed,
                age_range=child.age_range,
                language=job.language,
            )
            out = guide_result.output
            assert assessment is not None
            db.add(
                Insight(
                    assessment_id=assessment.id,
                    child_nudge=out.child_nudge,
                    parent_insight=out.parent_insight.model_dump(),
                    micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
                    situation=guide_result.situation.value,
                    source=guide_result.source,
                    language=job.language,
                )
            )
            db.commit()
            _publish_guide(bus, job, step, conversation.id, guide_result, thread_key)

    return Result(conversation.id, step, guide_result, tuple(events))


def _publish_step(
    bus: Broker,
    job: Job,
    step: Step,
    conversation_id,
    events,
    stored: bool,
    thread_key,
    app_name,
    quick: GuideResult | None,
) -> None:
    cid = str(conversation_id)
    guardian = child_key(job.child_id)
    for kind in events:
        bus.publish(
            guardian, "event", {"kind": kind, "level": step.level.value, "conversation_id": cid}
        )
    if stored:
        bus.publish(
            guardian,
            "assessment",
            {
                "conversation_id": cid,
                "app": app_name,
                "message_index": step.index,
                "risk_score": step.score,
                "level": step.level.value,
                "raised": step.raised,
                "patterns_observed": list(step.patterns),
                "trajectory": step.trajectory,
                "rationale_for_parent": step.rationale,
                "confidence": str(step.confidence),
                "source": step.source,
            },
        )
    if job.device_id is not None and (step.raised or quick is not None):
        nudge = None
        if quick is not None:
            # A reviewed template, so the child is guided now; the "nudge" event that
            # follows carries the model's version for the same moment.
            nudge = {
                "source": quick.source,
                "situation": quick.situation.value,
                "child_nudge": quick.output.child_nudge,
                "help_channels": list(quick.help_channels),
            }
        bus.publish(
            device_key(job.device_id),
            "level",
            {
                "conversation_id": cid,
                "thread_key": thread_key,
                "level": step.level.value,
                "nudge": nudge,
            },
        )


def _publish_guide(
    bus: Broker, job: Job, step: Step, conversation_id, r: GuideResult, thread_key
) -> None:
    cid, out = str(conversation_id), r.output
    lesson = out.micro_lesson.model_dump() if out.micro_lesson else None
    bus.publish(
        child_key(job.child_id),
        "insight",
        {
            "conversation_id": cid,
            "level": step.level.value,
            "situation": r.situation.value,
            "parent_insight": out.parent_insight.model_dump(),
            "micro_lesson": lesson,
        },
    )
    if job.device_id is not None:
        bus.publish(
            device_key(job.device_id),
            "nudge",
            {
                "conversation_id": cid,
                "thread_key": thread_key,
                "level": step.level.value,
                "source": r.source,
                "situation": r.situation.value,
                "child_nudge": out.child_nudge,
                "micro_lesson": lesson,
                "help_channels": list(r.help_channels),
            },
        )
