"""Project text rules that a typo can break silently: no emdash or en dash anywhere, and no
control characters (a backspace once replaced a regex word boundary without any error)."""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
_FORBIDDEN = {"\u2014": "emdash", "\u2013": "en dash", "\x08": "backspace", "\x00": "NUL"}
_TEXT = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".ini", ".mako", ".txt", ".example"}


def _tracked_and_new() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\n")
    return [REPO / p for p in out if p and Path(p).suffix in _TEXT]


def test_no_forbidden_characters_in_repo_text():
    problems = []
    for path in _tracked_and_new():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for ch, name in _FORBIDDEN.items():
            if ch in text:
                problems.append(f"{path.relative_to(REPO)}: {name}")
    assert problems == []
