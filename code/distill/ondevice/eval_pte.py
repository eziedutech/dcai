"""Accuracy check of the exported .pte against the locked test-split scenarios.

Runs the on-device student over every message of the test scenarios, masks each message the
same way production does (the ported app/privacy/mask.py), applies the stage 1 deterministic
rules, and compares predicted labels to the scenario gold labels. Reports label recall and
precision and how many ordinary (wajar) messages drew a label.

    python eval_pte.py --pte ~/out_pte --tokenizer ~/merged_tok \
        --train ~/stage1-train.jsonl --scenarios ~/scenarios --split ~/split.json

This is stage 1 labels only (no stage 2, rule floor or final level): the part the on-device
model is responsible for. Numbers here are the measured ones; nothing is guessed.
"""

import argparse
import json
from pathlib import Path

import mask as M  # the ported app/privacy/mask.py, stdlib only

# Approach patterns describe what a contact does; on a child's own message they are noise and
# stripped, except a threat, which a child can make. Mirrors app/risk/stage1.apply_rules.
APPROACH = {
    "membangun_kedekatan",
    "meminta_kerahasiaan",
    "pindah_kanal",
    "meminta_data_pribadi",
    "menawarkan_hadiah",
    "menguji_batas",
    "menekan_mengancam",
}


def apply_rules(sender: str, model_labels: list[str], has_findings: bool) -> set[str]:
    labels = set(model_labels)
    if sender == "child" and has_findings:
        labels.add("berbagi_data_pribadi")
    if sender == "child":
        labels -= APPROACH - {"menekan_mengancam"}
    return labels


def parse_labels(out) -> list[str] | None:
    text = out if isinstance(out, str) else getattr(out, "text", str(out))
    text = (text or "").strip()
    cands = [text]
    if "\n" in text:
        cands.append(text.splitlines()[-1])
    for cand in cands:
        try:
            obj = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("labels"), list):
            return [str(x) for x in obj["labels"]]
    return None


def main(
    pte: str, tokenizer_dir: str, train: str, scenarios_dir: str, split_path: str
) -> None:
    from optimum.executorch import ExecuTorchModelForCausalLM
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(tokenizer_dir)
    model = ExecuTorchModelForCausalLM.from_pretrained(pte)
    with Path(train).open(encoding="utf-8") as fh:
        first = fh.readline()
    system = json.loads(first)["messages"][0]["content"]
    test_ids = json.loads(Path(split_path).read_text(encoding="utf-8"))["test"]

    tp = fp = fn = msgs = bad_json = wajar_false = 0
    for sid in test_ids:
        group = sid.rsplit("-", 1)[0]
        sc = json.loads(
            (Path(scenarios_dir) / group / f"{sid}.json").read_text(encoding="utf-8")
        )
        for m in sc["messages"]:
            msgs += 1
            sender = m["from"]
            masked = M.mask(m["text"])
            user = json.dumps(
                {"sender": sender, "text": masked.text}, ensure_ascii=False
            )
            prompt = tok.apply_chat_template(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
            out = model.text_generation(
                tokenizer=tok, prompt=prompt, max_seq_len=1024, echo=False
            )
            preds = parse_labels(out)
            if preds is None:
                bad_json += 1
                preds = []
            pred = apply_rules(sender, preds, bool(masked.findings))
            gold = set(m.get("labels", []))
            tp += len(pred & gold)
            fp += len(pred - gold)
            fn += len(gold - pred)
            if group == "wajar" and pred:
                wajar_false += 1

    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    print("=" * 50)
    print(f"test scenarios={len(test_ids)} messages={msgs} bad_json={bad_json}")
    print(
        f"label recall={recall:.2f} precision={precision:.2f} (tp={tp} fp={fp} fn={fn})"
    )
    print(f"wajar messages given any label (false alarms)={wajar_false}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pte", default="out_pte")
    p.add_argument("--tokenizer", default="merged_tok")
    p.add_argument("--train", default="stage1-train.jsonl")
    p.add_argument("--scenarios", default="scenarios")
    p.add_argument("--split", default="split.json")
    a = p.parse_args()
    main(a.pte, a.tokenizer, a.train, a.scenarios, a.split)
