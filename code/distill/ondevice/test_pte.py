"""Quick functional check of the exported .pte: does the on-device student still emit the
stage 1 label JSON? Runs a few masked synthetic samples through the same stage 1 prompt the
model was trained on and prints the model output. Run on a Linux box with optimum-executorch
installed (the same env used for export). This is a smoke test, not the accuracy eval against
the scenario gold labels.

    python test_pte.py --pte ~/out_pte --tokenizer ~/merged --train ~/dcai/data/distill/stage1-train.jsonl

The system prompt is read from the training file so it matches exactly what the model saw;
no raw user data is used (the samples below are synthetic and already masked).
"""

import argparse
import json
from pathlib import Path

# Synthetic, already-masked samples. Expect the first to draw approach labels
# (meminta_kerahasiaan, pindah_kanal), the second none, the third berbagi_data_pribadi.
SAMPLES = [
    (
        "contact",
        "jangan cerita ke siapa-siapa ya, ini rahasia kita. mending pindah ke WA aja",
    ),
    ("contact", "besok ada PR matematika yang dikumpul nggak?"),
    ("child", "ini alamatku [ALAMAT], main ke sini aja"),
]


def system_prompt(train_path: Path) -> str:
    """The exact stage 1 system prompt, taken from the first training row."""
    first = json.loads(train_path.open(encoding="utf-8").readline())
    return first["messages"][0]["content"]


def main(pte: str, tokenizer_dir: str, train: str, max_new_tokens: int) -> None:
    from optimum.executorch import ExecuTorchModelForCausalLM
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(tokenizer_dir)
    model = ExecuTorchModelForCausalLM.from_pretrained(pte)
    system = system_prompt(Path(train))

    for sender, text in SAMPLES:
        user = json.dumps({"sender": sender, "text": text}, ensure_ascii=False)
        prompt = tok.apply_chat_template(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        # optimum-executorch generation. The exact call is confirmed on the instance against
        # the installed version (introspect ExecuTorchModelForCausalLM.generate) and adjusted
        # if needed; the generate loop itself does not change the rest of this script.
        out = model.generate(
            tokenizer=tok, prompt=prompt, max_seq_len=max_new_tokens + 1024
        )
        print("=" * 60)
        print(f"sender={sender} text={text!r}")
        print("raw:", out)
        text_out = out if isinstance(out, str) else getattr(out, "text", str(out))
        try:
            parsed = json.loads(text_out.strip().splitlines()[-1])
            print("parsed JSON:", parsed)
            print("labels:", parsed.get("labels"), "signal:", parsed.get("signal"))
        except (json.JSONDecodeError, IndexError, AttributeError) as exc:
            print("NOT valid JSON on last line:", type(exc).__name__)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pte", default="out_pte", help="dir holding model.pte")
    p.add_argument("--tokenizer", default="merged", help="dir holding the tokenizer")
    p.add_argument(
        "--train",
        default="../../../data/distill/stage1-train.jsonl",
        help="training file, for the exact system prompt",
    )
    p.add_argument("--max-new-tokens", type=int, default=64)
    a = p.parse_args()
    main(a.pte, a.tokenizer, a.train, a.max_new_tokens)
