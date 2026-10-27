"""Guardian accounts: register, login, refresh (rotating), logout."""

from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import audit
from app.api.deps import DbDep, GuardianDep, SettingsDep
from app.auth.security import (
    hash_password,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
    verify_password,
)
from app.config import Settings
from app.db.base import utcnow
from app.db.models import Guardian, RefreshToken

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    language: Literal["id", "en"] = "id"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(max_length=200)


class GuardianOut(BaseModel):
    id: str
    email: str
    name: str
    language: str


class TokensOut(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 (a scheme name, not a secret)
    guardian: GuardianOut


def _guardian_out(g: Guardian) -> GuardianOut:
    return GuardianOut(id=str(g.id), email=g.email, name=g.name, language=g.language)


def _issue(db: Session, settings: Settings, guardian: Guardian) -> TokensOut:
    if not settings.secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_KEY is not configured")
    access, expires = issue_access_token(
        guardian.id, settings.secret_key, settings.access_token_minutes
    )
    refresh, refresh_hash = new_refresh_token()
    db.add(
        RefreshToken(
            guardian_id=guardian.id,
            token_hash=refresh_hash,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    return TokensOut(
        access_token=access,
        access_expires_at=expires,
        refresh_token=refresh,
        guardian=_guardian_out(guardian),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: DbDep, settings: SettingsDep) -> TokensOut:
    guardian = Guardian(
        email=body.email.lower(),
        name=body.name,
        language=body.language,
        password_hash=hash_password(body.password),
    )
    db.add(guardian)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from None
    audit.record(db, audit.guardian_actor(guardian.id), "guardian_registered", guardian.id)
    return _issue(db, settings, guardian)


@router.post("/login")
def login(body: LoginIn, db: DbDep, settings: SettingsDep) -> TokensOut:
    guardian = db.scalar(select(Guardian).where(Guardian.email == body.email.lower()))
    if not verify_password(guardian.password_hash if guardian else None, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "email or password is wrong")
    assert guardian is not None
    audit.record(db, audit.guardian_actor(guardian.id), "guardian_login", guardian.id)
    return _issue(db, settings, guardian)


@router.post("/refresh")
def refresh(body: RefreshIn, db: DbDep, settings: SettingsDep) -> TokensOut:
    row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
        )
    )
    now = utcnow()
    if row is None or row.expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token invalid or expired")
    if row.revoked_at is not None:
        # A used token came back: someone else may hold it. End every session of this account.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.guardian_id == row.guardian_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        audit.record(db, "system", "refresh_token_reuse", row.guardian_id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token invalid or expired")
    row.revoked_at = now
    guardian = db.get(Guardian, row.guardian_id)
    assert guardian is not None
    return _issue(db, settings, guardian)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshIn, db: DbDep, guardian: GuardianDep) -> None:
    row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
        )
    )
    if row is not None and row.guardian_id == guardian.id and row.revoked_at is None:
        row.revoked_at = utcnow()
    audit.record(db, audit.guardian_actor(guardian.id), "guardian_logout", guardian.id)
    db.commit()


@router.get("/me")
def me(guardian: GuardianDep) -> GuardianOut:
    return _guardian_out(guardian)


class MeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None
    ) = None
    language: Literal["id", "en"] | None = None


@router.patch("/me")
def update_me(body: MeIn, db: DbDep, guardian: GuardianDep) -> GuardianOut:
    """Name and language. The language also sets the Coach and the phone's language."""
    if body.name is not None:
        guardian.name = body.name
    if body.language is not None:
        guardian.language = body.language
    db.commit()
    return _guardian_out(guardian)
