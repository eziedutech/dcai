# Train the 1B student on Brev (NVIDIA)

Concrete recipe to produce the on-device student checkpoint on a Brev GPU VM, then export it
to a `.pte` for the phone. Llama 3.2 1B LoRA SFT is light (minutes on one mid GPU). Stop the
instance when done; Brev bills per hour.

## 0. One-time prerequisites (on your accounts)

- Accept the Llama 3.2 Community License for `meta-llama/Llama-3.2-1B-Instruct` on Hugging
  Face, and create an HF access token.
- Keep the token out of git and out of chat. Put it in the environment on the instance only.

## 1. Provision the instance

- Brev GPU VM, Ubuntu, Python 3.12.
- GPU: an L4 or A10 (24 GB) is plenty for 1B LoRA in bf16. An A100 is faster but costs more;
  not needed for 1B. Disk: ~100 GB (base weights ~2.5 GB plus checkpoints).

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
export HF_TOKEN=...        # from your HF account, never commit or paste in chat
pip install -r requirements.txt
```

## 4. Train

```bash
python train_1b.py --epochs 2
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
