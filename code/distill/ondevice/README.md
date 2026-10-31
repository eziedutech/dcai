# On-device stage 1 student (Llama 3.2 1B)

The phone option "Llama di ponsel" for message analysis (WS1 in
docs/proposals/on-device-behavior.md). This folder trains a small student that runs on the
phone via ExecuTorch, so ordinary messages are judged and dropped on the device and only
flagged, masked messages reach the server.

This is separate from `../train.py`, which fine-tunes the 8B server student on OpenPipe ART
(serverless) and yields an inference endpoint only. The on-device path needs a weights file,
so it uses HF transformers + PEFT and writes a merged checkpoint on disk.

## What runs where

- Training and export run on a GPU host (Brev / NVIDIA GPU VM). Not on the laptop. The
  Baseten hackathon grant is inference only (Muse Spark Open), so it is not used for training.
  Stop the Brev instance when idle; it bills per hour.
- The trained `.pte` is downloaded by the Android app when a parent chooses the on-device
  mode. The online mode (Muse Spark) stays the default, and a lightweight classifier is a
  planned third option.

## Prerequisites

- Accept the Llama 3.2 Community License on Hugging Face for
  `meta-llama/Llama-3.2-1B-Instruct`, then set `HF_TOKEN` in the environment. Never commit it.
- Llama license attribution: the output model name is prefixed "Llama", and the product must
  state "Built with Llama". Llama 3.2 1B is text only and has no EU restriction (that clause
  is for the multimodal models). dcAI is well under the 700M MAU threshold.

## Steps

1. Build the teacher-labelled training set (once), from the backend:

   ```bash
   cd code/backpy && uv run python -m app.distill.build
   ```

   This writes `data/distill/stage1-train.jsonl` (synthetic scenarios only).

2. Train the student (on the GPU host):

   ```bash
   pip install -r requirements.txt
   python train_1b.py --epochs 2
   ```

   Reuses the same data and class balancing as the 8B student, loss on the assistant turn
   only. Writes a merged checkpoint to `out/Llama-3.2-1B-dcai-stage1/merged`.

3. Measure the student before trusting it. Point the backend's stage 1 eval at an endpoint
   serving this checkpoint and run the same eval as the 8B student
   (`app.risk.stage1_eval`, `app.risk.pipeline_eval`). Report only eval numbers, never
   guessed accuracy.

4. Export to the phone: see `export_executorch.md`.

## Notes

- The stage 1 system prompt is long, so the training and runtime context cannot be tiny
  (default max_seq_len 1024). Shortening the on-device prompt to save context is a tuning
  step to try during export, measured against the same eval.
- No raw message text is used: the training data is synthetic (data/distill), the same
  source the 8B student uses.
