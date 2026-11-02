"""Consent checks. Analysis for a child runs only while the latest record for the scope
is a grant (spec section 10), and while no material change to the consent text for that
scope is waiting for the parent (proposal 0005)."""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consent.texts import VERSIONS, ConsentText, Scope
from app.db.models import ConsentRecord


@dataclass(frozen=True)
class Review:
    """Changes to the consent text since the parent agreed, for the scopes they granted."""

    scopes: list[Scope]
    changes: list[ConsentText]

    @property
    def material(self) -> bool:
        return any(c.material for c in self.changes)


def granted_versions(db: Session, child_id: uuid.UUID) -> dict[Scope, str]:
    """Granted scopes with the text version of the grant. Records are append-only, so the
    newest record per scope decides."""
    rows = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.child_id == child_id)
        .order_by(ConsentRecord.created_at, ConsentRecord.id)
    ).all()
    state: dict[Scope, str | None] = {}
    for row in rows:
        for scope in row.scopes:
            state[Scope(scope)] = row.text_version if row.action == "grant" else None
    return {scope: version for scope, version in state.items() if version is not None}


def _changes_since(
    version: str, scope: Scope, versions: Mapping[str, ConsentText]
) -> list[ConsentText]:
    """Later versions (in publication order) that changed this scope's wording."""
    order = list(versions)
    if version not in versions:
        return []
    return [versions[v] for v in order[order.index(version) + 1 :] if scope in versions[v].changed]


def review(
    db: Session, child_id: uuid.UUID, versions: Mapping[str, ConsentText] = VERSIONS
) -> Review | None:
    granted = granted_versions(db, child_id)
    scopes: list[Scope] = []
    changes: dict[str, ConsentText] = {}
    for scope, version in sorted(granted.items()):
        found = _changes_since(version, scope, versions)
        if found:
            scopes.append(scope)
            changes.update((c.version, c) for c in found)
    if not scopes:
        return None
    return Review(scopes=scopes, changes=[versions[v] for v in versions if v in changes])


def active_scopes(
    db: Session, child_id: uuid.UUID, versions: Mapping[str, ConsentText] = VERSIONS
) -> set[Scope]:
    """Granted scopes, minus those with a material change the parent has not agreed to."""
    return {
        scope
        for scope, version in granted_versions(db, child_id).items()
        if not any(c.material for c in _changes_since(version, scope, versions))
    }


def has_consent(db: Session, child_id: uuid.UUID, scope: Scope) -> bool:
    return scope in active_scopes(db, child_id)
