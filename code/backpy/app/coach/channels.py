"""Help channels from data/coach/channels.json. Only manually verified entries carry a
number or a link; the model never writes one (spec section 8.3)."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CHANNELS_FILE = Path(__file__).resolve().parents[4] / "data" / "coach" / "channels.json"


@dataclass(frozen=True)
class Channel:
    name: str
    contact: str  # number or link, as verified
    purpose: str
    verified_by: str
    verified_on: str


@dataclass(frozen=True)
class Channels:
    general: dict[str, tuple[str, ...]]
    verified: tuple[Channel, ...]
    distress: dict[str, tuple[str, ...]] | None = None

    def lines(self, language: str, distress: bool = False) -> list[str]:
        base = self.distress if distress and self.distress else self.general
        out = list(base.get(language, base["id"]))
        out += [f"{c.name}: {c.contact} ({c.purpose})" for c in self.verified]
        return out


@lru_cache
def load_channels(path: Path = CHANNELS_FILE) -> Channels:
    data = json.loads(path.read_text(encoding="utf-8"))
    verified = []
    for entry in data.get("verified", []):
        if not (
            entry.get("verified") is True and entry.get("verified_by") and entry.get("verified_on")
        ):
            continue  # unverified entries are never shown
        verified.append(
            Channel(
                name=entry["name"],
                contact=entry["contact"],
                purpose=entry["purpose"],
                verified_by=entry["verified_by"],
                verified_on=entry["verified_on"],
            )
        )
    general = {lang: tuple(lines) for lang, lines in data["general"].items()}
    distress = {lang: tuple(lines) for lang, lines in data.get("distress", {}).items()} or None
    return Channels(general=general, verified=tuple(verified), distress=distress)
