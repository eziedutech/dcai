"""Run whole scenarios through the live pipeline and score them (spec section 11 metrics).

    python -m app.risk.pipeline_eval [--split dev|test] [--concurrency 4] [--tag NAME]

Uses the configured pools (SCREENING_ENDPOINTS, REASONING_ENDPOINTS). Dev split by default;
the test split is for the final evaluation only. Writes eval/pipeline/<split>.md and .json
(ids, levels and scores only, never text).
"""

import argparse
import asyncio
import itertools
import json
import statistics
import sys
import time
from collections import Counter

import httpx

from app.config import get_settings
from app.llm import build_clients
from app.risk.pipeline import ConversationAnalyzer
from app.risk.schemas import Level
from app.scenarios.schema import ContactRole, Group, Scenario
from app.scenarios.split import load_split
from app.scenarios.validate import DEFAULT_DIR, REPO_ROOT, load

OUT_DIR = REPO_ROOT / "eval" / "pipeline"
_RANK = {Level.AMAN: 0, Level.PERHATIAN: 1, Level.WASPADA: 2, Level.MENDESAK: 3}
_BENIGN = {Group.WAJAR, Group.KASUS_SULIT}


def contact_known(role: ContactRole) -> bool:
    # The simulator's view of the contact. A long-time online friend counts as known:
    # their risk has to show in behaviour, not in their status.
    return role != ContactRole.TAK_DIKENAL


async def run_one(s: Scenario, screening, reasoning) -> dict:
    a = ConversationAnalyzer(
        screening=screening,
        reasoning=reasoning,
        contact_known=contact_known(s.contact_role),
        channel=s.channel.value,
        age_range=s.child_age_range.value,
    )
    started = time.perf_counter()
    steps = []
    for m in s.messages:
        st = await a.add(m.sender.value, m.text)
        steps.append(st)
    first_raise = next((st.index for st in steps if st.level != Level.AMAN), None)
    stage2 = [st for st in steps if st.stage2_called]
    return {
        "scenario": s.id,
        "group": s.group.value,
        "expected": s.expected_final_level.value,
        "final": steps[-1].level.value,
        "scores": [st.score for st in steps],
        "sources": [st.source for st in steps],
        "risk_starts_at": s.risk_starts_at,
        "first_raise": first_raise,
        "stage2_calls": len(stage2),
        "stage2_model_used": sum(st.source == "model" for st in stage2),
        "stage1_unavailable": sum(st.stage1.status != "ok" for st in steps),
        "analysis_unavailable_steps": sum(not st.analysis_available for st in steps),
        "support_needed": steps[-1].support_needed,
        "expects_support": s.expects_support_response,
        "monotonic": all(x.score <= y.score for x, y in itertools.pairwise(steps)),
        "seconds": round(time.perf_counter() - started, 1),
    }


