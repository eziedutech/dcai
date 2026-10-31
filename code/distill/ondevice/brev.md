# Train the 1B student on Brev (NVIDIA)

Concrete recipe to produce the on-device student checkpoint on a Brev GPU VM, then export it
to a `.pte` for the phone. Llama 3.2 1B LoRA SFT is light (minutes on one mid GPU). Stop the
instance when done; Brev bills per hour.

## 0. Base model (easiest path)

- Use the ungated mirror `unsloth/Llama-3.2-1B-Instruct`: same Llama 3.2 1B Instruct weights,
  safetensors BF16, no access gate, no HF token needed. Pass it with `--base-model`.
- The official `meta-llama/Llama-3.2-1B-Instruct` is gated (approval can be pending); if you
  prefer it, accept the license on your HF account and set `HF_TOKEN` on the instance only.
- Either way the Llama 3.2 Community License applies: the product states "Built with Llama".

## 1. Provision the instance

- Brev GPU VM, Ubuntu, Python 3.12, x86_64.
- GPU: 16 GB VRAM is enough for 1B LoRA. A T4 (16 GB) works; the script auto-uses fp16 on it
  because T4 has no bf16. An L4/A10 (24 GB, bf16 native) is a bit nicer but not needed.
- System RAM and CPU matter here: pick at least ~16 GB RAM and 2+ vCPUs. A tiny 1 vCPU /
  3.75 GB RAM tier risks running out of memory when loading or merging the model, and is slow
  to pip install and tokenise.
- Disk: ~100 GB is enough for 1B (base ~2.5 GB plus checkpoints); more is fine.

## 2. Get the code and data onto the instance

The training data (`data/distill/stage1-train.jsonl`) is not in git, so a plain clone will
not include it. Two options:

- Copy the minimal subset, keeping the repo layout so paths resolve
  (`train_1b.py` expects `data/distill/` three levels up from itself):

  ```bash
  # from your laptop
  scp -r code/distill/ondevice   <brev>:~/dcai/code/distill/ondevice
  scp -r data/distill            <brev>:~/dcai/data/distill
  ```

- Or regenerate the data on the instance from the backend (needs the Baseten Muse key in the
  environment, and the backend installed): `cd code/backpy && uv run python -m app.distill.build`.

## 3. Set the token and install

```bash
cd ~/dcai/code/distill/ondevice
# HF_TOKEN only needed for the gated official repo; the unsloth mirror needs none.
pip install -r requirements.txt
```

## 4. Train

```bash
python train_1b.py --base-model unsloth/Llama-3.2-1B-Instruct --epochs 2
```

Writes the merged checkpoint to `out/Llama-3.2-1B-dcai-stage1/merged`. This reuses the same
synthetic training data and class balancing as the 8B student.

## 5. Measure before trusting it

Serve the checkpoint and run the same stage 1 and pipeline eval the 8B student uses
(`app.risk.stage1_eval`, `app.risk.pipeline_eval`). Report only eval numbers.

## 6. Export to .pte

Follow `export_executorch.md` on the same instance: install ExecuTorch, convert the merged HF
checkpoint, export to a 4-bit `.pte` (about 1.1 GB for 1B).

## 7. Download and stop

```bash
scp -r <brev>:~/dcai/code/distill/ondevice/out/Llama-3.2-1B-dcai-stage1 ./artifacts
```

Then STOP the Brev instance so it stops billing.
