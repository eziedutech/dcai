"""Fine-tune the stage 1 student: Llama 3.1 8B, LoRA SFT on W&B Serverless Training.

    uv run python train.py [--epochs 3]

Reads the training set made by the backend (python -m app.distill.build):
data/distill/stage1-train.jsonl, one {"messages": [system, user, assistant]} per line, where
the assistant turn is the teacher's (Muse Spark) JSON. Loss is on the assistant turn only.

WANDB_API_KEY is read from the environment or from code/backpy/.env and never printed.
Writes eval/distill/student.json with the inference model name of the trained checkpoint,
so the backend can be pointed at it (WB_STUDENT_MODEL) and measured on the test split.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRAIN = REPO / "data" / "distill" / "stage1-train.jsonl"
BALANCED = REPO / "data" / "distill" / "stage1-train-balanced.jsonl"
OUT = REPO / "eval" / "distill" / "student.json"
BASE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# Class balance. In the teacher's labels 79% of messages carry no label and some labels
# are rare (menyakiti_diri appears 6 times). Trained on that as is, the first student
# learned that "no label" is almost always right and never labelled self-harm on the test
# split. Labelled examples are repeated, rare ones more, decided from the training data's
# own counts (labels seen at most RARE_MAX times).
LABELLED_REPEAT = 3
RARE_REPEAT = 6
RARE_MAX = 6


def balance(src: Path, dst: Path) -> tuple[int, int, dict[str, int]]:
    from collections import Counter

    rows = [json.loads(line) for line in src.open(encoding="utf-8")]
    labels_of = [set(json.loads(r["messages"][-1]["content"])["labels"]) for r in rows]
    counts = Counter(lab for labs in labels_of for lab in labs)
    rare = {lab for lab, c in counts.items() if c <= RARE_MAX}
    out = []
    for row, labs in zip(rows, labels_of, strict=True):
        repeat = RARE_REPEAT if labs & rare else LABELLED_REPEAT if labs else 1
        out.extend([row] * repeat)
    dst.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out),
        encoding="utf-8",
        newline="\n",
    )
    return len(rows), len(out), {lab: counts[lab] for lab in sorted(rare)}


def load_key() -> None:
    if os.environ.get("WANDB_API_KEY"):
        return
    env = REPO / "code" / "backpy" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("WANDB_API_KEY="):
                os.environ["WANDB_API_KEY"] = line.split("=", 1)[1].strip()
                return
    sys.exit("WANDB_API_KEY not set (environment or code/backpy/.env)")


async def main(epochs: int, name: str) -> None:
    import art
    from art.serverless.backend import ServerlessBackend
    from art.utils.sft import train_sft_from_file

    if not TRAIN.exists():
        sys.exit(f"missing {TRAIN}; run: cd code/backpy && uv run python -m app.distill.build")
    unique, n, rare = balance(TRAIN, BALANCED)
    print(f"examples: {unique} unique, {n} after balancing; rare labels {rare}")
    print(f"epochs: {epochs}, base: {BASE_MODEL}")

    backend = ServerlessBackend()
    model = art.TrainableModel(
        name=name,
        run_name=f"{name}-run",
        project="dcai-distill",
        base_model=BASE_MODEL,
    )
    await model.register(backend)
    await train_sft_from_file(
        model=model,
        file_path=str(BALANCED),
        epochs=epochs,
        batch_size=2,
        peak_lr=2e-4,
        schedule_type="cosine",
        warmup_ratio=0.1,
        assistant_turns="last",
        verbose=True,
    )
    step = await model.get_step()
    inference_name = model.get_inference_name(step)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "base_model": BASE_MODEL,
                "examples_unique": unique,
                "examples_balanced": n,
                "rare_labels": rare,
                "labelled_repeat": LABELLED_REPEAT,
                "rare_repeat": RARE_REPEAT,
                "epochs": epochs,
                "step": step,
                "inference_model": inference_name,
                "inference_base_url": "https://forge.coreweave.com/api/training/v1",
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"done: step {step}, inference model {inference_name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    # Balancing repeats labelled examples, so fewer passes avoid memorising them.
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--name", default="stage1-student-8b-v2")
    a = p.parse_args()
    load_key()
    asyncio.run(main(a.epochs, a.name))
