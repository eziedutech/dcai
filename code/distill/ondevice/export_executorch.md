# Export the student to ExecuTorch (.pte) for the phone

Turns the merged HF checkpoint from `train_1b.py` into a quantized `.pte` that runs on Android
through ExecuTorch. This step is CPU only; no GPU is needed. We use `optimum-executorch`, which
exports a Hugging Face checkpoint directly, so there is no consolidated.pth conversion.

Run on Linux. On a Windows laptop use WSL2 (Ubuntu), or a small CPU cloud box. The merged
checkpoint is at `code/distill/ondevice/out/Llama-3.2-1B-dcai-stage1/merged`; from WSL that is
`/mnt/d/HACKATHON/DCAI/code/distill/ondevice/out/Llama-3.2-1B-dcai-stage1/merged`.

## 1. Install optimum-executorch

```bash
conda create -n oe python=3.11 && conda activate oe
git clone https://github.com/huggingface/optimum-executorch.git
cd optimum-executorch
pip install '.[dev]'
python install_dev.py   # pulls executorch, torch, torchao, transformers (nightly/source)
```

Pin the optimum-executorch commit you use, since it tracks nightlies.

## 2. Export to .pte (4-bit, XNNPACK / CPU)

```bash
MERGED=/mnt/d/HACKATHON/DCAI/code/distill/ondevice/out/Llama-3.2-1B-dcai-stage1/merged
optimum-cli export executorch \
  --model "$MERGED" \
  --task text-generation \
  --recipe xnnpack \
  --use_custom_sdpa \
  --use_custom_kv_cache \
  --qlinear 8da4w \
  --qembedding 8w \
  --output_dir out_pte
```

`8da4w` is 8-bit dynamic activations with 4-bit weights (TorchAO PTQ); `8w` is 8-bit
embeddings. The `.pte` lands in `out_pte/`. Expect roughly 0.7 to 1.1 GB for a 1B at 4-bit;
record the real size after the run (no guessed numbers).

## 3. Sanity check, then Android

- Quick generation check: load the `.pte` with `optimum.executorch.ExecuTorchModelForCausalLM`
  (or the ExecuTorch llama runner) on one masked sample message and confirm it emits the
  stage 1 label JSON.
- Wire the `.pte` into the Android app behind the on-device mode (see
  docs/proposals/on-device-behavior.md). It is large, so the app downloads it on demand and
  loads it lazily; it is not bundled in the APK.

## Notes

- `--model` takes a local HF directory (standard `from_pretrained`). If it rejects the path,
  pass an absolute path, or check `optimum-cli export executorch --help`.
- Measure before trusting the student: serve the merged checkpoint and run the same eval as the
  8B student (`app.risk.stage1_eval`, `app.risk.pipeline_eval`). Report only eval numbers.
- Alternative path: the raw ExecuTorch llama example
  (examples/models/llama/README.md) also works, but it expects a consolidated.00.pth plus
  params.json, so it needs an HF-to-consolidated conversion first. optimum-executorch avoids that.
