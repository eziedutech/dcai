"""Passwords (Argon2) and tokens: a short-lived JWT for access, an opaque rotating refresh
token stored only as a SHA-256 hash."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.db.base import utcnow

_hasher = PasswordHasher()
# Verifying against a real hash when the email is unknown keeps login timing uniform.
_DUMMY_HASH = _hasher.hash("dcai-dummy-password-for-timing")
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except VerificationError, InvalidHashError:
        return False


def issue_access_token(guardian_id: uuid.UUID, secret: str, minutes: int) -> tuple[str, datetime]:
    now = utcnow()
    expires = now + timedelta(minutes=minutes)
    claims = {
        "sub": str(guardian_id),
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(claims, secret, algorithm=_ALGORITHM), expires


def read_access_token(token: str, secret: str) -> uuid.UUID | None:
    try:
        claims = jwt.decode(
            token, secret, algorithms=[_ALGORITHM], options={"require": ["exp", "sub", "typ"]}
        )
    except jwt.PyJWTError:
        return None
    if claims.get("typ") != "access":
        return None
    try:
        return uuid.UUID(claims["sub"])
    except ValueError:
        return None


def new_refresh_token() -> tuple[str, str]:
    """Returns (token for the client, hash for the database)."""
    token = secrets.token_urlsafe(32)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
