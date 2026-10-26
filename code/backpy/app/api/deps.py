"""Request dependencies: database session, the signed-in guardian, owned children."""

import uuid
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import read_access_token
from app.config import Settings
from app.db.base import session_factory
from app.db.models import ChildProfile, Guardian

_bearer = HTTPBearer(auto_error=False)


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
