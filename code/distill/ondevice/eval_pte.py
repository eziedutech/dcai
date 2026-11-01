"""Accuracy check of the exported .pte against the locked test-split scenarios.

Runs the on-device student over every message of the test scenarios, masks each message the
same way production does (the ported app/privacy/mask.py), applies the stage 1 deterministic
rules, and compares predicted labels to the scenario gold labels. Reports label recall and
precision, the message-level flagged recall/precision (the send policy, see below), and how
many ordinary (wajar) messages drew a label.

    python eval_pte.py --pte ~/out_pte_short --tokenizer ~/merged \
        --train ~/stage1-train-short.jsonl --scenarios ~/scenarios --split ~/split.json

The short on-device student emits a COMPACT CODE, not JSON: the present label letters (sorted)
then one signal digit, or "N" for no labels. "BC4" = {meminta_kerahasiaan, pindah_kanal},
signal ~40; "N0" = ordinary. This decoder mirrors Stage1Prompt.parse on the phone
(code/android/.../ingest/Stage1Prompt.kt) and the codebook in build_short.py exactly. Pass the
short train file as --train so the system prompt read from its first row is SHORT_SYSTEM.

On the on-device path a message is sent to the server when it carries any label OR a signal at
or above ONDEVICE_SEND_SIGNAL (20), see app .../ingest/MessageIngest.kt. The flagged metric
below scores that same decision against whether the gold message is risky (has any gold label),
so a missed threat (false negative) shows up directly.

This is stage 1 labels only (no stage 2, rule floor or final level): the part the on-device
model is responsible for. Numbers here are the measured ones; nothing is guessed.
"""

import argparse
import json
import re
from pathlib import Path

import mask as M  # the ported app/privacy/mask.py, stdlib only

# Letter -> label, the inverse of build_short.py LETTERS and Stage1Prompt.LABEL_OF.
LABEL_OF = {
    "A": "membangun_kedekatan",
    "B": "meminta_kerahasiaan",
    "C": "pindah_kanal",
    "D": "meminta_data_pribadi",
    "E": "menawarkan_hadiah",
    "F": "menguji_batas",
    "G": "menekan_mengancam",
    "H": "perundungan",
    "I": "kata_kasar",
    "J": "berbagi_data_pribadi",
    "K": "menyakiti_diri",
    "L": "ajakan_berbahaya",
}

# Same pattern as Stage1Prompt.CODE: letters then one signal digit.
CODE = re.compile(r"([A-LN]+)([0-9])")

# The on-device send threshold (ONDEVICE_SEND_SIGNAL in MessageIngest.kt).
SEND_SIGNAL = 20

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


def parse_code(out) -> tuple[list[str], int] | None:
    """Decode the coded answer the way the phone does: the last non-empty line, the first code
    in it, letters -> labels (drop N), the final digit -> signal (x10). None when nothing
    parses, so the caller fails safe (counts as a bad decode and an empty label set)."""
    text = out if isinstance(out, str) else getattr(out, "text", str(out))
    text = (text or "").strip()
    line = next(
        (ln.strip() for ln in reversed(text.splitlines()) if ln.strip()), None
    )
    if line is None:
        return None
    m = CODE.search(line.upper())
    if m is None:
        return None
    letters, digit = m.group(1), m.group(2)
    labels = [LABEL_OF[c] for c in letters if c != "N" and c in LABEL_OF]
    signal = min(100, max(0, int(digit) * 10))
    return labels, signal


def decode_json(out) -> tuple[list[str], int] | None:
    """Decode the full-prompt JSON answer ({"labels":[...], "signal": N}): the last line that
    parses as a JSON object carrying a 'labels' list. None when nothing parses, so the caller
    fails safe (bad decode, empty labels)."""
    text = out if isinstance(out, str) else getattr(out, "text", str(out))
    text = (text or "").strip()
    cands = [text, *reversed(text.splitlines())] if text else []
    for cand in cands:
        cand = cand.strip()
        if not cand:
            continue
        try:
            obj = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("labels"), list):
            labels = [str(x) for x in obj["labels"]]
            signal = int(obj.get("signal", 0) or 0)
            return labels, min(100, max(0, signal))
    return None


def main(
    pte: str,
    tokenizer_dir: str,
    train: str,
    scenarios_dir: str,
    split_path: str,
    fmt: str,
    max_seq_len: int,
) -> None:
    from optimum.executorch import ExecuTorchModelForCausalLM
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(tokenizer_dir)
    model = ExecuTorchModelForCausalLM.from_pretrained(pte)
    with Path(train).open(encoding="utf-8") as fh:
        first = fh.readline()
    system = json.loads(first)["messages"][0]["content"]
    decode = parse_code if fmt == "code" else decode_json
    test_ids = json.loads(Path(split_path).read_text(encoding="utf-8"))["test"]

    tp = fp = fn = msgs = bad_code = wajar_false = 0
    # Message-level flagged decision (the send policy): did the model send this message, and
    # should it have (gold message is risky = has any gold label)?
    f_tp = f_fp = f_fn = 0
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
                tokenizer=tok, prompt=prompt, max_seq_len=max_seq_len, echo=False
            )
            decoded = decode(out)
            if decoded is None:
                bad_code += 1
                raw_labels, signal = [], 0
            else:
                raw_labels, signal = decoded
            pred = apply_rules(sender, raw_labels, bool(masked.findings))
            gold = set(m.get("labels", []))
            tp += len(pred & gold)
            fp += len(pred - gold)
            fn += len(gold - pred)
            if group == "wajar" and pred:
                wajar_false += 1
            # A bad decode fails safe (sent) on the phone, so it counts as flagged here too.
            flagged = decoded is None or bool(pred) or signal >= SEND_SIGNAL
            risky = bool(gold)
            if flagged and risky:
                f_tp += 1
            elif flagged and not risky:
                f_fp += 1
            elif not flagged and risky:
                f_fn += 1

    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f_recall = f_tp / (f_tp + f_fn) if (f_tp + f_fn) else 0.0
    f_precision = f_tp / (f_tp + f_fp) if (f_tp + f_fp) else 0.0
    print("=" * 50)
    print(f"test scenarios={len(test_ids)} messages={msgs} bad_code={bad_code}")
    print(
        f"label recall={recall:.2f} precision={precision:.2f} (tp={tp} fp={fp} fn={fn})"
    )
    print(
        f"flagged recall={f_recall:.2f} precision={f_precision:.2f} "
        f"(tp={f_tp} fp={f_fp} fn={f_fn}); missed risky messages={f_fn}"
    )
    print(f"wajar messages given any label (false alarms)={wajar_false}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pte", default="out_pte")
    p.add_argument("--tokenizer", default="merged_tok")
    p.add_argument("--train", default="stage1-train.jsonl")
    p.add_argument("--scenarios", default="scenarios")
    p.add_argument("--split", default="split.json")
    # The assistant answer format: "code" (short letters+digit, the compact on-device student)
    # or "json" (the full-prompt student that emits {"labels":[...], "signal": N}).
    p.add_argument("--format", choices=["code", "json"], default="code")
    # Export/runtime context length; must cover the prompt (short ~150 tok, full ~950 tok).
    p.add_argument("--max-seq-len", type=int, default=512)
    a = p.parse_args()
    main(a.pte, a.tokenizer, a.train, a.scenarios, a.split, a.format, a.max_seq_len)
