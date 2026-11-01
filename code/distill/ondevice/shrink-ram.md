# Shrink the on-device student to fit a 4 GB phone

Measured on a CPH2239 (3.8 GB RAM, ~1.5 GB free): the 3B .pte (2.0 GB) needs RSS ~3.7 GB and is
killed instantly by the Low Memory Killer; the 1B .pte (915 MB, `8da4w` weights, `8w` embedding,
full 943-token prompt) reaches RSS ~1.5 GB and survives at first but is still LMK-killed under
WhatsApp foreground. Goal: get RSS to ~1.0-1.1 GB so a 4 GB phone runs it comfortably.

These are three STACKING stages (0 -> 1 -> 2), not alternatives. Do the cheap one first and
measure; each one removes more RAM/latency and they combine.

RSS is dominated by: model weights, the 128k-vocab embedding table, and the KV cache (which
grows with the INPUT prompt length, not the output). So the big levers are a 4-bit embedding and
a SHORT input prompt. A short coded output helps latency a little, not RAM.

## Stage 0 - 4-bit embedding re-export (no GPU, no retrain, do first)

Re-export the existing merged 1B checkpoint, changing only the embedding from 8-bit to 4-bit.
The 128k x 2048 embedding drops from ~262 MB to ~131 MB of resident memory.

```bash
# in the optimum-executorch env (see export_executorch.md step 1)
MERGED=.../out/Llama-3.2-1B-dcai-stage1/merged
optimum-cli export executorch \
  --model "$MERGED" --task text-generation --recipe xnnpack \
  --use_custom_sdpa --use_custom_kv_cache \
  --qlinear 8da4w --qembedding 4w \
  --output_dir out_pte_emb4
```

Then host + measure (below). Expect roughly -130 to -200 MB RSS vs the 8w build. If that alone
brings RSS low enough on the target phone, you may stop here.

## Stage 1 - short prompt + coded output, re-distill (Brev GPU, the big win)

The full 943-token prompt is what makes the KV cache large and prompt-eval slow (~20 s/first
message). Re-distill the student on a COMPACT prompt and a COMPACT coded target, then export with
a small context. This cuts KV cache + activations + latency together.

1. Regenerate the base training set, then rewrite it to the short format:
   ```bash
   cd code/backpy && uv run python -m app.distill.build          # writes stage1-train.jsonl
   cd ../distill/ondevice && python build_short.py               # -> stage1-train-short.jsonl
   ```
   `build_short.py` is the source of truth for the SHORT_SYSTEM prompt and the label<->letter
   codebook. The code format is: sorted label letters then one signal digit; "N0" = ordinary.

2. Retrain the 1B on the short data (reuse train_1b.py; point it at the short file). On Brev GPU:
   ```bash
   # TRAIN path override: edit train_1b.py TRAIN to stage1-train-short.jsonl, or symlink it.
   python train_1b.py --base-model meta-llama/Llama-3.2-1B-Instruct --epochs 2 \
     --out out/Llama-3.2-1B-dcai-stage1-short --max-seq-len 320
   ```
   max-seq-len 320 is enough for the short prompt (~150 tokens) + one message + the short code,
   with headroom. Do NOT use 1024.

3. Export with the small context and 4-bit embedding:
   ```bash
   MERGED=out/Llama-3.2-1B-dcai-stage1-short/merged
   optimum-cli export executorch \
     --model "$MERGED" --task text-generation --recipe xnnpack \
     --use_custom_sdpa --use_custom_kv_cache \
     --qlinear 8da4w --qembedding 4w \
     --output_dir out_pte_short
   ```
   If the exporter takes a max sequence length flag, set it to 320 (match training); otherwise the
   runtime caps context at export metadata. Smaller context = smaller KV cache = less RAM.

4. (Optional, more accuracy at 4-bit) use SpinQuant instead of plain 8da4w PTQ; see
   examples/models/llama config `llama_xnnpack_spinquant.yaml`. SpinQuant needs a one-time
   rotation step but no full retrain.

## Accuracy check (every variant, before trusting it)

Adapt `eval_pte.py` to parse the coded output (letters+digit) instead of JSON, then:
```bash
python eval_pte.py --pte out_pte_short --tokenizer <merged> \
  --train stage1-train-short.jsonl --scenarios <scenarios> --split <split.json>
```
Report the measured recall/precision. The current full-prompt 1B is 0.53/0.55; a short prompt may
move this up or down - measure, do not guess. If it drops too far, lengthen the short prompt
slightly or keep 3B for high-RAM phones only.

## Measure RSS on the phone (how the numbers above were taken)

Host the new .pte (swap `/srv/dcai-model/stage1.pte`, tokenizer unchanged), re-download in the
app (Settings -> Analisis pesan -> remove, then download), then while sending one risky message:
```bash
PKG=dev.eziedutech.dcai.guardian
for i in $(seq 1 45); do
  adb shell 'p=$(pidof dev.eziedutech.dcai.guardian); [ -n "$p" ] && grep VmRSS /proc/$p/status || echo DEAD'
  sleep 1.5
done
```
Peak VmRSS is the number that matters; compare against `MemAvailable` in `/proc/meminfo`. Also
watch `adb logcat` for `lowmemorykiller ... guardian` and the "Protection turned off" event, which
mean it was killed.

## App changes required when the short model is ready (not done yet)

- `Stage1Prompt.kt`: replace the long SYSTEM with SHORT_SYSTEM (copied verbatim from
  build_short.py), and replace `parse()` to decode the code (letters -> labels via the same table,
  last digit -> signal = digit*10). `applyRules` and `hasFindings` stay.
- `OnDeviceModel.kt`: drop MAX_SEQ_LEN from 1024 to match the export (e.g. 320), and
  MAX_NEW_TOKENS to ~8 (the code is tiny).
- Stage 2 (server) is unchanged: on the on-device path the PHONE decodes the code and, only if
  flagged, sends the masked TEXT (not the code) to the server for stage 2. The server never sees
  the code.

## Stage 2 - process isolation (app, independent of the model work)

Run the model in a `:ondevice` process so that if a phone is still too small, the OOM kills only
that process and dcAI's UI + accessibility service survive and fall back to online. This makes
on-device safe to offer on borderline phones instead of crashing the whole app.
