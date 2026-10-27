"""Child profiles and consent records."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import delete, select

from app import audit
from app.age import AgeRange
from app.api.deps import DbDep, GuardianDep, owned_child
from app.api.devices import notify_config_changed, notify_devices_revoked
from app.consent.service import active_scopes
from app.consent.texts import CURRENT, VERSIONS, Scope
from app.db.models import ChildProfile, ConsentRecord

router = APIRouter(tags=["children", "consent"])


class ChildIn(BaseModel):
    nickname: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    age_range: AgeRange


class ChildOut(BaseModel):
    id: str
    nickname: str
    age_range: str
    created_at: datetime
    consent_scopes: list[Scope]


class ConsentIn(BaseModel):
    child_id: uuid.UUID
    text_version: str
    action: Literal["grant", "revoke"] = "grant"
    scopes: list[Scope] = Field(min_length=1, max_length=len(Scope))


class ConsentOut(BaseModel):
    id: str
    child_id: str
    text_version: str
    action: str
    scopes: list[str]
    age_range: str
    created_at: datetime


class ConsentTextOut(BaseModel):
    version: str
    id: str
    en: str
    scopes: list[Scope]


def _child_out(db, child: ChildProfile) -> ChildOut:
    return ChildOut(
        id=str(child.id),
        nickname=child.nickname,
        age_range=child.age_range,
        created_at=child.created_at,
        consent_scopes=sorted(active_scopes(db, child.id)),
    )


def _consent_out(r: ConsentRecord) -> ConsentOut:
    return ConsentOut(
        id=str(r.id),
        child_id=str(r.child_id),
        text_version=r.text_version,
        action=r.action,
        scopes=r.scopes,
        age_range=r.age_range,
        created_at=r.created_at,
    )


@router.post("/children", status_code=status.HTTP_201_CREATED)
def add_child(body: ChildIn, db: DbDep, guardian: GuardianDep) -> ChildOut:
    child = ChildProfile(guardian_id=guardian.id, nickname=body.nickname, age_range=body.age_range)
    db.add(child)
    db.flush()
    audit.record(db, audit.guardian_actor(guardian.id), "child_added", child.id)
    db.commit()
    return _child_out(db, child)


@router.get("/children")
def list_children(db: DbDep, guardian: GuardianDep) -> list[ChildOut]:
    children = db.scalars(
        select(ChildProfile)
        .where(ChildProfile.guardian_id == guardian.id)
        .order_by(ChildProfile.created_at)
    ).all()
    return [_child_out(db, c) for c in children]


@router.get("/consents/text")
def consent_text() -> ConsentTextOut:
    """The current consent text. Public, so it can be read before signing up."""
    return ConsentTextOut(
        version=CURRENT.version, id=CURRENT.id, en=CURRENT.en, scopes=list(CURRENT.scopes)
    )


@router.post("/consents", status_code=status.HTTP_201_CREATED)
def record_consent(
    body: ConsentIn, request: Request, db: DbDep, guardian: GuardianDep
) -> ConsentOut:
    child = owned_child(db, guardian, body.child_id)
    if body.text_version not in VERSIONS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown consent text version")
    if body.action == "grant" and body.text_version != CURRENT.version:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "consent must be given to the current text version"
        )
    if body.action == "grant" and not set(body.scopes) <= set(CURRENT.scopes):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "scope not covered by the consent text"
        )
    record = ConsentRecord(
        guardian_id=guardian.id,
        child_id=child.id,
        text_version=body.text_version,
        action=body.action,
        scopes=sorted(set(body.scopes)),
        age_range=child.age_range,
    )
    db.add(record)
    db.flush()
    audit.record(db, audit.guardian_actor(guardian.id), f"consent_{body.action}", child.id)
    db.commit()
    notify_config_changed(request.app.state, db, child.id)
    return _consent_out(record)


@router.get("/children/{child_id}/consents")
def consent_history(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> list[ConsentOut]:
    child = owned_child(db, guardian, child_id)
    rows = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.child_id == child.id)
        .order_by(ConsentRecord.created_at, ConsentRecord.id)
    ).all()
    return [_consent_out(r) for r in rows]


@router.delete("/children/{child_id}/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_child_data(
    child_id: uuid.UUID, request: Request, db: DbDep, guardian: GuardianDep
) -> None:
    """Erase the child and everything linked to it (cascade). The audit entry keeps only
    the child's id, so the erasure itself stays provable. Paired phones are told first, and
    their tokens end with the device rows."""
    child = owned_child(db, guardian, child_id)
    notify_devices_revoked(request.app.state, db, child.id)
    db.execute(delete(ChildProfile).where(ChildProfile.id == child.id))
    audit.record(db, audit.guardian_actor(guardian.id), "child_data_deleted", child.id)
    db.commit()
