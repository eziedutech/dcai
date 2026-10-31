"""Distil the on-device stage 1 student: Llama 3.2 1B, LoRA SFT with HF + PEFT + TRL.

Unlike code/distill/train.py (OpenPipe ART serverless, which yields only an inference
endpoint), this path writes a MERGED CHECKPOINT on disk so it can be exported to ExecuTorch
(.pte) and run on the phone. See export_executorch.md for the export step.

    python train_1b.py [--epochs 2] [--base-model meta-llama/Llama-3.2-1B-Instruct]

Reuses the same training set as the 8B student (data/distill/stage1-train.jsonl, one
{"messages": [system, user, assistant]} per line, assistant turn = the teacher's JSON) and
the same class balancing, so the on-device student learns the same task distribution. Loss is
on the assistant turn only.

The base weights are gated: accept the Llama 3.2 Community License on Hugging Face and set
HF_TOKEN in the environment (never commit it). The Llama license requires attribution:
the output model name is prefixed "Llama" and products must state "Built with Llama".

Runs on a GPU host (Baseten Training Jobs, bring-your-own-container, H100). It is not meant
to run on the developer laptop. torch and transformers are imported inside main() so the
data-prep helpers below can be imported and checked without the heavy stack installed.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TRAIN = REPO / "data" / "distill" / "stage1-train.jsonl"
BALANCED = REPO / "data" / "distill" / "stage1-train-balanced.jsonl"

# Same balancing as code/distill/train.py: in the teacher labels most messages carry no
# label and some labels are rare, so labelled examples are repeated and rare ones repeated
# more, decided from the training data's own counts.
LABELLED_REPEAT = 3
RARE_REPEAT = 6
RARE_MAX = 6

# Long enough for the full stage 1 system prompt plus one message and the label JSON. The
# system prompt is large, so a tiny context would truncate it; runtime context and any prompt
# shortening are tuned at export time, not here.
DEFAULT_MAX_SEQ_LEN = 1024

# LoRA on all attention and MLP projections, matching the usual Llama recipe.
LORA_TARGETS = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]

# The Llama 3.2 Instruct assistant turn starts after this header; loss is masked to the text
# that follows it, so only the assistant (label) turn trains.
RESPONSE_TEMPLATE = "<|start_header_id|>assistant<|end_header_id|>\n\n"


def balance(src: Path, dst: Path) -> tuple[int, int, dict[str, int]]:
    """Expand the training file by repeating labelled and rare-labelled examples, writing the
    balanced file. Returns (unique rows, rows after balancing, rare-label counts)."""
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


def main(base_model: str, epochs: int, out_dir: Path, max_seq_len: int) -> None:
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer

    if not TRAIN.exists():
        sys.exit(
            f"missing {TRAIN}; run: cd code/backpy && uv run python -m app.distill.build"
        )
    unique, n, rare = balance(TRAIN, BALANCED)
    print(f"examples: {unique} unique, {n} after balancing; rare labels {rare}")
    print(f"base: {base_model}, epochs: {epochs}, max_seq_len: {max_seq_len}")

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def render(example: dict) -> dict:
        text = tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )
        return {"text": text}

    dataset = load_dataset("json", data_files=str(BALANCED), split="train").map(
        render, remove_columns=["messages"]
    )

    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=LORA_TARGETS,
    )

    collator = DataCollatorForCompletionOnlyLM(
        response_template=RESPONSE_TEMPLATE, tokenizer=tokenizer
    )

    config = SFTConfig(
        output_dir=str(out_dir / "trainer"),
        num_train_epochs=epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=10,
        bf16=True,
        max_seq_length=max_seq_len,
        dataset_text_field="text",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=dataset,
        peft_config=lora,
        data_collator=collator,
    )
    trainer.train()

    # Merge the LoRA adapter into the base so the result is a plain checkpoint ExecuTorch can
    # export. Save weights and tokenizer side by side.
    merged = trainer.model.merge_and_unload()
    merged_dir = out_dir / "merged"
    merged.save_pretrained(str(merged_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(merged_dir))
    print(f"done: merged checkpoint at {merged_dir}")
    print("next: see export_executorch.md to produce the .pte for the phone")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-model", default="meta-llama/Llama-3.2-1B-Instruct")
    p.add_argument("--epochs", type=int, default=2)
    # Name prefixed "Llama" per the Llama 3.2 Community License.
    p.add_argument("--out", default="out/Llama-3.2-1B-dcai-stage1")
    p.add_argument("--max-seq-len", type=int, default=DEFAULT_MAX_SEQ_LEN)
    a = p.parse_args()
    main(a.base_model, a.epochs, Path(a.out), a.max_seq_len)
