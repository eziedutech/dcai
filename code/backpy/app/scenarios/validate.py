"""Validate every scenario file and print a summary.

    python -m app.scenarios.validate [scenario_dir]

Checks the schema, unique ids, and content rules that a schema cannot express: no emdash,
no explicit wording, and personal data that is visibly fake.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from app.scenarios.schema import Scenario

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DIR = REPO_ROOT / "data" / "scenarios"

_DASHES = ("\u2014", "\u2013", "\u2015")
# Safety net only; human review is the real check (spec section 11, rule 1 and 2).
_EXPLICIT = re.compile(
    r"\b(seks|seksi|sexy|sex|telanjang|bugil|nude|nudes|porn\w*|ciuman|cium|pacaran)\b", re.I
)
_EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")
_FAKE_EMAIL_DOMAIN = re.compile(r"@(example\.(com|org|net)|[\w-]+\.test)$", re.I)


def load(directory: Path) -> tuple[list[Scenario], list[str]]:
    scenarios: list[Scenario] = []
    errors: list[str] = []
    for path in sorted(directory.rglob("*.json")):
        if path.name == "split.json":
            continue
        rel = path.relative_to(directory)
        try:
            raw = path.read_text(encoding="utf-8")
            scenario = Scenario.model_validate(json.loads(raw))
        except (ValueError, ValidationError) as exc:
            errors.append(f"{rel}: {exc}")
            continue
        if path.stem != scenario.id:
            errors.append(f"{rel}: file name must equal id {scenario.id}")
        errors.extend(f"{rel}: {problem}" for problem in content_problems(scenario))
        scenarios.append(scenario)
    counts = Counter(s.id for s in scenarios)
    errors.extend(f"duplicate id {i}" for i, n in counts.items() if n > 1)
    return scenarios, errors


def content_problems(scenario: Scenario) -> list[str]:
    problems = []
    texts = [scenario.title, scenario.notes, *(m.text for m in scenario.messages)]
    for i, text in enumerate(texts):
        where = "title" if i == 0 else "notes" if i == 1 else f"message {i - 1}"
        if any(d in text for d in _DASHES):
            problems.append(f"{where}: emdash or en dash")
        if _EXPLICIT.search(text):
            problems.append(f"{where}: explicit or romantic wording")
        for m in _EMAIL.finditer(text):
            if not _FAKE_EMAIL_DOMAIN.search(m.group(0)):
                problems.append(f"{where}: email must use example.com or .test")
    return problems


def main(argv: list[str]) -> int:
    directory = Path(argv[0]) if argv else DEFAULT_DIR
    scenarios, errors = load(directory)
    by_group = Counter(s.group.value for s in scenarios)
    by_review = Counter(s.review.status.value for s in scenarios)
    messages = sum(len(s.messages) for s in scenarios)
    print(f"{len(scenarios)} valid scenarios, {messages} messages, in {directory}")
    for group, n in sorted(by_group.items()):
        print(f"  {group}: {n}")
    print(f"review: {dict(by_review)}")
    for e in errors:
        print(f"ERROR {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