async def run(split: str, concurrency: int, tag: str = "") -> int:
    stem = f"{split}-{tag}" if tag else split
    settings = get_settings()
    ids = set(load_split()[split])
    scenarios = [s for s in load(DEFAULT_DIR)[0] if s.id in ids]
    sem = asyncio.Semaphore(concurrency)
    started = time.perf_counter()
    usage_log: list = []

    async with httpx.AsyncClient() as http:
        reasoning, screening = build_clients(settings, http)
        for pool in (reasoning, screening):
            _record_usage(pool, usage_log)

        async def one(s):
            async with sem:
                return await run_one(s, screening, reasoning)

        rows = await asyncio.gather(*(one(s) for s in scenarios))
    wall = time.perf_counter() - started
    rows.sort(key=lambda r: r["scenario"])

    risky = [r for r in rows if r["group"] == Group.PENDEKATAN_BERISIKO.value]
    benign = [r for r in rows if Group(r["group"]) in _BENIGN]
    caught = [r for r in risky if _RANK[Level(r["final"])] >= _RANK[Level.WASPADA]]
    alarms = [r for r in benign if _RANK[Level(r["final"])] >= _RANK[Level.WASPADA]]
    delays = [
        r["first_raise"] - r["risk_starts_at"]
        for r in rows
        if r["risk_starts_at"]
        and r["first_raise"] is not None
        and r["expected"] != Level.AMAN.value
    ]
    never_raised = [
        r["scenario"]
        for r in rows
        if r["expected"] != Level.AMAN.value and r["first_raise"] is None
    ]
    exact = sum(r["final"] == r["expected"] for r in rows)
    confusion = Counter((r["expected"], r["final"]) for r in rows)
    support_rows = [r for r in rows if r["expects_support"]]
    by_endpoint = Counter(u.endpoint for _, u in usage_log)
    cost = sum(u.cost_usd for _, u in usage_log if u.cost_usd is not None)
    unknown_cost_calls = sum(u.cost_usd is None for _, u in usage_log)
    lat_by_purpose: dict[str, list[int]] = {}
    for purpose, u in usage_log:
        lat_by_purpose.setdefault(purpose, []).append(u.latency_ms)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{stem}.json").write_text(
        json.dumps({"rows": rows}, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    levels = [lv.value for lv in Level]
    lines = [
        f"# Pipeline on the {split} split" + (f" ({tag})" if tag else ""),
        "",
        f"{len(rows)} synthetic scenarios, {sum(len(r['scores']) for r in rows)} messages, "
        f"each played message by message through stage 1, the rule floor and stage 2. "
        f"Expected levels are the dataset drafts, not yet reviewed by a person.",
        "",
        "| Measure | Result | Spec target |",
        "| --- | --- | --- |",
        f"| Risky approach reaching waspada or higher | {len(caught)} of {len(risky)} | 0.9 |",
        f"| Ordinary and hard cases reaching waspada or higher | {len(alarms)} of {len(benign)} "
        f"| at most 0.1 |",
        f"| Detection delay (messages after the expected start), median | "
        f"{statistics.median(delays) if delays else 'n/a'} (n={len(delays)}) | at most 2 |",
        f"| Risky scenarios never raised above aman | {len(never_raised)} | |",
        f"| Final level exactly as expected | {exact} of {len(rows)} | |",
        f"| Self-harm scenarios flagged for a support response | "
        f"{sum(r['support_needed'] for r in support_rows)} of {len(support_rows)} | |",
        f"| Score never decreased | {sum(r['monotonic'] for r in rows)} of {len(rows)} | |",
        f"| Stage 2 calls, used / made | {sum(r['stage2_model_used'] for r in rows)} / "
        f"{sum(r['stage2_calls'] for r in rows)} | |",
        f"| Messages where some analysis was unavailable | "
        f"{sum(r['analysis_unavailable_steps'] for r in rows)} | |",
        f"| Model calls per endpoint | {dict(by_endpoint)} | |",
        f"| Cost of priced calls (lower bound) | USD {cost:.4f} "
        f"({unknown_cost_calls} calls unpriced) | |",
        f"| Wall time, concurrency {concurrency} | {wall:.0f} s | |",
        "",
        "Latency per call:",
        "",
        "| Purpose | p50 | p95 | n |",
        "| --- | --- | --- | --- |",
    ]
    for purpose, lat in sorted(lat_by_purpose.items()):
        lat = sorted(lat)
        p95 = lat[min(len(lat) - 1, round(0.95 * (len(lat) - 1)))]
        lines.append(f"| {purpose} | {statistics.median(lat):.0f} ms | {p95} ms | {len(lat)} |")
    lines += [
        "",
        "Confusion (rows expected, columns final):",
        "",
        "| expected \\ final | " + " | ".join(levels) + " |",
        "| --- |" + " --- |" * len(levels),
    ]
    for e in levels:
        lines.append(f"| {e} | " + " | ".join(str(confusion[(e, f)]) for f in levels) + " |")
    lines += [
        "",
        "Per scenario:",
        "",
        "| Scenario | Expected | Final | Starts | First raise | Scores |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['scenario']} | {r['expected']} | {r['final']} | "
            f"{r['risk_starts_at'] or '-'} | {r['first_raise'] or '-'} | "
            f"{' '.join(map(str, r['scores']))} |"
        )
    lines.append("")
    (OUT_DIR / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines[:26]))
    return 0


def _record_usage(pool, sink: list) -> None:
    """Wrap a pool so every attempt of a successful call is collected with its purpose.
    Calls that end in an error are not collected, so cost here is a lower bound."""
    original = pool.complete_json

    async def wrapped(**kw):
        result = await original(**kw)
        sink.extend((kw.get("purpose", "?"), u) for u in result.attempts)
        return result

    pool.complete_json = wrapped


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--concurrency", type=int, default=4)
    # Names the output (eval/pipeline/<split>-<tag>.md) so a comparison run, such as a
    # different screening model, does not overwrite the main result.
    parser.add_argument("--tag", default="")
    args = parser.parse_args(argv)
    return asyncio.run(run(args.split, args.concurrency, args.tag))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
