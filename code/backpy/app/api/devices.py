"""The child's phone (dcAI Guardian) and the guardian's control over it.

Guardian side: create a pairing code, list and revoke devices, follow a child live.
Phone side (/v1/device): pair, read its configuration, report service state, send flagged
messages (already masked on the phone, masked again here), image labels and confirmed
false detections, and follow its own live updates.

What a phone may receive is limited to what the child may see: its configuration, levels
of its own conversations and Coach nudges. Parent insight never goes to the phone.
"""

import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import audit
from app.analysis.service import (
    ConsentWithdrawn,
    ConversationGone,
    Job,
    broker,
    state_item,
    worker,
)
from app.api.deps import DbDep, DeviceDep, GuardianDep, SettingsDep, owned_child
from app.auth.security import hash_pairing_code, new_device_token, new_pairing_code
from app.consent.service import active_scopes
from app.consent.texts import Scope
from app.db.base import utcnow
from app.db.models import (
    ChildProfile,
    ConsentRecord,
    Conversation,
    DetectionFeedback,
    Device,
    Event,
    Guardian,
    ImageSignal,
    PairingCode,
)
from app.live.broker import child_key, device_key, sse_stream
from app.scenarios.schema import Channel

guardian_router = APIRouter(tags=["devices"])
device_router = APIRouter(prefix="/device", tags=["device"])

Service = Literal["accessibility", "notification", "vpn", "keyboard"]
ThreadKey = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{16,64}$")]
PackageName = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$", max_length=100)
]
ModelVersion = Annotated[str, StringConstraints(min_length=1, max_length=120)]


class ImageTrigger(StrEnum):
    PERCAKAPAN = "percakapan"  # an image in a conversation already at perhatian or above
    DIBAGIKAN = "dibagikan"  # an image the child is about to share
    SITUS = "situs"  # an image on a flagged site


class ImageCategory(StrEnum):
    SEKSUAL = "seksual"
    KEKERASAN = "kekerasan"
    TEKS_PRIBADI = "teks_pribadi"  # e.g. a student card or an address in the picture
    WAJAH = "wajah"
    AMAN = "aman"


class ImageAction(StrEnum):
    DIKABURKAN = "dikaburkan"  # blurred on the phone, never sent
    DITINJAU = "ditinjau"  # sent, reduced and with faces and text blurred, for a cloud look
    DIBIARKAN = "dibiarkan"


# ---------------------------------------------------------------- guardian side


class PairingCodeOut(BaseModel):
    code: str
    expires_at: datetime


class DeviceOut(BaseModel):
    id: str
    child_id: str
    name: str
    platform: str
    app_version: str
    services: dict[str, bool]
    paired_at: datetime
    last_seen_at: datetime | None
    revoked: bool


def _device_out(d: Device) -> DeviceOut:
    return DeviceOut(
        id=str(d.id),
        child_id=str(d.child_id),
        name=d.name,
        platform=d.platform,
        app_version=d.app_version,
        services=d.services or {},
        paired_at=d.paired_at,
        last_seen_at=d.last_seen_at,
        revoked=d.revoked_at is not None,
    )


@guardian_router.post("/children/{child_id}/pairing-codes", status_code=status.HTTP_201_CREATED)
def create_pairing_code(
    child_id: uuid.UUID, db: DbDep, guardian: GuardianDep, settings: SettingsDep
) -> PairingCodeOut:
    child = owned_child(db, guardian, child_id)
    if not active_scopes(db, child.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "consent is required before pairing")
    code, code_hash = new_pairing_code()
    expires = utcnow() + timedelta(minutes=settings.pairing_code_minutes)
    db.add(PairingCode(child_id=child.id, code_hash=code_hash, expires_at=expires))
    audit.record(db, audit.guardian_actor(guardian.id), "pairing_code_created", child.id)
    db.commit()
    return PairingCodeOut(code=f"{code[:4]}-{code[4:]}", expires_at=expires)


@guardian_router.get("/children/{child_id}/devices")
def list_devices(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> list[DeviceOut]:
    child = owned_child(db, guardian, child_id)
    rows = db.scalars(
        select(Device).where(Device.child_id == child.id).order_by(Device.paired_at)
    ).all()
    return [_device_out(d) for d in rows]


@guardian_router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_device(device_id: uuid.UUID, request: Request, db: DbDep, guardian: GuardianDep) -> None:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "device not found")
    owned_child(db, guardian, device.child_id)  # 404 for another guardian's device
    if device.revoked_at is None:
        device.revoked_at = utcnow()
        audit.record(db, audit.guardian_actor(guardian.id), "device_revoked", device.id)
        db.commit()
    broker(request.app.state).publish(device_key(device.id), "revoked", {})


