"""Export the off-the-shelf sexual-content image classifier to an ExecuTorch .pte for the
phone (ADR docs/proposals/on-device-behavior.md, WS2a).

Model: Falconsai/nsfw_image_detection (ViT-base, Apache-2.0, two classes "normal"/"nsfw"),
used as published. dcAI does not train or fine-tune it and never downloads or collects
sensitive images: export, quantization and the parity check below use ordinary synthetic
pictures only. Its accuracy is the figure its source states; dcAI has not measured it.

Quantization: XNNPACK dynamic int8 (per-channel int8 weights, activations quantized at run
time), so no calibration images are needed.

The .pte runs on the executorch-android runtime the app already ships; the exporter version
must not be newer than the runtime (gradle/libs.versions.toml `executorch`).

    uv venv v && uv pip install -p v executorch==1.4.0 "transformers>=4.55,<5" pillow
    v/Scripts/python code/vision/export_nsfw.py --out code/android/app/src/main/assets/vision
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = "Falconsai/nsfw_image_detection"
SIZE = 224


class Probs(torch.nn.Module):
    """pixel_values [1,3,224,224] (already normalized) -> softmax probabilities [1,2]."""

    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.model(pixel_values=pixel_values).logits, dim=-1)


def synthetic_images(n: int) -> list[np.ndarray]:
    """Ordinary test pictures: gradients, flat colours and noise, uint8 HxWx3."""
    rng = np.random.default_rng(0)
    out = []
    for i in range(n):
        h, w = int(rng.integers(160, 900)), int(rng.integers(160, 900))
        kind = i % 3
        if kind == 0:
            y = np.linspace(0, 255, h)[:, None, None]
            x = np.linspace(0, 255, w)[None, :, None]
            img = np.concatenate([y + 0 * x, x + 0 * y, (x + y) / 2], axis=2)
        elif kind == 1:
            img = np.ones((h, w, 3)) * rng.integers(0, 256, 3)
        else:
            img = rng.integers(0, 256, (h, w, 3))
        out.append(np.clip(img, 0, 255).astype(np.uint8))
    return out


def phone_preprocess(img: np.ndarray, mean: list[float], std: list[float]) -> torch.Tensor:
    """What the phone does (VisionNsfwModel.kt): bilinear resize to 224, scale to 0..1,
    normalize per channel, CHW."""
    from PIL import Image

    pil = Image.fromarray(img).resize((SIZE, SIZE), Image.BILINEAR)
    x = np.asarray(pil, dtype=np.float32) / 255.0
    x = (x - np.array(mean, dtype=np.float32)) / np.array(std, dtype=np.float32)
    return torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0).contiguous()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True, help="directory for nsfw.pte + nsfw.json")
    args = ap.parse_args()

    from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
    from executorch.backends.xnnpack.quantizer.xnnpack_quantizer import (
        XNNPACKQuantizer,
        get_symmetric_quantization_config,
    )
    from executorch.exir import to_edge_transform_and_lower
    from executorch.runtime import Runtime
    from torchao.quantization.pt2e.quantize_pt2e import convert_pt2e, prepare_pt2e

    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    hf = AutoModelForImageClassification.from_pretrained(MODEL_ID).eval()
    labels = [hf.config.id2label[i] for i in range(hf.config.num_labels)]
    if labels != ["normal", "nsfw"]:
        raise SystemExit(f"unexpected labels {labels}; update the phone side before exporting")
    mean, std = list(processor.image_mean), list(processor.image_std)

    model = Probs(hf).eval()
    example = (torch.zeros(1, 3, SIZE, SIZE),)
    with torch.no_grad():
        graph = torch.export.export(model, example).module()
        quantizer = XNNPACKQuantizer().set_global(
            get_symmetric_quantization_config(is_per_channel=True, is_dynamic=True)
        )
        prepared = prepare_pt2e(graph, quantizer)
        prepared(*example)
        quantized = convert_pt2e(prepared)
        program = to_edge_transform_and_lower(
            torch.export.export(quantized, example), partitioner=[XnnpackPartitioner()]
        ).to_executorch()

    args.out.mkdir(parents=True, exist_ok=True)
    pte = args.out / "nsfw.pte"
    pte.write_bytes(program.buffer)

    # Parity on ordinary pictures: the HF pipeline (its own resize + normalize, fp32) against
    # the .pte fed with the phone's preprocessing. Only the nsfw probability is compared.
    method = Runtime.get().load_program(str(pte)).load_method("forward")
    worst = 0.0
    for img in synthetic_images(12):
        with torch.no_grad():
            ref = model(processor(images=img, return_tensors="pt")["pixel_values"])[0, 1].item()
        got = method.execute([phone_preprocess(img, mean, std)])[0][0, 1].item()
        worst = max(worst, abs(ref - got))
    print(f"parity on 12 ordinary pictures: max |p_nsfw(hf fp32) - p_nsfw(pte)| = {worst:.4f}")
    if worst > 0.05:
        raise SystemExit("parity too loose; do not ship this export")

    meta = {
        "source": MODEL_ID,
        "license": "Apache-2.0",
        "labels": labels,
        "size": SIZE,
        "mean": mean,
        "std": std,
        "quant": "xnnpack dynamic int8",
        "sha256": hashlib.sha256(pte.read_bytes()).hexdigest(),
        "parity_max_abs": round(worst, 4),
    }
    (args.out / "nsfw.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {pte} ({pte.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
