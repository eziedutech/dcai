"""Build the phone's site lists from UT1 Blacklists (CC BY-SA 4.0).

    uv run python -m app.blocklist.build                 # download from UT1
    uv run python -m app.blocklist.build --source DIR    # local copy: DIR/<ut1 cat>/domains*

Writes data/blocklist/<category>.bin and manifest.json. The output is an adaptation of
UT1's lists and carries the same license; the manifest says so and the phone shows it.
Generated files are not committed: they are large and refreshed from the source.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.blocklist.lists import CATEGORIES, LICENSE, SOURCE, encode

OUT_DIR = Path(__file__).resolve().parents[4] / "data" / "blocklist"
# One archive per category from UT1 itself: no API rate limit, the same lists the mirror holds.
UT1_ARCHIVE = "https://dsi.ut-capitole.fr/blacklists/download/{cat}.tar.gz"


def _remote_lines(cat: str, http: httpx.Client):
    with tempfile.TemporaryFile() as tmp:
        with http.stream("GET", UT1_ARCHIVE.format(cat=cat), timeout=300) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_bytes():
                tmp.write(chunk)
        tmp.seek(0)
        with tarfile.open(fileobj=tmp, mode="r:gz") as tar:
            # Large categories may be split into domains.0, domains.1, ...
            members = [
                m
                for m in tar.getmembers()
                if m.isfile() and Path(m.name).name.split(".")[0] == "domains"
            ]
            for m in sorted(members, key=lambda m: m.name):
                fh = tar.extractfile(m)
                if fh is not None:
                    for raw in fh:
                        yield raw.decode("utf-8", errors="ignore")


def _local_lines(source: Path, cat: str):
    for path in sorted((source / cat).glob("domains*")):
        with path.open(encoding="utf-8", errors="ignore") as fh:
            yield from fh


def build(out_dir: Path = OUT_DIR, source: Path | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    version = datetime.now(UTC).strftime("%Y%m%d%H%M")
    entries = []
    with httpx.Client(follow_redirects=True) as http:
        for category in CATEGORIES:
            # Streamed: the adult list alone is millions of lines.
            lines = itertools.chain.from_iterable(
                _local_lines(source, cat) if source else _remote_lines(cat, http)
                for cat in category.sources
            )
            blob, count = encode(lines)
            (out_dir / f"{category.name}.bin").write_bytes(blob)
            entries.append(
                {
                    "name": category.name,
                    "count": count,
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                }
            )
            print(f"{category.name}: {count} domains, {len(blob) / 1e6:.1f} MB")
    manifest = {"version": version, "source": SOURCE, "license": LICENSE, "categories": entries}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", type=Path, help="local UT1 copy instead of downloading")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    build(args.out, args.source)


if __name__ == "__main__":
    main()
