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


# Pairing codes are read off the dashboard and typed on the phone: no 0/O, 1/I/L.
_PAIRING_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
PAIRING_CODE_LENGTH = 8
DEVICE_TOKEN_PREFIX = "dcd_"  # noqa: S105  (a label, not a secret)


def new_pairing_code() -> tuple[str, str]:
    """Returns (code shown to the guardian, hash for the database). 31^8 codes, single
    use, minutes to live."""
    code = "".join(secrets.choice(_PAIRING_ALPHABET) for _ in range(PAIRING_CODE_LENGTH))
    return code, hash_pairing_code(code)


def hash_pairing_code(code: str) -> str:
    normalized = "".join(ch for ch in code.upper() if ch.isalnum())
    return hashlib.sha256(f"pairing:{normalized}".encode()).hexdigest()


def new_device_token() -> tuple[str, str]:
    """Returns (token kept on the phone, hash for the database)."""
    token = DEVICE_TOKEN_PREFIX + secrets.token_urlsafe(32)
    return token, hash_device_token(token)


def hash_device_token(token: str) -> str:
    return hashlib.sha256(f"device:{token}".encode()).hexdigest()


CLASS_CODE_LENGTH = 6


def new_class_code() -> tuple[str, str]:
    """A class join code a teacher shares; a parent types it to let their child be counted
    (proposal 0004). Returns (code shown to the teacher, hash for the database)."""
    code = "".join(secrets.choice(_PAIRING_ALPHABET) for _ in range(CLASS_CODE_LENGTH))
    return code, hash_class_code(code)


def hash_class_code(code: str) -> str:
    normalized = "".join(ch for ch in code.upper() if ch.isalnum())
    return hashlib.sha256(f"class:{normalized}".encode()).hexdigest()
