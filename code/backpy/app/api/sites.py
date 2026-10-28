"""Site categories on the child's phone (scope "situs", wire name "domain").

The phone downloads the category lists, matches looked-up names on the phone, and reports
only the category of a held site. The site's name, the time of every lookup and the
browsing history never reach the server.
"""

import json
from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import select

from app.analysis.service import broker
from app.api.deps import DbDep, DeviceDep, SettingsDep
from app.api.devices import _require
from app.blocklist.build import OUT_DIR
from app.blocklist.lists import BY_NAME
from app.consent.texts import Scope
from app.db.base import utcnow
from app.db.models import Event
from app.live.broker import child_key

router = APIRouter(prefix="/device/sites", tags=["device"])


def _dir(settings) -> Path:
    return Path(settings.site_lists_dir) if settings.site_lists_dir else OUT_DIR


def _manifest(settings) -> dict:
    path = _dir(settings) / "manifest.json"
    if not path.exists():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "site lists are not built")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("")
def site_lists(db: DbDep, device: DeviceDep, settings: SettingsDep) -> dict:
    """Version, source and license, and one entry per category the phone can download."""
    _require(db, device, Scope.DOMAIN)
    return _manifest(settings)


@router.get("/{name}")
def site_list(
    name: str, request: Request, db: DbDep, device: DeviceDep, settings: SettingsDep
) -> Response:
    _require(db, device, Scope.DOMAIN)
    entry = next((c for c in _manifest(settings)["categories"] if c["name"] == name), None)
    if entry is None or name not in BY_NAME:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown category")
    etag = f'"{entry["sha256"]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    # Streamed in chunks: the adult list is over 20 MB.
    path = _dir(settings) / f"{name}.bin"
    return FileResponse(path, media_type="application/octet-stream", headers={"ETag": etag})


CategoryName = Annotated[str, StringConstraints(pattern=r"^[a-z]{3,20}$")]
ListVersion = Annotated[str, StringConstraints(pattern=r"^[0-9]{8,14}$")]


class SiteSignalIn(BaseModel):
    """A site held on the phone. There is no field for the site's name."""

    model_config = ConfigDict(extra="forbid")

    category: CategoryName
    list_version: ListVersion


class SiteSignalOut(BaseModel):
    event: str | None


@router.post("/signals", status_code=status.HTTP_201_CREATED)
def site_signal(
    body: SiteSignalIn, request: Request, db: DbDep, device: DeviceDep, settings: SettingsDep
) -> SiteSignalOut:
    _require(db, device, Scope.DOMAIN)
    category = BY_NAME.get(body.category)
    if category is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category")
    kind = f"situs_{category.name}"
    # One page loads many names; a burst in the same category is one moment for the parent.
    since = utcnow() - timedelta(minutes=settings.site_event_minutes)
    recent = db.scalar(
        select(Event.id).where(
            Event.child_id == device.child_id, Event.kind == kind, Event.created_at >= since
        )
    )
    if recent is not None:
        return SiteSignalOut(event=None)
    db.add(Event(child_id=device.child_id, kind=kind, level=category.level))
    db.commit()
    broker(request.app.state).publish(
        child_key(device.child_id), "event", {"kind": kind, "level": category.level}
    )
    return SiteSignalOut(event=kind)
