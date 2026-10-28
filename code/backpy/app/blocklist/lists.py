"""The site list format shared with the phone.

A category file holds the sorted, unique first 5 bytes of SHA-256 over each normalised
domain. The phone binary-searches it for a looked-up name and its parent domains, so the
list on the phone holds no readable domain names, and a match sends only the category.

At about 5 million entries, 40 bits leave a false match about once in 200,000 checks;
the parent can allow a site on the phone when that happens.

File: b"DCBL" | format byte (1) | entry count (4 bytes, big endian) | entries (5 bytes each).
"""

from __future__ import annotations

import hashlib
import ipaddress
import struct
from dataclasses import dataclass

MAGIC = b"DCBL"
FORMAT = 1
HASH_BYTES = 5
HEADER = struct.Struct(">4sBI")

LICENSE = "CC BY-SA 4.0"
SOURCE = "UT1 Blacklists, Universite Toulouse Capitole (dsi.ut-capitole.fr/blacklists)"


@dataclass(frozen=True)
class Category:
    name: str  # wire name, also the event kind suffix
    sources: tuple[str, ...]  # UT1 category directories
    level: str  # event level for the parent


# Categories that matter for a child aged 10 to 17. UT1 has no violence category;
# "agressif" (aggressive, hateful sites) is the closest.
CATEGORIES: tuple[Category, ...] = (
    Category("dewasa", ("adult",), "perhatian"),
    Category("judi", ("gambling",), "perhatian"),
    Category("penipuan", ("phishing",), "perhatian"),
    Category("berbahaya", ("malware",), "aman"),
    Category("kencan", ("dating",), "perhatian"),
    Category("narkoba", ("drogue",), "perhatian"),
    Category("kebencian", ("agressif",), "perhatian"),
)
BY_NAME = {c.name: c for c in CATEGORIES}


def normalise(domain: str) -> str | None:
    """Lowercase, no leading dot or 'www.', no trailing dot. None for IPs and junk."""
    d = domain.strip().lower().lstrip(".").rstrip(".")
    if d.startswith("www."):
        d = d[4:]
    if not d or "." not in d or "/" in d or " " in d or len(d) > 253:
        return None
    try:
        ipaddress.ip_address(d)
        return None
    except ValueError:
        return d


def domain_hash(domain: str) -> bytes:
    # DNS names arrive as ASCII (internationalised names in punycode); UTF-8 covers both.
    return hashlib.sha256(domain.encode("utf-8")).digest()[:HASH_BYTES]


def encode(domains) -> tuple[bytes, int]:
    hashes = sorted({domain_hash(d) for raw in domains if (d := normalise(raw))})
    return HEADER.pack(MAGIC, FORMAT, len(hashes)) + b"".join(hashes), len(hashes)


def decode_count(blob: bytes) -> int:
    magic, fmt, count = HEADER.unpack_from(blob)
    if magic != MAGIC or fmt != FORMAT or len(blob) != HEADER.size + count * HASH_BYTES:
        raise ValueError("not a dcAI site list")
    return count


def contains(blob: bytes, domain: str) -> bool:
    """Reference lookup, the same walk the phone does: the name, then each parent domain
    down to two labels."""
    count = decode_count(blob)
    d = normalise(domain)
    if d is None:
        return False
    labels = d.split(".")
    for i in range(len(labels) - 1):
        target = domain_hash(".".join(labels[i:]))
        lo, hi = 0, count
        while lo < hi:
            mid = (lo + hi) // 2
            off = HEADER.size + mid * HASH_BYTES
            entry = blob[off : off + HASH_BYTES]
            if entry < target:
                lo = mid + 1
            elif entry > target:
                hi = mid
            else:
                return True
    return False
