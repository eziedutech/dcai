# Stage 1 distillation: Muse Spark teacher, Llama 3.1 8B student

Teacher: Muse Spark labels each message of the 34 dev scenarios (366 messages). Student:
`meta-llama/Llama-3.1-8B-Instruct`, LoRA SFT on W&B Serverless Training (OpenPipe ART),
trained on exactly the production stage 1 input. Measured on the 16 test scenarios
(177 messages), which the prompt and the training data never saw.

**Disclosure.** The test split was used twice for the student: v1 showed that it never
labelled self-harm, and v2 fixes that by rebalancing the classes. The fix was chosen from
the training data's own label counts, not from test results, but the v2 test numbers are
no longer from an untouched split.

## Teacher on the dev split

| Measure | Value |
| --- | --- |
| Labelled messages found | recall 0.86, precision 0.94 |
| Ordinary-chat messages given a label | 1 of 80 |
| Training examples | 365 (1 teacher answer cut by its token budget) |
| Cost | USD 0.58 |

## Stage 1 on the test split

| Model | Recall | Precision | Ordinary messages labelled | Self-harm messages caught | Cost |
| --- | --- | --- | --- | --- | --- |
| Llama 3.3 70B (previous default) | 0.84 | 0.72 | 0 of 41 | 3 of 3 | USD 0.106 |
| Llama 3.1 8B, base | 0.89 | 0.52 | 5 of 41 | 2 of 3 | USD 0.033 |
| Student v1 (as is) | 0.73 | 0.84 | 0 of 41 | 0 of 3 | USD 0.033 |
| **Student v2 (balanced)** | **0.81** | **0.91** | **0 of 41** | **2 of 3** | **USD 0.033** |

v1 trained on the data as is: 79% of messages carry no label and self-harm appears 6
times, so it learned that "no label" is almost always right. v2 repeats labelled examples
three times and those with rare labels six times (50% labelled after balancing), with two
epochs instead of three.

## Full pipeline on the test split

Stage 1, the rule floor and stage 2 (Muse Spark), message by message.

| Measure | 70B screening | Student v1 | **Student v2** |
| --- | --- | --- | --- |
| Risky approaches reaching `waspada` or higher | 4 of 4 | 4 of 4 | **4 of 4** |
| Ordinary and hard cases reaching `waspada` or higher | 1 of 7 | 0 of 7 | **1 of 7** |
| Detection delay, median | 2 | 1 | **0** |
| Final level exactly as expected | 12 of 16 | 13 of 16 | **12 of 16** |
| Self-harm flagged for a support response | 1 of 1 | 0 of 1 | **1 of 1** |
| Score never decreased | 16 of 16 | 16 of 16 | **16 of 16** |
| Cost of the run | USD 0.32 | USD 0.18 | **USD 0.17** |

With v2 the pipeline matches 70B screening on every safety measure, catches approaches
earlier, and costs 46% less. Trained checkpoints are billed at W&B Serverless Inference
rates (USD 0.22 per million tokens for Llama 3.1 8B against 0.71 for 3.3 70B).

## Rebuild

```bash
cd code/backpy && uv run python -m app.distill.build      # teacher labels (dev only)
cd code/distill && uv run python train.py                 # SFT on W&B, writes student.json
cd code/backpy && uv run python -m app.risk.stage1_eval wb_student --split test
SCREENING_ENDPOINTS=wb_student uv run python -m app.risk.pipeline_eval --split test --tag student-v2
```

Files: `teacher-dev.md`, `student.json` (v2 checkpoint), `student-v1.json`,
`../stage1/test-wb_*.md` (v1 and v2 named), `../pipeline/test-student-v1.md`, `../pipeline/test-student-v2.md`.
