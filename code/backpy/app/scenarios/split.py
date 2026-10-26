"""Deterministic 70/30 dev/test split, stratified by group (spec section 11, rule 5).

    python -m app.scenarios.split          write data/scenarios/split.json if missing
    python -m app.scenarios.split --check  fail if the file disagrees with the dataset

The test set is locked: prompts and thresholds are tuned on dev only. Assignment depends
only on each id (a hash), so adding scenarios never moves an existing one between sets.
Removing a rejected scenario just drops its id.
"""

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from app.scenarios.validate import DEFAULT_DIR, load

SPLIT_FILE = DEFAULT_DIR / "split.json"
TEST_FRACTION = 0.3
_SALT = "dcai-split-v1"


def _rank(scenario_id: str) -> str:
    return hashlib.sha256(f"{_SALT}:{scenario_id}".encode()).hexdigest()


def compute(ids_by_group: dict[str, list[str]]) -> dict[str, list[str]]:
    dev, test = [], []
    for _group, ids in sorted(ids_by_group.items()):
        ranked = sorted(ids, key=_rank)
        n_test = math.floor(len(ranked) * TEST_FRACTION + 0.5) if len(ranked) > 1 else 0
        test.extend(ranked[:n_test])
        dev.extend(ranked[n_test:])
    return {"dev": sorted(dev), "test": sorted(test)}


def load_split(path: Path = SPLIT_FILE) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"dev": data["dev"], "test": data["test"]}


def main(argv: list[str]) -> int:
    scenarios, errors = load(DEFAULT_DIR)
    if errors:
        print("dataset has errors; run python -m app.scenarios.validate")
        return 1
    by_group: dict[str, list[str]] = defaultdict(list)
    for s in scenarios:
        by_group[s.group.value].append(s.id)
    split = compute(by_group)
    if argv == ["--check"]:
        if not SPLIT_FILE.exists():
            print("split.json missing")
            return 1
        stored = load_split()
        if stored != split:
            print("split.json does not match the dataset")
            return 1
        print(f"split ok: dev {len(split['dev'])}, test {len(split['test'])}")
        return 0
    if SPLIT_FILE.exists():
        print("split.json exists; it is locked. Use --check.")
        return 1
    SPLIT_FILE.write_text(
        json.dumps(
            {
                "about": "Locked split. Tune prompts and thresholds on dev only.",
                "method": f"sha256('{_SALT}:' + id), lowest {int(TEST_FRACTION * 100)}% per "
                "group to test (rounded half up)",
                **split,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {SPLIT_FILE}: dev {len(split['dev'])}, test {len(split['test'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
