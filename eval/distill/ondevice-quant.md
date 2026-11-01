# On-device stage 1 (Llama .pte): prompt format and quantization sweep

All numbers are measured with `code/distill/ondevice/eval_pte.py` on the locked test split
(18 scenarios, 197 messages, 45 of them carrying a gold label = "risky"). Nothing here is
guessed. Two metrics:

- label recall / precision: per-label, the part the on-device model is responsible for.
- flagged recall / precision: the message-level send decision (a message is sent to the
  server when it has any label OR signal >= 20, the `ONDEVICE_SEND_SIGNAL` policy in
  `MessageIngest.kt`). "missed" = risky messages the phone would judge ordinary and never send.

Runtime: Brev L40, CPU inference via optimum-executorch 1.1.0 / executorch 1.5.1. Students are
LoRA SFT of the ungated `unsloth/Llama-3.2-{1B,3B}-Instruct` base on the same teacher labels,
2 epochs. Exports use xnnpack + custom sdpa + custom kv cache; `.pte` built with
`--qlinear <linear> --qembedding <emb> --max_seq_len <ctx>`.

## The sweep (same checkpoint, same test split)

| Model | Prompt | Quant (linear + emb) | ctx | .pte | Label R / P | Flagged R / P | Missed | Wajar false alarms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1B | short + coded | 8da4w + 4w | 512 | 0.79 GB | 0.33 / 0.38 | 0.60 / 0.71 | 18 | 4 |
| **1B** | **full** | **8da4w + 4w** | **1024** | **0.83 GB** | **0.55 / 0.60** | **0.69 / 0.79** | **14** | **1** |
| 1B | full | 8da4w + 8w | 1024 | 0.96 GB | 0.53 / 0.55 | 0.71 / 0.76 | 13 | 2 |
| 1B | full | 8da8w + 8w | 1024 | 1.50 GB | 0.45 / 0.52 | 0.64 / 0.74 | 16 | 2 |
| 3B | short + coded | 8da4w + 4w | 512 | 2.00 GB | 0.51 / 0.58 | 0.76 / 0.81 | 11 | 0 |
| 3B | full | 8da4w + 8w | 1024 | 2.05 GB | 0.59 / 0.83 | (not measured) | - | 0 |
| online 8B student (server default) | full | - | - | server | 0.81 / 0.95 | - | - | 0 |

(The 3B full-prompt row is the earlier measurement from docs/log/2026-11-01.md, label-level
only; the online 8B row is eval/distill/report.md student v2 on the test split.)

## What the numbers say

1. The prompt format, not the quantization, drove the accuracy loss. Compare rows 1 and 2:
   identical quant (8da4w + 4w) and nearly identical size (~0.8 GB), differing only in short
   coded prompt vs full prompt. Label recall goes 0.33 -> 0.55 and missed risky 18 -> 14. The
   shrink-to-coded format (built to cut KV cache and latency for a 4 GB phone) cost about 0.22
   label recall.
2. More quantization bits did not help. 8da4w + 8w (0.96 GB) and 8da8w + 8w (1.50 GB) are no
   better than 8da4w + 4w (0.83 GB); 8da8w is lower, which on a 45-risky-message split is within
   noise. So the smallest quant is tied-best and lightest, with the fewest false alarms.
3. 3B buys little over the full-prompt 1B at the send gate (flagged 0.76 vs 0.69) for 2.4x the
   size, and its on-device RAM is unverified (a ~2 GB .pte needs ~2.5 to 2.9 GB RSS; the full 3B
   needed ~3.7 GB and was killed instantly on a 3.8 GB phone).
4. On-device tops out well below the online 8B student (0.81 / 0.95). On-device stays the privacy
   option (ordinary messages never leave the phone), not the accuracy option; online is default.

## Best on-device point

Full-prompt 1B at 8da4w + 4w embedding: 0.55 label / 0.69 flagged, 1 false alarm, 0.83 GB, the
same size and roughly the same weight-RAM as the deployed short-coded 1B. The cost of the full
prompt is latency (about 20 s to first token on a phone CPU, against about 0.5 s for the short
prompt) and a larger KV cache at ctx 1024 (vs 512). That latency and KV cost are exactly why the
short format was built; the trade is accuracy vs responsiveness and KV RAM, and it needs an
on-device check before shipping.

## SpinQuant note (not applied)

torchao 0.18 ships `torchao.prototype.spinquant.apply_spinquant`, but it targets torchao's own
Llama module layout (`tok_embeddings`, `wq/wk/wv`) and raises `AttributeError` on a Hugging Face
`LlamaForCausalLM` (`model.embed_tokens`, `self_attn.q_proj`). Real SpinQuant would need the
checkpoint converted to the Meta consolidated format and the ExecuTorch Llama
`export_llama --use_spin_quant` pipeline (R1/R2 offline plus the R4 online Hadamard op in the
runtime), a separate larger effort. Given that prompt format, not quantization, dominated the
accuracy here, SpinQuant is unlikely to change the picture much; it is parked, not done.

## Reproduce

On a GPU box (training) + the optimum-executorch env (export/eval):

```bash
# train (venv with transformers<5 + trl + peft), full-prompt JSON target:
python train_1b.py --base-model unsloth/Llama-3.2-1B-Instruct --train stage1-train.jsonl \
  --max-seq-len 1024 --out out/Llama-3.2-1B-dcai-stage1-full --epochs 2
# export (optimum-executorch env):
optimum-cli export executorch --model out/Llama-3.2-1B-dcai-stage1-full/merged \
  --task text-generation --recipe xnnpack --use_custom_sdpa --use_custom_kv_cache \
  --qlinear 8da4w --qembedding 4w --max_seq_len 1024 --output_dir out_f_8da4w_4w
# eval:
python eval_pte.py --pte out_f_8da4w_4w --tokenizer out/Llama-3.2-1B-dcai-stage1-full/merged \
  --train stage1-train.jsonl --scenarios scenarios --split scenarios/split.json \
  --format json --max-seq-len 1024
```
