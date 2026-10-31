# Export the student to ExecuTorch (.pte) for the phone

Turns the merged checkpoint from `train_1b.py` into a quantized `.pte` that runs on Android
through ExecuTorch. Run on the GPU/Linux host, not the laptop. ExecuTorch officially supports
Llama 3.2 1B/3B on mobile; exact flags change between releases, so pin the ExecuTorch version
and check the installed example's README when you run this.

Reference: https://github.com/pytorch/executorch/blob/main/examples/models/llama/README.md

## 1. Install ExecuTorch and the llama example

```bash
git clone https://github.com/pytorch/executorch.git
cd executorch
./install_executorch.sh
./examples/models/llama/install_requirements.sh
```

Pin to a specific release tag rather than main for a reproducible build.

## 2. Convert the merged HF checkpoint

ExecuTorch's llama export expects a checkpoint plus a `params.json`. Convert the
`out/Llama-3.2-1B-dcai-stage1/merged` directory (HF safetensors) to the format the example
expects using the conversion utility shipped with the llama example (see its README section
on fine-tuned / custom checkpoints). Keep the tokenizer that `train_1b.py` saved.

## 3. Export to .pte with 4-bit quantization

Use `export_llm` with a quantization config. Options, strongest accuracy last:

- 4-bit groupwise (group size 32) weights + 8-bit dynamic activations (XNNPACK)
- SpinQuant (lower outliers, higher accuracy)
- QAT + LoRA (quantization-aware)

```bash
python -m extension.llm.export.export_llm \
  --config examples/models/llama/config/llama_xnnpack_spinquant.yaml \
  +base.model_class=llama3_2 \
  +base.checkpoint=<converted_checkpoint> \
  +base.params=<params.json>
```

Expected size for 1B at 4-bit: about 1.1 GB (SpinQuant ~1083 MiB, QAT+LoRA ~1127 MiB).

## 4. Validate on the host, then on a phone

- Build the llama runner and run `llama_main` with the `.pte`, the tokenizer, and a sample
  masked message to confirm the labels match the eval.
- Push to an Android device with `adb` and benchmark, then wire it into the app behind the
  on-device mode.

## Delivery

The `.pte` is large, so it is not bundled in the APK. The app downloads it when a parent
turns on the on-device mode, stores it in app data, and loads it lazily with an idle evict
(see docs/proposals/on-device-behavior.md). HP that cannot run it stay on the online mode.