@guardian_router.get("/children/{child_id}/stream")
async def child_stream(
    child_id: uuid.UUID, request: Request, db: DbDep, guardian: GuardianDep, settings: SettingsDep
) -> StreamingResponse:
    """Live events, assessments and insight for one child, for the dashboard."""
    child = owned_child(db, guardian, child_id)
    db.close()
    return _sse(request, child_key(child.id), settings)


# ---------------------------------------------------------------- phone side


class DeviceConfig(BaseModel):
    device_id: str
    child_nickname: str
    age_range: str
    language: str
    # The phone uses only these. Withdrawn scopes arrive as a "config" live update.
    scopes: list[Scope]
    consent_version: str | None
    stream_path: str = "/v1/device/stream"


def device_config(db: Session, device: Device) -> DeviceConfig:
    child = db.get(ChildProfile, device.child_id)
    assert child is not None
    guardian = db.get(Guardian, child.guardian_id)
    assert guardian is not None
    latest = db.scalar(
        select(ConsentRecord.text_version)
        .where(ConsentRecord.child_id == child.id, ConsentRecord.action == "grant")
        .order_by(ConsentRecord.created_at.desc(), ConsentRecord.id.desc())
        .limit(1)
    )
    return DeviceConfig(
        device_id=str(device.id),
        child_nickname=child.nickname,
        age_range=child.age_range,
        language=guardian.language,
        scopes=sorted(active_scopes(db, child.id)),
        consent_version=latest,
    )


def notify_config_changed(state, db: Session, child_id: uuid.UUID) -> None:
    """Tell every active phone of this child its new configuration, e.g. after consent
    for a scope is withdrawn, so it stops using that scope right away."""
    bus = broker(state)
    devices = db.scalars(
        select(Device).where(Device.child_id == child_id, Device.revoked_at.is_(None))
    ).all()
    for d in devices:
        bus.publish(device_key(d.id), "config", device_config(db, d).model_dump(mode="json"))


def notify_devices_revoked(state, db: Session, child_id: uuid.UUID) -> None:
    bus = broker(state)
    for (device_id,) in db.execute(select(Device.id).where(Device.child_id == child_id)):
        bus.publish(device_key(device_id), "revoked", {})


class PairIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Annotated[str, StringConstraints(min_length=8, max_length=12)]
    device_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
    ]
    platform: Literal["android"]
    app_version: Annotated[str, StringConstraints(pattern=r"^[0-9A-Za-z.+-]{1,20}$")]


class PairOut(BaseModel):
    device_id: str
    # Shown once. The server keeps only its hash.
    device_token: str
    config: DeviceConfig


@device_router.post("/pair", status_code=status.HTTP_201_CREATED)
def pair(body: PairIn, db: DbDep) -> PairOut:
    now = utcnow()
    code = db.scalar(
        select(PairingCode).where(PairingCode.code_hash == hash_pairing_code(body.code))
    )
    if code is None or code.used_at is not None or code.expires_at <= now:
        # One answer for unknown, used and expired, so codes cannot be probed.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "pairing code invalid or expired")
    code.used_at = now
    token, token_hash = new_device_token()
    device = Device(
        child_id=code.child_id,
        name=body.device_name,
        platform=body.platform,
        app_version=body.app_version,
        token_hash=token_hash,
        services={},
        last_seen_at=now,
    )
    db.add(device)
    db.flush()
    audit.record(db, f"device:{device.id}", "device_paired", code.child_id)
    db.commit()
    return PairOut(device_id=str(device.id), device_token=token, config=device_config(db, device))


@device_router.get("/config")
def get_config(db: DbDep, device: DeviceDep) -> DeviceConfig:
    db.commit()  # last_seen_at
    return device_config(db, device)


class HeartbeatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_version: Annotated[str, StringConstraints(pattern=r"^[0-9A-Za-z.+-]{1,20}$")]
    services: dict[Service, bool]


