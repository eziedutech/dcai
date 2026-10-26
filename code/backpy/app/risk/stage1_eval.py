"""Measure stage 1 labels against scenario labels, one endpoint at a time.

    python -m app.risk.stage1_eval ENDPOINT [--split dev|test] [--concurrency 4]

Dev split by default. The test split is locked for the final evaluation (spec section 11)
and needs --split test explicitly. Writes eval/stage1/<split>-<endpoint>.md and .json; the
JSON holds ids and labels only, never message text.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import Counter

import httpx

from app.config import endpoint_from_env, get_settings
from app.llm import PooledClient
from app.risk.stage1 import label_message
from app.scenarios.split import load_split
from app.scenarios.validate import DEFAULT_DIR, REPO_ROOT, load

OUT_DIR = REPO_ROOT / "eval" / "stage1"


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def _ratio(num: int, den: int) -> str:
    return "n/a" if den == 0 else f"{num / den:.2f}"


async def run(endpoint_name: str, split: str, concurrency: int) -> int:
    settings = get_settings()
    endpoint = endpoint_from_env(endpoint_name)
    if endpoint is None:
        print(f"endpoint {endpoint_name} is not configured")
        return 2
    ids = set(load_split()[split])
    scenarios = [s for s in load(DEFAULT_DIR)[0] if s.id in ids]
    jobs = [(s, i, m) for s in scenarios for i, m in enumerate(s.messages, 1)]
    sem = asyncio.Semaphore(concurrency)
    started = time.perf_counter()

    async with httpx.AsyncClient() as http:
        client = PooledClient(
            [endpoint], http=http, timeout=settings.llm_timeout_seconds, max_transient_retries=2
        )

        async def one(job):
            s, i, m = job
            async with sem:
                r = await label_message(client, m.sender.value, m.text)
            return s, i, m, r

        results = await asyncio.gather(*(one(j) for j in jobs))
    wall = time.perf_counter() - started

    rows = []
    tp = Counter()
    fp = Counter()
    fn = Counter()
    flagged_tp = flagged_fp = flagged_fn = 0
    wajar_total = wajar_flagged = 0
    unavailable = 0
    latencies, cost, cost_known = [], 0.0, True
    for s, i, m, r in results:
        gold = {str(x) for x in m.labels}
        pred = {str(x) for x in r.labels}
        if r.status != "ok":
            unavailable += 1
        if r.usage:
            latencies.append(r.usage.latency_ms)
            if r.usage.cost_usd is None:
                cost_known = False
            else:
                cost += r.usage.cost_usd
        for lab in pred & gold:
            tp[lab] += 1
        for lab in pred - gold:
            fp[lab] += 1
        for lab in gold - pred:
            fn[lab] += 1
        if gold and pred:
            flagged_tp += 1
        elif pred and not gold:
            flagged_fp += 1
        elif gold and not pred:
            flagged_fn += 1
        if s.group.value == "wajar":
            wajar_total += 1
            wajar_flagged += bool(pred)
        rows.append(
            {
                "scenario": s.id,
                "message": i,
                "sender": m.sender.value,
                "gold": sorted(gold),
                "pred": sorted(pred),
                "signal": r.signal,
                "status": r.status,
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{split}-{endpoint_name}"
    (OUT_DIR / f"{stem}.json").write_text(
        json.dumps({"endpoint": endpoint_name, "model": endpoint.model, "rows": rows}, indent=1)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    labels = sorted(set(tp) | set(fp) | set(fn))
    found = (
        f"recall {_ratio(flagged_tp, flagged_tp + flagged_fn)}, "
        f"precision {_ratio(flagged_tp, flagged_tp + flagged_fp)}"
    )
    latency = f"p50 {_pct(latencies, 0.5):.0f} ms, p95 {_pct(latencies, 0.95):.0f} ms"
    quiet = [r["signal"] for r in rows if not r["gold"] and r["signal"] is not None]
    lines = [
        f"# Stage 1 on the {split} split: {endpoint_name}",
        "",
        f"Model `{endpoint.model}`. {len(scenarios)} synthetic scenarios, {len(rows)} messages. "
        f"Gold labels are the scenario labels written with the dataset (draft, not yet "
        f"reviewed by a human).",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        f"| Model unavailable (after retries) | {unavailable} of {len(rows)} |",
        f"| Labelled messages found (any label) | {found} |",
        f"| Ordinary-chat messages given a label | {wajar_flagged} of {wajar_total} |",
        f"| Latency per message | {latency} |",
        f"| Cost | {'USD ' + format(cost, '.4f') if cost_known else 'unknown (price not set)'} |",
        f"| Wall time, concurrency {concurrency} | {wall:.0f} s |",
        "",
        "| Label | Precision | Recall | Gold count |",
        "| --- | --- | --- | --- |",
    ]
    for lab in labels:
        lines.append(
            f"| {lab} | {_ratio(tp[lab], tp[lab] + fp[lab])} | "
            f"{_ratio(tp[lab], tp[lab] + fn[lab])} | {tp[lab] + fn[lab]} |"
        )
    lines += [
        "",
        f"Median signal on messages without gold labels: {statistics.median(quiet or [0])}",
        "",
    ]
    (OUT_DIR / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args(argv)
    return asyncio.run(run(args.endpoint, args.split, args.concurrency))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
