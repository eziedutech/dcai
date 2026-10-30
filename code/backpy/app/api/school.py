"""School module endpoints (proposal 0004, aggregate-only).

Staff accounts sign in like guardians but can only read aggregate counts for their own
school's classes, never a child's level, insight or identity. Class membership and the
parent consent that creates it are added in a later phase; here a class is created with a
join code, and a class overview returns k-anon counts for the children already in it.
"""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import audit
from app.api.deps import DbDep, SettingsDep, StaffDep
from app.auth.security import (
    hash_password,
    issue_access_token,
    new_class_code,
    verify_password,
)
from app.db.models import ClassMembership, Classroom, School, SchoolStaff
from app.school.service import class_counts

router = APIRouter(prefix="/school", tags=["school"])

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class StaffRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    name: Name
    school_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]


class StaffLoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class StaffOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    school_id: str


class StaffTokenOut(BaseModel):
    # No refresh token yet: staff sessions use a short-lived access token for now.
    access_token: str
    access_expires_at: datetime
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 (a scheme name, not a secret)
    staff: StaffOut


def _staff_out(s: SchoolStaff) -> StaffOut:
    return StaffOut(
        id=str(s.id), email=s.email, name=s.name, role=s.role, school_id=str(s.school_id)
    )


def _token(settings, staff: SchoolStaff) -> StaffTokenOut:
    if not settings.secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_KEY is not configured")
    access, expires = issue_access_token(
        staff.id, settings.secret_key, settings.access_token_minutes
    )
    return StaffTokenOut(access_token=access, access_expires_at=expires, staff=_staff_out(staff))


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: StaffRegisterIn, db: DbDep, settings: SettingsDep) -> StaffTokenOut:
    """Create a school and its first staff account (role kepala)."""
    school = School(name=body.school_name)
    db.add(school)
    db.flush()
    staff = SchoolStaff(
        school_id=school.id,
        email=body.email.lower(),
        name=body.name,
        role="kepala",
        password_hash=hash_password(body.password),
    )
    db.add(staff)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from None
    audit.record(db, f"staff:{staff.id}", "school_registered", school.id)
    db.commit()
    return _token(settings, staff)


@router.post("/login")
def login(body: StaffLoginIn, db: DbDep, settings: SettingsDep) -> StaffTokenOut:
    staff = db.scalar(select(SchoolStaff).where(SchoolStaff.email == body.email.lower()))
    if not verify_password(staff.password_hash if staff else None, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "email or password is wrong")
    assert staff is not None
    return _token(settings, staff)


@router.get("/me")
def me(staff: StaffDep) -> StaffOut:
    return _staff_out(staff)


class ClassIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name


class ClassOut(BaseModel):
    id: str
    name: str
    members: int
    # The join code is returned only when the class is created, never listed again.
    join_code: str | None = None


@router.post("/classes", status_code=status.HTTP_201_CREATED)
def create_class(body: ClassIn, db: DbDep, staff: StaffDep) -> ClassOut:
    code, code_hash = new_class_code()
    room = Classroom(school_id=staff.school_id, name=body.name, join_code_hash=code_hash)
    db.add(room)
    db.commit()
    audit.record(db, f"staff:{staff.id}", "class_created", room.id)
    db.commit()
    return ClassOut(id=str(room.id), name=room.name, members=0, join_code=code)


@router.get("/classes")
def list_classes(db: DbDep, staff: StaffDep) -> list[ClassOut]:
    counts = dict(
        db.execute(
            select(ClassMembership.classroom_id, func.count()).group_by(
                ClassMembership.classroom_id
            )
        ).all()
    )
    rooms = db.scalars(
        select(Classroom)
        .where(Classroom.school_id == staff.school_id)
        .order_by(Classroom.created_at)
    ).all()
    return [ClassOut(id=str(r.id), name=r.name, members=counts.get(r.id, 0)) for r in rooms]


class ClassOverviewOut(BaseModel):
    classroom_id: str
    window_days: int
    total: int
    # None when the class is too small to stay anonymous (below the k threshold).
    suppressed: bool
    by_level: dict[str, int] | None
    support: int | None


def _owned_class(db, staff: SchoolStaff, classroom_id) -> Classroom:
    room = db.get(Classroom, classroom_id)
    if room is None or room.school_id != staff.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "class not found")
    return room


@router.get("/classes/{classroom_id}/overview")
def class_overview(
    classroom_id: str, db: DbDep, staff: StaffDep, days: int = 7
) -> ClassOverviewOut:
    """k-anon counts per level for the class. Never a child's level, insight or identity."""
    import uuid

    try:
        cid = uuid.UUID(classroom_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "class not found") from None
    _owned_class(db, staff, cid)
    counts = class_counts(db, cid, days=days)
    return ClassOverviewOut(
        classroom_id=classroom_id,
        window_days=days,
        total=counts.total,
        suppressed=counts.suppressed,
        by_level=counts.by_level,
        support=counts.support,
    )
