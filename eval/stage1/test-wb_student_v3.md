# Stage 1 on the test split: wb_student_v3

Model `wandb-artifact:///unismuh/dcai-distill/stage1-student-8b-v3-run:step1`. 18 synthetic scenarios, 197 messages. Gold labels are the scenario labels written with the dataset (draft, not yet reviewed by a human).

| Measure | Value |
| --- | --- |
| Model unavailable (after retries) | 0 of 197 |
| Labelled messages found (any label) | recall 0.84, precision 0.90 |
| Ordinary-chat messages given a label | 0 of 41 |
| Latency per message | p50 417 ms, p95 785 ms |
| Cost | USD 0.0411 |
| Wall time, concurrency 4 | 24 s |

| Label | Precision | Recall | Gold count |
| --- | --- | --- | --- |
| ajakan_berbahaya | 1.00 | 0.33 | 3 |
| berbagi_data_pribadi | 0.80 | 1.00 | 4 |
| kata_kasar | 1.00 | 0.33 | 3 |
| membangun_kedekatan | 1.00 | 1.00 | 4 |
| meminta_data_pribadi | 1.00 | 1.00 | 7 |
| meminta_kerahasiaan | 1.00 | 0.80 | 5 |
| menawarkan_hadiah | 0.75 | 1.00 | 3 |
| menekan_mengancam | 1.00 | 0.75 | 4 |
| menguji_batas | 1.00 | 1.00 | 1 |
| menyakiti_diri | 1.00 | 0.67 | 3 |
| perundungan | 0.50 | 0.44 | 9 |
| pindah_kanal | 1.00 | 1.00 | 3 |

Median signal on messages without gold labels: 0.0
