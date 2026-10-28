# Stage 1 distillation: Muse Spark teacher, Llama 3.1 8B student

Sections up to "Student v3" describe v1 and v2 on the earlier 34 dev and 16 test scenarios.

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

## Student v3: the invitation label

v2 was trained before `ajakan_berbahaya` existed. v3 repeats the v2 method on the dev split
as it is now (40 scenarios, 424 messages, including four `kenakalan` scenarios and the two
look-alike hard cases `kasus_sulit-010` and `kasus_sulit-011`): the teacher labels the dev
messages with the production prompt, the same balancing rule (labelled examples three
times, labels seen at most 6 times six times), two epochs.

**Disclosure.** The training data comes from the dev split only. The test split was used a
third time for the student, to decide whether v3 replaces v2 as the default. v2 and v3 are
compared below on the same 40 dev and 18 test scenarios.

| Teacher and training | Value |
| --- | --- |
| Teacher, labelled messages found | recall 0.84, precision 0.93 |
| Teacher, ordinary-chat messages given a label | 1 of 80 |
| Teacher cost | USD 0.6873 |
| Training examples | 424 unique, 670 after balancing |
| Rare labels (repeated six times) | `ajakan_berbahaya` 6, `kata_kasar` 1, `membangun_kedekatan` 6, `menguji_batas` 4, `pindah_kanal` 5 |
| Training | 670 gradient steps in 4 min 28 s, 6 min wall time; the service did not report a cost |

The teacher put `ajakan_berbahaya` on 6 of the 11 dev messages that carry it. `menyakiti_diri`
now appears 7 times and is no longer rare under the rule, so it is repeated three times.

### Stage 1

| Measure | v2 dev | **v3 dev** | v2 test | **v3 test** |
| --- | --- | --- | --- | --- |
| Labelled messages found | recall 0.82, precision 0.91 | **recall 0.81, precision 0.94** | recall 0.78, precision 0.95 | **recall 0.84, precision 0.90** |
| Ordinary-chat messages given a label | 2 of 80 | **1 of 80** | 0 of 41 | **0 of 41** |
| `ajakan_berbahaya` | precision 0.67, recall 0.55 (11) | **precision 1.00, recall 0.55 (11)** | precision 0.75, recall 1.00 (3) | **precision 1.00, recall 0.33 (3)** |
| `menyakiti_diri` recall | 0.60 (10) | **0.80 (10)** | 0.33 (3) | **0.67 (3)** |
| Cost | USD 0.0883 | **USD 0.0885** | USD 0.0411 | **USD 0.0411** |

v3 no longer puts the label on the anti-drug poster project. It still misses about half of
the invitations on dev, and on test it found 1 of 3; the rest of each `kenakalan`
conversation still brings it to `waspada`.

### Full pipeline

| Measure | v2 dev | **v3 dev** | v2 test | **v3 test** |
| --- | --- | --- | --- | --- |
| Risky approaches reaching `waspada` or higher | 8 of 8 | **7 of 8** | 4 of 4 | **4 of 4** |
| Ordinary and hard cases reaching `waspada` or higher | 1 of 16 | **0 of 16** | 1 of 7 | **1 of 7** |
| Detection delay, median | 0.0 | **0.0** | 1.0 | **0.0** |
| Final level exactly as expected | 33 of 40 | **33 of 40** | 14 of 18 | **11 of 18** |
| Self-harm flagged for a support response | 3 of 3 | **3 of 3** | 1 of 1 | **1 of 1** |
| Score never decreased | 40 of 40 | **40 of 40** | 18 of 18 | **18 of 18** |
| Cost of the run | USD 0.4876 | **USD 0.4869** | USD 0.2174 | **USD 0.2256** |

| Scenario | Split | Expected | v2 | **v3** |
| --- | --- | --- | --- | --- |
| kenakalan-001 | dev | waspada | waspada | **mendesak** |
| kenakalan-002 | dev | waspada | waspada | **mendesak** |
| kenakalan-003 | dev | mendesak | mendesak | **mendesak** |
| kenakalan-004 | dev | waspada | mendesak | **mendesak** |
| kasus_sulit-010 (silat) | dev | aman | aman | **aman** |
| kasus_sulit-011 (poster) | dev | aman | waspada | **aman** |
| kenakalan-005 | test | waspada | waspada | **mendesak** |
| kenakalan-006 | test | waspada | mendesak | **mendesak** |

On test, v3 matches v2 on every safety measure of the full pipeline. What got worse: on dev, `pendekatan_berisiko-004` ends at `perhatian`, because v3 left two of its
later messages unlabelled (the new teacher run left one of them unlabelled too), so stage 2
was not called again. On test, three scenarios that v2 got right end one level above the expected one, and
the run cost USD 0.008 more, all of it in stage 2 (stage 1 cost the same). On test v3 also
finds 1 of 3 invitation messages, against 3 of 3 for v2.

**Decision: v2 stays the default.** A risky approach ending at `perhatian` on dev, and fewer
invitations found on test, weigh more than the false alarm v3 removes.

## Rebuild

```bash
cd code/backpy && uv run python -m app.distill.build      # teacher labels (dev only)
cd code/distill && uv run python train.py                 # SFT on W&B, writes student.json
cd code/backpy && uv run python -m app.risk.stage1_eval wb_student --split test
SCREENING_ENDPOINTS=wb_student uv run python -m app.risk.pipeline_eval --split test --tag student-v3
```

Files: `teacher-dev.md` (v3), `teacher-dev-v2.md`, `student.json` (v3 checkpoint),
`student-v2.json`, `student-v1.json`, `../stage1/test-wb_*.md` (v1 and v2 named),
`../stage1/dev-wb_student.md` and `test-wb_student.md` (v2 on the 40 and 18 scenarios),
`../stage1/dev-wb_student_v3.md`, `test-wb_student_v3.md`, `../pipeline/test-student-v1.md`,
`../pipeline/test-student-v2.md`, `../pipeline/dev-kenakalan.md` and `test-kenakalan.md` (v2),
`../pipeline/dev-student-v3.md`, `test-student-v3.md`.