@device_router.post("/heartbeat")
def heartbeat(body: HeartbeatIn, request: Request, db: DbDep, device: DeviceDep) -> DeviceConfig:
    """The phone reports which protection services are on. A service that goes off is an
    event for the parent (a teenager may switch it off); coming back on is one too."""
    before = dict(device.services or {})
    after = {**before, **body.services}
    changes = []
    for name, on in body.services.items():
        if before.get(name) is True and not on:
            changes.append(("perlindungan_dimatikan", "perhatian", name))
        elif before.get(name) is False and on:
            changes.append(("perlindungan_aktif", "aman", name))
    device.services = after
    device.app_version = body.app_version
    for kind, level, _ in changes:
        db.add(Event(child_id=device.child_id, kind=kind, level=level))
    db.commit()
    bus = broker(request.app.state)
    for kind, level, name in changes:
        bus.publish(
            child_key(device.child_id),
            "event",
            {"kind": kind, "level": level, "device_id": str(device.id), "service": name},
        )
    return device_config(db, device)


def _require(db: Session, device: Device, scope: Scope) -> None:
    if scope not in active_scopes(db, device.child_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"consent for {scope.value} required")


class RateLimiter:
    """Per-device sliding window. Only messages the phone flagged come here, so hitting it
    means something is wrong on the phone, not a busy child."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._hits: dict[uuid.UUID, deque[float]] = {}

    def allow(self, key: uuid.UUID) -> bool:
        now = time.monotonic()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= self.per_minute:
            return False
        hits.append(now)
        return True


class DeviceMessageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_key: ThreadKey
    app: PackageName
    channel: Channel
    contact_known: bool
    sender: Literal["child", "contact"]
    text: Annotated[str, StringConstraints(min_length=1, max_length=1000)]
    # Used only to mask this name before any model sees the text; never stored.
    contact_name: Annotated[str, StringConstraints(max_length=40)] | None = None


class DeviceNudge(BaseModel):
    situation: str
    child_nudge: str
    micro_lesson: dict | None
    help_channels: list[str]


class DeviceMessageOut(BaseModel):
    """What the phone may know: never the parent insight or the rationale."""

    conversation_id: str
    queued: bool
    message_index: int | None = None
    level: str | None = None
    raised: bool | None = None
    nudge: DeviceNudge | None = None


def _conversation(db: Session, device: Device, body: DeviceMessageIn) -> Conversation:
    def find():
        return db.scalar(
            select(Conversation).where(
                Conversation.device_id == device.id, Conversation.thread_key == body.thread_key
            )
        )

    conversation = find()
    if conversation is None:
        conversation = Conversation(
            child_id=device.child_id,
            channel=body.channel.value,
            device_id=device.id,
            thread_key=body.thread_key,
            app=body.app,
        )
        db.add(conversation)
        try:
            db.flush()
        except IntegrityError:  # the same thread arrived twice at once
            db.rollback()
            conversation = find()
            assert conversation is not None
    return conversation


@device_router.post("/messages", status_code=status.HTTP_202_ACCEPTED)
async def device_message(
    body: DeviceMessageIn,
    request: Request,
    response: Response,
    db: DbDep,
    device: DeviceDep,
    settings: SettingsDep,
    wait: bool = False,
) -> DeviceMessageOut:
    """A flagged message, masked on the phone. Answers at once; the level and any nudge
    arrive on the live stream. wait=true answers after analysis (simulator and tests)."""
    _require(db, device, Scope.PERCAKAPAN)
    limiter = state_item(
        request.app.state,
        "device_limiter",
        lambda: RateLimiter(settings.device_messages_per_minute),
    )
    if not limiter.allow(device.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "too many messages", headers={"Retry-After": "60"}
        )
    child = db.get(ChildProfile, device.child_id)
    guardian = db.get(Guardian, child.guardian_id) if child else None
    assert child is not None and guardian is not None
    conversation = _conversation(db, device, body)
    db.commit()
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
            device_id=device.id,
        ),
        wait=wait,
    )
    if fut is None:
        return DeviceMessageOut(conversation_id=str(conversation.id), queued=True)
    try:
        result = await fut
    except ConsentWithdrawn as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent withdrawn") from exc
    except ConversationGone as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found") from exc
    response.status_code = status.HTTP_200_OK
    nudge = None
    if result.coach is not None:
        out = result.coach.output
        nudge = DeviceNudge(
            situation=result.coach.situation.value,
            child_nudge=out.child_nudge,
            micro_lesson=out.micro_lesson.model_dump() if out.micro_lesson else None,
            help_channels=list(result.coach.help_channels),
        )
    return DeviceMessageOut(
        conversation_id=str(conversation.id),
        queued=False,
        message_index=result.step.index,
        level=result.step.level.value,
        raised=result.step.raised,
        nudge=nudge,
    )


class ImageSignalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_key: ThreadKey | None = None
    trigger: ImageTrigger
    sender: Literal["child", "contact"] | None = None
    category: ImageCategory
    action: ImageAction
    score: int = Field(ge=0, le=100)
    model_version: ModelVersion


class ImageSignalOut(BaseModel):
    id: str
    event: str | None


def image_event(body: ImageSignalIn) -> tuple[str, str] | None:
    """(event kind, level) for the parent, or None. The image itself never arrives."""
    if body.category in (ImageCategory.SEKSUAL, ImageCategory.KEKERASAN):
        level = "perhatian" if body.trigger == ImageTrigger.SITUS else "waspada"
        return "gambar_sensitif", level
    if body.category in (ImageCategory.TEKS_PRIBADI, ImageCategory.WAJAH) and (
        body.trigger == ImageTrigger.DIBAGIKAN
    ):
        return "gambar_data_pribadi", "perhatian"
    return None


@device_router.post("/images", status_code=status.HTTP_201_CREATED)
def image_signal(
    body: ImageSignalIn, request: Request, db: DbDep, device: DeviceDep
) -> ImageSignalOut:
    """The label of an image judged on the phone: category, action, score, model."""
    _require(db, device, Scope.GAMBAR)
    conversation_id = None
    if body.thread_key is not None:
        conversation_id = db.scalar(
            select(Conversation.id).where(
                Conversation.device_id == device.id, Conversation.thread_key == body.thread_key
            )
        )
    signal = ImageSignal(
        child_id=device.child_id,
        device_id=device.id,
        conversation_id=conversation_id,
        trigger=body.trigger.value,
        sender=body.sender,
        category=body.category.value,
        action=body.action.value,
        score=body.score,
        model_version=body.model_version,
    )
    db.add(signal)
    event = image_event(body)
    if event is not None:
        db.add(Event(child_id=device.child_id, kind=event[0], level=event[1]))
    db.commit()
    if event is not None:
        broker(request.app.state).publish(
            child_key(device.child_id),
            "event",
            {
                "kind": event[0],
                "level": event[1],
                "trigger": body.trigger.value,
                "category": body.category.value,
                "conversation_id": str(conversation_id) if conversation_id else None,
            },
        )
    return ImageSignalOut(id=str(signal.id), event=event[0] if event else None)


class FeedbackIn(BaseModel):
    """A detection the parent confirmed as wrong, on the child's phone (tier 2 learning)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["gambar", "teks", "domain"]
    category: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,20}$")]
    score: int = Field(ge=0, le=100)
    model_version: ModelVersion
    verdict: Literal["salah_deteksi"]
    # The phone sends this only after the parent's PIN; the field makes the contract explicit.
    confirmed_by_guardian: Literal[True]


@device_router.post("/detection-feedback", status_code=status.HTTP_204_NO_CONTENT)
def detection_feedback(body: FeedbackIn, db: DbDep, device: DeviceDep) -> None:
    """Stored without the child, the device or the image. The score is rounded to 5 so a
    single row says even less about one moment on one phone."""
    db.add(
        DetectionFeedback(
            kind=body.kind,
            category=body.category,
            score=5 * round(body.score / 5),
            model_version=body.model_version,
            verdict=body.verdict,
        )
    )
    db.commit()


@device_router.get("/stream")
async def device_stream(
    request: Request, db: DbDep, device: DeviceDep, settings: SettingsDep
) -> StreamingResponse:
    key = device_key(device.id)
    db.commit()
    db.close()
    return _sse(request, key, settings)


def _sse(request: Request, key: str, settings) -> StreamingResponse:
    return StreamingResponse(
        sse_stream(
            broker(request.app.state),
            key,
            request.headers.get("last-event-id"),
            heartbeat=settings.sse_heartbeat_seconds,
            max_seconds=settings.sse_max_seconds,
            is_disconnected=request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
