"""Measure the stage 1 prompt in Llama tokens and try LLMLingua-2 compression on the static
system prompt. Research only: nothing here changes training data, the app or prod.
See docs/proposals/ondevice-prompt-compression.md.

Needs a throwaway venv with `tokenizers` and (for --compress) `llmlingua` + CPU torch:
    uv venv v && uv pip install -p v tokenizers llmlingua
    uv pip install -p v torch --index-url https://download.pytorch.org/whl/cpu
Run from the repo root:
    v/Scripts/python code/distill/ondevice/compress_prompt.py [--compress] [--out x.json]
"""

import argparse
import ast
import json
import statistics
from pathlib import Path

from build_short import SHORT_SYSTEM

REPO = Path(__file__).resolve().parents[3]
TOKENIZER = REPO / "code" / "distill" / "ondevice" / "out" / "full1b" / "tokenizer.json"
TRAIN_FULL = REPO / "data" / "distill" / "stage1-train.jsonl"
TRAIN_SHORT = REPO / "data" / "distill" / "stage1-train-short.jsonl"
LINGUA_MODEL = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"

# Label order as it appears in stage1.py SYSTEM; the compressor mangles these names
# ("membangun _ kedekatan" or drops them), so they are put back by position.
LABELS = [
    "membangun_kedekatan",
    "meminta_kerahasiaan",
    "pindah_kanal",
    "meminta_data_pribadi",
    "menawarkan_hadiah",
    "menguji_batas",
    "menekan_mengancam",
    "perundungan",
    "kata_kasar",
    "berbagi_data_pribadi",
    "menyakiti_diri",
    "ajakan_berbahaya",
]


def server_system() -> str:
    """stage1.py SYSTEM, read without importing the backend package."""
    src = (REPO / "code" / "backpy" / "app" / "risk" / "stage1.py").read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "SYSTEM":
            return ast.literal_eval(node.value)
    raise SystemExit("SYSTEM not found in stage1.py")


def repair(text: str) -> str:
    """Put each label line's canonical name back, in order, and drop empty header lines."""
    lines, i = [], 0
    for raw in text.split("\n"):
        s = raw.strip()
        if s.startswith("-") and i < len(LABELS):
            body = s.split(":", 1)[1].strip() if ":" in s else s[1:].strip()
            s = f"- {LABELS[i]}: {body}"
            i += 1
        if s not in ("", ":"):
            lines.append(s)
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compress", action="store_true", help="run LLMLingua-2 (downloads a model)")
    ap.add_argument("--out", type=Path, help="write compressed prompts as JSON")
    args = ap.parse_args()

    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))

    def n(s: str) -> int:
        return len(tok.encode(s, add_special_tokens=False).ids)

    system = server_system()
    print(f"system prompt: full {n(system)} tokens, short {n(SHORT_SYSTEM)} tokens")

    def spread(xs: list[int]) -> str:
        xs = sorted(xs)
        return f"median {statistics.median(xs)}, p95 {xs[int(len(xs) * 0.95)]}, max {xs[-1]}"

    for path, name in ((TRAIN_FULL, "full"), (TRAIN_SHORT, "short")):
        if not path.exists():
            print(f"skip {name}: {path} missing")
            continue
        rows = [json.loads(line)["messages"] for line in path.open(encoding="utf-8")]
        print(f"{name}: {len(rows)} rows; user turn {spread([n(m[-2]['content']) for m in rows])}")
        print(f"{name}: answer {spread([n(m[-1]['content']) for m in rows])}")

    if not args.compress:
        return
    from llmlingua import PromptCompressor

    pc = PromptCompressor(model_name=LINGUA_MODEL, use_llmlingua2=True, device_map="cpu")
    out = {}
    for rate in (0.6, 0.45, 0.33):
        raw = pc.compress_prompt(system, rate=rate, force_tokens=["\n", "-", ":"])
        raw = raw["compressed_prompt"]
        fixed = repair(raw)
        lost = [w for w in LABELS if w not in raw]
        print(
            f"rate {rate}: {n(raw)} tokens raw ({len(lost)} label names lost), "
            f"{n(fixed)} after repair"
        )
        out[str(rate)] = {"raw": raw, "repaired": fixed, "tokens": n(fixed)}
    if args.out:
        args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
