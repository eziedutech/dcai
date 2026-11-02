"""Export the off-the-shelf sexual-content image classifier to a LiteRT (.tflite) model for
the phone (ADR docs/proposals/on-device-behavior.md, WS2a).

Model: Falconsai/nsfw_image_detection (ViT-base, Apache-2.0, two classes "normal"/"nsfw"),
used as published. dcAI does not train or fine-tune it and never downloads or collects
sensitive images: export, quantization and the parity check below use ordinary synthetic
pictures only. Its accuracy is the figure its source states; dcAI has not measured it.

Runtime: LiteRT (gradle/libs.versions.toml `litert`). The ExecuTorch runtime the message
model uses has ARMv8.1 atomics inline and dies with SIGILL on ARMv8.0 phones (Cortex-A53);
LiteRT selects its atomics at run time, so the image model runs on those phones too.

Conversion: the published PyTorch weights load into the TensorFlow ViT of the same
architecture, then the LiteRT converter applies dynamic-range quantization (int8 weights,
float activations), so no calibration images are needed. The input stays NCHW so the phone's
preprocessing is unchanged.

    uv venv -p 3.12 v && uv pip install -p v "tensorflow==2.19.*" "tf-keras==2.19.*" \
        "transformers>=4.55,<5" torch pillow
    v/Scripts/python code/vision/export_nsfw.py --out code/vision/out
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
    ap.add_argument("--out", type=Path, required=True, help="directory for nsfw.tflite + nsfw.json")
    args = ap.parse_args()

    import tensorflow as tf
    from transformers import TFViTForImageClassification

    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    hf = AutoModelForImageClassification.from_pretrained(MODEL_ID).eval()
    labels = [hf.config.id2label[i] for i in range(hf.config.num_labels)]
    if labels != ["normal", "nsfw"]:
        raise SystemExit(f"unexpected labels {labels}; update the phone side before exporting")
    mean, std = list(processor.image_mean), list(processor.image_std)
    reference = Probs(hf).eval()

    from transformers.modeling_tf_pytorch_utils import load_pytorch_model_in_tf2_model

    # The source publishes safetensors only, so the weights move from the loaded PyTorch model.
    tf_model = TFViTForImageClassification(hf.config)
    load_pytorch_model_in_tf2_model(tf_model, hf)

    @tf.function(input_signature=[tf.TensorSpec([1, 3, SIZE, SIZE], tf.float32, name="pixels")])
    def probs(pixels):
        return tf.nn.softmax(tf_model(pixel_values=pixels, training=False).logits, axis=-1)

    converter = tf.lite.TFLiteConverter.from_concrete_functions([probs.get_concrete_function()], tf_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    blob = converter.convert()

    args.out.mkdir(parents=True, exist_ok=True)
    model_file = args.out / "nsfw.tflite"
    model_file.write_bytes(blob)

    # Parity on ordinary pictures: the HF pipeline (its own resize + normalize, PyTorch fp32)
    # against the .tflite fed with the phone's preprocessing. Only the nsfw probability counts.
    interpreter = tf.lite.Interpreter(model_path=str(model_file))
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]["index"]
    out = interpreter.get_output_details()[0]["index"]
    worst = 0.0
    for img in synthetic_images(12):
        with torch.no_grad():
            ref = reference(processor(images=img, return_tensors="pt")["pixel_values"])[0, 1].item()
        interpreter.set_tensor(inp, phone_preprocess(img, mean, std).numpy())
        interpreter.invoke()
        got = float(interpreter.get_tensor(out)[0, 1])
        worst = max(worst, abs(ref - got))
    print(f"parity on 12 ordinary pictures: max |p_nsfw(hf fp32) - p_nsfw(tflite)| = {worst:.4f}")
    if worst > 0.05:
        raise SystemExit("parity too loose; do not ship this export")

    meta = {
        "source": MODEL_ID,
        "license": "Apache-2.0",
        "labels": labels,
        "size": SIZE,
        "layout": "NCHW",
        "mean": mean,
        "std": std,
        "quant": "litert dynamic-range int8",
        "sha256": hashlib.sha256(blob).hexdigest(),
        "parity_max_abs": round(worst, 4),
    }
    (args.out / "nsfw.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {model_file} ({len(blob)} bytes)")


if __name__ == "__main__":
    main()
