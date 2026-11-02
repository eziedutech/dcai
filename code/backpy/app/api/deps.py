"""Request dependencies: database session, the signed-in guardian, owned children, and
the paired phone."""

import logging
import uuid
from collections.abc import Iterator
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from app.auth.security import DEVICE_TOKEN_PREFIX, hash_device_token, read_access_token
from app.config import Settings
from app.db.base import session_factory, utcnow
from app.db.models import ChildProfile, Device, Guardian, SchoolStaff

_bearer = HTTPBearer(auto_error=False)
log = logging.getLogger("dcai.device")

# A phone bursts several requests at once after a restart. Writing last_seen_at on every one
# made them queue on the same device row until the lock timeout failed a message (2 Nov).
LAST_SEEN_EVERY = timedelta(seconds=60)


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_db(settings: Annotated[Settings, Depends(get_settings_dep)]) -> Iterator[Session]:
    with session_factory(settings.database_url)() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbDep = Annotated[Session, Depends(get_db)]


def current_guardian(
    db: DbDep,
    settings: SettingsDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Guardian:
    guardian_id = read_access_token(creds.credentials, settings.secret_key) if creds else None
    guardian = db.get(Guardian, guardian_id) if guardian_id else None
    if guardian is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "not signed in or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return guardian


GuardianDep = Annotated[Guardian, Depends(current_guardian)]


def owned_child(db: Session, guardian: Guardian, child_id: uuid.UUID) -> ChildProfile:
    """The child, if it belongs to this guardian. Another guardian's child answers 404, the
    same as a missing one, so ids cannot be probed."""
    child = db.get(ChildProfile, child_id)
    if child is None or child.guardian_id != guardian.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "child not found")
    return child


def current_device(
    db: DbDep, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Device:
    token = creds.credentials if creds else ""
    device = (
        db.scalar(select(Device).where(Device.token_hash == hash_device_token(token)))
        if token.startswith(DEVICE_TOKEN_PREFIX)
        else None
    )
    if device is None or device.revoked_at is not None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "device not paired or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    touch_last_seen(db, device)
    return device


def touch_last_seen(db: Session, device: Device) -> None:
    """Record that the phone was seen, at most once a minute, in its own short transaction
    that skips a locked row. A lost last_seen_at is harmless; a request failed by it is not,
    so the request session never carries this write."""
    now = utcnow()
    if device.last_seen_at is not None and now - device.last_seen_at < LAST_SEEN_EVERY:
        return
    try:
        with Session(db.get_bind()) as side, side.begin():
            row = side.scalar(
                select(Device.id).where(Device.id == device.id).with_for_update(skip_locked=True)
            )
            if row is None:  # another request holds the row; it is being seen anyway
                return
            side.execute(update(Device).where(Device.id == device.id).values(last_seen_at=now))
    except DBAPIError as exc:
        log.warning("last_seen_at not updated: %s", type(exc.orig or exc).__name__)
        return
    set_committed_value(device, "last_seen_at", now)


DeviceDep = Annotated[Device, Depends(current_device)]


def current_staff(
    db: DbDep,
    settings: SettingsDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> SchoolStaff:
    """A signed-in school staff account. A guardian or device token resolves to no staff
    row, so it cannot reach staff endpoints."""
    staff_id = read_access_token(creds.credentials, settings.secret_key) if creds else None
    staff = db.get(SchoolStaff, staff_id) if staff_id else None
    if staff is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "not signed in or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return staff


StaffDep = Annotated[SchoolStaff, Depends(current_staff)]
