"""Build the stage 1 distillation set: the teacher labels every dev-split message.

    python -m app.distill.build [--concurrency 4]

The teacher is the reasoning pool (Muse Spark). Each training example is exactly what the
student will see in production: the stage 1 system prompt with the JSON instruction
(json_system), the masked message as the user turn, and the teacher's JSON as the answer.

Only the dev split is used. The test split stays held out to measure the student.
Writes data/distill/stage1-train.jsonl (synthetic masked text, git-ignored, rebuilt by
this command) and eval/distill/teacher-dev.md (ids and labels only, no text).
"""

import argparse
import asyncio
import json
import sys
import time
from collections import Counter

import httpx

from app.config import get_settings
from app.llm import LLMError, build_clients
from app.llm.pool import json_system
from app.privacy.mask import mask
from app.risk.stage1 import SYSTEM, Stage1Output, apply_rules, user_payload
from app.scenarios.split import load_split
from app.scenarios.validate import DEFAULT_DIR, REPO_ROOT, load

DATA_DIR = REPO_ROOT / "data" / "distill"
EVAL_DIR = REPO_ROOT / "eval" / "distill"
# Muse Spark reasons before answering; stage 1's 200-token budget is for the student.
TEACHER_MAX_TOKENS = 1500


async def run(concurrency: int) -> int:
    settings = get_settings()
    ids = set(load_split()["dev"])
    scenarios = [s for s in load(DEFAULT_DIR)[0] if s.id in ids]
    jobs = [(s, i, m) for s in scenarios for i, m in enumerate(s.messages, 1)]
    system = json_system(SYSTEM, Stage1Output)
    sem = asyncio.Semaphore(concurrency)
    started = time.perf_counter()

    async with httpx.AsyncClient() as http:
        teacher, _ = build_clients(settings, http)

        async def one(job):
            s, i, m = job
            masked = mask(m.text)
            user = user_payload(m.sender.value, masked.text)
            async with sem:
                try:
                    r = await teacher.complete_json(
                        purpose="distill_teacher",
                        system=SYSTEM,
                        user=user,
                        schema=Stage1Output,
                        max_tokens=TEACHER_MAX_TOKENS,
                        timeout=60.0,
                    )
                except LLMError as exc:
                    return s, i, m, masked, user, None, type(exc).__name__, None
            return s, i, m, masked, user, r.value, None, r.usage

        results = await asyncio.gather(*(one(j) for j in jobs))
    wall = time.perf_counter() - started

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    rows, examples = [], []
    failed = Counter()
    flag = Counter()
    wajar_total = wajar_flagged = 0
    cost = 0.0
    for s, i, m, masked, user, out, err, usage in results:
        if out is None:
            failed[err] += 1
            continue
        if usage and usage.cost_usd is not None:
            cost += usage.cost_usd
        answer = json.dumps(out.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))
        examples.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": answer},
                ]
            }
        )
        gold = {str(x) for x in m.labels}
        pred = {str(x) for x in apply_rules(m.sender.value, out.labels, masked.findings)}
        if gold and pred:
            flag["tp"] += 1
        elif pred and not gold:
            flag["fp"] += 1
        elif gold and not pred:
            flag["fn"] += 1
        if s.group.value == "wajar":
            wajar_total += 1
            wajar_flagged += bool(pred)
        rows.append(
            {
                "scenario": s.id,
                "message": i,
                "gold": sorted(gold),
                "teacher": sorted(pred),
                "signal": out.signal,
            }
        )

    train = DATA_DIR / "stage1-train.jsonl"
    train.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in examples),
        encoding="utf-8",
        newline="\n",
    )
    (EVAL_DIR / "teacher-dev.json").write_text(
        json.dumps({"rows": rows}, indent=1) + "\n", encoding="utf-8", newline="\n"
    )

    def ratio(a, b):
        return "n/a" if b == 0 else f"{a / b:.2f}"

    recall = ratio(flag["tp"], flag["tp"] + flag["fn"])
    precision = ratio(flag["tp"], flag["tp"] + flag["fp"])
    lines = [
        "# Distillation teacher on the dev split",
        "",
        f"Teacher: the reasoning pool (Muse Spark). {len(scenarios)} scenarios, {len(jobs)} "
        f"messages, {len(examples)} training examples written. Gold labels are the dataset "
        "drafts.",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        f"| Teacher failed (after retries) | {sum(failed.values())} {dict(failed) or ''} |",
        f"| Labelled messages found (any label) | recall {recall}, precision {precision} |",
        f"| Ordinary-chat messages given a label | {wajar_flagged} of {wajar_total} |",
        f"| Cost of priced calls | USD {cost:.4f} |",
        f"| Wall time, concurrency {concurrency} | {wall:.0f} s |",
        "",
    ]
    (EVAL_DIR / "teacher-dev.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))
    print(f"train file: {train} ({len(examples)} examples)")
    return 0 if examples else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.concurrency)))


if __name__ == "__main__":
    main()
